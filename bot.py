import os
import logging
import asyncio
from telegram import Update, InputFile
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from telegram.constants import ChatAction
from telegram.error import TelegramError
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.stats import norm
from io import BytesIO

# استيراد الوحدات المحلية
from config import BOT_TOKEN, ADMIN_CHANNEL_ID, UNIVERSITY_NAME, COLLEGE_NAME
from database import init_db, register_student, get_student_info, get_all_students
from pdf_parser import parse_pdf_marks
from data_processor import process_marks, generate_normal_distribution_plot

# تهيئة الخطوط لـ matplotlib لدعم اللغة العربية والأحرف الخاصة
# هذا يحل مشكلة: Character "╒" at index 0 in text is outside the range...
plt.rcParams['font.family'] = 'DejaVu Sans'
plt.rcParams['font.sans-serif'] = ['DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

# تهيئة التسجيل
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)

# حالة التسجيل
REGISTRATION_STATE = {}

# الأوامر
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """يرسل رسالة ترحيب ويبدأ عملية التسجيل."""
    await update.message.reply_text(
        f'مرحباً بك في نظام توزيع علامات {UNIVERSITY_NAME} - {COLLEGE_NAME}.\n'
        'الرجاء إرسال رقمك الجامعي (5 أرقام) للتسجيل.'
    )
    REGISTRATION_STATE[update.effective_user.id] = 'WAITING_FOR_ID'

async def handle_registration(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """يتعامل مع عملية التسجيل."""
    user_id = update.effective_user.id
    text = update.message.text

    if user_id not in REGISTRATION_STATE:
        await update.message.reply_text('الرجاء استخدام الأمر /start لبدء التسجيل.')
        return

    state = REGISTRATION_STATE[user_id]

    if state == 'WAITING_FOR_ID':
        if text and len(text) == 5 and text.isdigit():
            student_id = text
            register_student(user_id, student_id, UNIVERSITY_NAME, COLLEGE_NAME)
            del REGISTRATION_STATE[user_id]
            await update.message.reply_text(
                f'تم تسجيلك بنجاح برقم جامعي: {student_id}.\n'
                'ستصلك نتيجتك تلقائياً عند نشرها.'
            )
        else:
            await update.message.reply_text('الرجاء إدخال رقم جامعي صحيح مكون من 5 أرقام فقط.')

# معالجة ملفات PDF
async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """يتعامل مع ملفات PDF المرسلة إلى البوت أو التي يتم إعادة توجيهها."""
    document = update.message.document
    chat_id = update.effective_chat.id

    if document.mime_type != 'application/pdf':
        await update.message.reply_text('الرجاء إرسال ملف PDF فقط.')
        return

    # إرسال حالة "جاري الكتابة"
    await context.bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)
    
    # تهيئة المتغيرات قبل كتلة try لمنع UnboundLocalError
    # هذا يحل مشكلة: UnboundLocalError: cannot access local variable 'image_path'
    image_path = None
    pdf_report_path = None
    
    try:
        # 1. تنزيل الملف
        file_id = document.file_id
        new_file = await context.bot.get_file(file_id)
        
        # إنشاء مسار مؤقت للملف
        pdf_path = f'/tmp/{file_id}.pdf'
        await new_file.download_to_drive(pdf_path)
        
        await update.message.reply_text('تم استلام الملف. جاري تحليل العلامات...')
        await context.bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)

        # 2. تحليل العلامات
        marks_df = parse_pdf_marks(pdf_path)
        
        if marks_df.empty:
            await update.message.reply_text('لم يتم العثور على أي بيانات علامات صالحة في ملف PDF.')
            return

        # 3. معالجة البيانات وتوليد الإحصائيات
        all_students = get_all_students()
        
        if all_students:
            # دمج بيانات التسجيل مع العلامات
            registered_students_df = pd.DataFrame(all_students, columns=['user_id', 'student_id', 'university', 'college'])
            registered_students_df['student_id'] = registered_students_df['student_id'].astype(str)
            
            merged_df = pd.merge(marks_df, registered_students_df, on='student_id', how='inner')
            
            if merged_df.empty:
                await update.message.reply_text('تم تحليل الملف بنجاح، ولكن لم يتم العثور على علامات لأي طالب مسجل.')
                return

            # 4. توزيع النتائج الفردية
            for index, row in merged_df.iterrows():
                student_user_id = row['user_id']
                student_mark = row['mark']
                student_id = row['student_id']
                
                # توليد الرسم البياني
                image_path = f'/tmp/plot_{student_id}.png'
                generate_normal_distribution_plot(marks_df['mark'], student_mark, image_path)
                
                # إرسال النتيجة للطالب
                try:
                    await context.bot.send_photo(
                        chat_id=student_user_id,
                        photo=image_path,
                        caption=f'نتيجتك في المادة:\n'
                                f'الرقم الجامعي: {student_id}\n'
                                f'العلامة: {student_mark}\n'
                                f'موقعك على التوزيع الطبيعي يظهر في الصورة المرفقة.'
                    )
                except TelegramError as e:
                    logger.error(f"فشل إرسال النتيجة للطالب {student_user_id}: {e}")
                
                # تنظيف ملف الصورة بعد الإرسال
                if os.path.exists(image_path):
                    os.remove(image_path)
                    image_path = None # إعادة التعيين لمنع الحذف المزدوج في finally

            # 5. إرسال الإحصائيات المجمعة إلى قناة الإدارة
            if ADMIN_CHANNEL_ID:
                stats = process_marks(marks_df)
                
                stats_message = (
                    f'**إحصائيات العلامات المجمعة:**\n'
                    f'المتوسط الحسابي: {stats["mean"]:.2f}\n'
                    f'الانحراف المعياري: {stats["std_dev"]:.2f}\n'
                    f'الحد الأدنى: {stats["min"]}\n'
                    f'الحد الأقصى: {stats["max"]}\n'
                    f'عدد الطلاب: {stats["count"]}'
                )
                await context.bot.send_message(chat_id=ADMIN_CHANNEL_ID, text=stats_message)
                
                await update.message.reply_text('تم توزيع النتائج الفردية وإرسال الإحصائيات المجمعة إلى قناة الإدارة.')
            else:
                await update.message.reply_text('تم توزيع النتائج الفردية بنجاح. لم يتم إرسال إحصائيات مجمعة لعدم تحديد قناة الإدارة.')
        else:
            await update.message.reply_text('لا يوجد طلاب مسجلون في قاعدة البيانات لتوزيع العلامات عليهم.')

    except Exception as e:
        logger.error(f"خطأ غير متوقع: {e}")
        await update.message.reply_text(f'حدث خطأ أثناء معالجة الملف: {e}')
        
    finally:
        # 6. تنظيف الملفات المؤقتة
        if 'pdf_path' in locals() and os.path.exists(pdf_path):
            os.remove(pdf_path)
        
        # استخدام المتغيرات المهيأة (image_path و pdf_report_path)
        if image_path and os.path.exists(image_path):
            os.remove(image_path)
        if pdf_report_path and os.path.exists(pdf_report_path):
            os.remove(pdf_report_path)


def main() -> None:
    """يبدأ البوت."""
    # تهيئة قاعدة البيانات
    init_db()
    
    # إنشاء التطبيق وتمرير التوكن
    application = Application.builder().token(BOT_TOKEN).build()

    # إضافة المعالجات
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_registration))
    application.add_handler(MessageHandler(filters.Document.ALL, handle_document))

    # بدء البوت
    logger.info("بدء تشغيل البوت...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()

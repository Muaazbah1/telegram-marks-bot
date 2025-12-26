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
# تم تعديل أسماء المتغيرات لتتوافق مع config.py
from config import TELEGRAM_BOT_TOKEN, STATISTICS_OUTPUT_CHANNEL_ID, UNIVERSITIES
from database import init_db, register_student, get_student_info, get_all_students
from pdf_parser import parse_pdf_marks
from data_processor import process_marks, generate_normal_distribution_plot, generate_text_report, generate_full_report_pdf

# استخراج أسماء الجامعة والكلية من القاموس (افتراضياً أول إدخال)
UNIVERSITY_NAME = list(UNIVERSITIES.keys())[0]
COLLEGE_NAME = list(UNIVERSITIES[UNIVERSITY_NAME].keys())[0]

# تهيئة الخطوط لـ matplotlib لدعم اللغة العربية والأحرف الخاصة
# تم إبقاؤه هنا للتأكد من تهيئة matplotlib قبل أي استخدام
plt.rcParams['font.family'] = 'sans-serif'
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
# إزالة حالة التسجيل من الذاكرة
# REGISTRATION_STATE = {}

# الأوامر
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """يرسل رسالة ترحيب ويبدأ عملية التسجيل."""
    # مسح أي حالة سابقة قبل البدء
    clear_registration_state(update.effective_user.id)
    
    await update.message.reply_text(
        f'مرحباً بك في نظام توزيع علامات {UNIVERSITY_NAME} - {COLLEGE_NAME}.\n'
        'الرجاء إرسال رقمك الجامعي (5 أرقام) للتسجيل.'
    )
    set_registration_state(update.effective_user.id, 'WAITING_FOR_ID')

async def handle_registration(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """يتعامل مع عملية التسجيل."""
    user_id = update.effective_user.id
    text = update.message.text

    # الحصول على الحالة من قاعدة البيانات
    state_data = get_registration_state(user_id)

    if not state_data:
        # إذا لم يكن في حالة التسجيل، اطلب منه البدء
        await update.message.reply_text('الرجاء استخدام الأمر /start لبدء التسجيل.')
        return

    state = state_data['state']
    student_id_temp = state_data['student_id']

    # 2. معالجة حالة انتظار الرقم الجامعي
    if state == 'WAITING_FOR_ID':
        if text and len(text) == 5 and text.isdigit():
            # الانتقال إلى حالة انتظار الاسم
            set_registration_state(user_id, 'WAITING_FOR_NAME', student_id=text)
            await update.message.reply_text('الآن، الرجاء إرسال اسمك الكامل.')
        else:
            await update.message.reply_text('الرجاء إدخال رقم جامعي صحيح مكون من 5 أرقام فقط.')
            
    # 3. معالجة حالة انتظار الاسم
    elif state == 'WAITING_FOR_NAME':
        student_id = student_id_temp
        student_name = text
        
        # التأكد من أننا نستخدم الدالة الجديدة التي تحفظ الاسم
        register_student(user_id, student_id, student_name, UNIVERSITY_NAME, COLLEGE_NAME)
        
        # بعد التسجيل الناجح، قم بمسح الحالة من قاعدة البيانات
        clear_registration_state(user_id)
        
        await update.message.reply_text(
            f'تم تسجيلك بنجاح:\n'
            f'الاسم: {student_name}\n'
            f'الرقم الجامعي: {student_id}\n'
            'ستصلك نتيجتك تلقائياً عند نشرها.'
        )


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
    
    # **رسالة تحذيرية جديدة**
    await update.message.reply_text('تم استلام الملف. **يرجى الانتظار، قد تستغرق عملية تحليل الملف عدة دقائق** بسبب حجم الملف وقيود الخادم.')
    
    # تهيئة المتغيرات قبل كتلة try لمنع UnboundLocalError
    pdf_path = None
    
    # قائمة لتتبع جميع الملفات المؤقتة التي يجب حذفها
    temp_files_to_clean = []
    
    try:
        # 1. تنزيل الملف
        file_id = document.file_id
        new_file = await context.bot.get_file(file_id)
        
        # إنشاء مسار مؤقت للملف
        pdf_path = f'/tmp/{file_id}.pdf'
        temp_files_to_clean.append(pdf_path)
        await new_file.download_to_drive(pdf_path)
        
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
            # تم تعديل هذا الجزء ليتضمن student_name
            registered_students_df = pd.DataFrame(all_students, columns=['user_id', 'student_id', 'student_name', 'university', 'college'])
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
                
                # توليد الرسم البياني الفردي
                image_path = f'/tmp/plot_{student_id}.png'
                temp_files_to_clean.append(image_path) # إضافة مسار الصورة للتنظيف
                
                generate_normal_distribution_plot(marks_df['mark'], student_mark, image_path)
                
                # إرسال النتيجة للطالب (باللغة الإنجليزية لتجنب مشكلة التقطيع في الصورة)
                try:
                    await context.bot.send_photo(
                        chat_id=student_user_id,
                        photo=image_path,
                        caption=f'Your result in the subject:\n'
                                f'Student ID: {student_id}\n'
                                f'Mark: {student_mark}\n'
                                f'Your position on the marks distribution is shown in the attached image.'
                    )
                except TelegramError as e:
                    logger.error(f"Failed to send result to student {student_user_id}: {e}")
                
                # **التنظيف الفوري للملفات المؤقتة بعد إرسالها**
                if os.path.exists(image_path):
                    os.remove(image_path)
                    temp_files_to_clean.remove(image_path) # إزالته من قائمة التنظيف النهائية

            # 5. إرسال الإحصائيات المجمعة وتقرير PDF إلى قناة الإدارة
            if STATISTICS_OUTPUT_CHANNEL_ID:
                stats = process_marks(marks_df)
                
                # توليد الرسم البياني العام
                general_plot_path = f'/tmp/general_plot.png'
                temp_files_to_clean.append(general_plot_path)
                generate_normal_distribution_plot(marks_df['mark'], -1, general_plot_path) 
                
                # دمج الاسم مع العلامات لتقرير PDF
                report_df = pd.merge(marks_df, registered_students_df[['student_id', 'student_name']], on='student_id', how='left')
                report_df['student_name'] = report_df['student_name'].fillna('غير مسجل')
                
                # توليد تقرير PDF الشامل
                pdf_report_path = f'/tmp/report_{document.file_id}.pdf'
                temp_files_to_clean.append(pdf_report_path)
                generate_full_report_pdf(report_df, stats, general_plot_path, pdf_report_path)
                
                # إرسال تقرير PDF
                with open(pdf_report_path, 'rb') as f:
                    await context.bot.send_document(
                        chat_id=STATISTICS_OUTPUT_CHANNEL_ID, 
                        document=f,
                        caption="Comprehensive Marks Report (PDF)"
                    )
                
                await update.message.reply_text('تم توزيع النتائج الفردية وإرسال التقرير الشامل إلى قناة الإدارة.')
                
            else:
                await update.message.reply_text('تم توزيع النتائج الفردية بنجاح. لم يتم إرسال تقرير مجمع لعدم تحديد قناة الإدارة.')
        else:
            await update.message.reply_text('لا يوجد طلاب مسجلون في قاعدة البيانات لتوزيع العلامات عليهم.')

    except Exception as e:
        logger.error(f"خطأ غير متوقع: {e}")
        await update.message.reply_text(f'حدث خطأ أثناء معالجة الملف: {e}')
        
    finally:
        # 6. التنظيف النهائي لجميع الملفات المؤقتة المتبقية
        for file_path in temp_files_to_clean:
            if os.path.exists(file_path):
                os.remove(file_path)
                logger.info(f"تم تنظيف الملف المؤقت: {file_path}")


def main() -> None:
    """يبدأ البوت."""
    # تهيئة قاعدة البيانات
    init_db()
    
    # إنشاء التطبيق وتمرير التوكن
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # إضافة المعالجات
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_registration))
    application.add_handler(MessageHandler(filters.Document.ALL, handle_document))

    # بدء البوت
    logger.info("بدء تشغيل البوت...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()

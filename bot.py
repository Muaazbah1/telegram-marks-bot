import logging
import os
import io
from telegram import Update, Bot
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# استيراد الدوال من الملفات الأخرى
from config import TELEGRAM_BOT_TOKEN, STATISTICS_OUTPUT_CHANNEL_ID, UNIVERSITIES
from database import init_db, register_student, get_student_info_by_user_id, get_student_info_by_id, get_all_students, update_student_name
from pdf_parser import parse_grades_pdf # تم تصحيح اسم الدالة
from data_processor import process_grades, create_normal_distribution_plot, create_admin_report_pdf # تم تصحيح أسماء الدوال

# إعداد التسجيل (Logging)
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# إعدادات الجامعة (للتسهيل، نفترض جامعة واحدة حالياً)
UNIVERSITY_NAME = "جامعة حلب"
COLLEGE_NAME = "كلية الطب"

# --- الأوامر ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """يرسل رسالة ترحيب ويبدأ عملية التسجيل (خطوة واحدة: الرقم الجامعي)."""
    user_id = update.effective_user.id
    
    # التحقق مما إذا كان الطالب مسجلاً بالفعل
    student_info = get_student_info_by_user_id(user_id)
    if student_info:
        student_id, student_name, _, _ = student_info
        status_message = f'أنت مسجل بالفعل.\n'
        status_message += f'الرقم الجامعي: {student_id}\n'
        if student_name:
            status_message += f'الاسم: {student_name}\n'
        else:
            status_message += 'لم يتم استخراج اسمك بعد من ملف العلامات.'
        await update.message.reply_text(status_message)
        return

    await update.message.reply_text(
        f'مرحباً بك في نظام توزيع علامات {UNIVERSITY_NAME} - {COLLEGE_NAME}.\n'
        'الرجاء إرسال رقمك الجامعي (5 أرقام) للتسجيل.'
    )

async def handle_registration(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """يتعامل مع عملية التسجيل (خطوة واحدة: الرقم الجامعي)."""
    user_id = update.effective_user.id
    text = update.message.text

    # التحقق مما إذا كان الطالب مسجلاً بالفعل
    if get_student_info_by_user_id(user_id):
        # إذا كان مسجلاً، تجاهل الرسالة أو أرسل رسالة تذكير
        await update.message.reply_text('أنت مسجل بالفعل. استخدم /start للتحقق من بياناتك.')
        return

    # معالجة الرقم الجامعي
    if text and len(text) == 5 and text.isdigit():
        student_id = text
        
        # التسجيل في قاعدة البيانات (الاسم سيكون فارغاً مبدئياً)
        register_student(user_id, student_id, UNIVERSITY_NAME, COLLEGE_NAME)
        
        await update.message.reply_text(
            f'تم تسجيل رقمك الجامعي ({student_id}) بنجاح.\n'
            'سيتم استخراج اسمك تلقائياً من ملف العلامات عند نشره.\n'
            'ستصلك نتيجتك الفردية تلقائياً بعد معالجة الملف.'
        )
    else:
        await update.message.reply_text('الرجاء إدخال رقم جامعي صحيح مكون من 5 أرقام فقط.')

async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """يتعامل مع ملفات PDF المرسلة إلى البوت (المعاد توجيهها من القناة)."""
    
    # 1. التحقق من أن الملف هو PDF
    if not update.message.document or update.message.document.mime_type != "application/pdf":
        # لا ترد على رسائل غير PDF لتجنب إزعاج المستخدمين في القناة
        return

    file_id = update.message.document.file_id
    file = await context.bot.get_file(file_id)
    
    # 2. تنزيل الملف
    pdf_path = f"/tmp/{file_id}.pdf"
    await file.download_to_drive(pdf_path)
    
    # رسالة إشعار بالبدء (يمكن إرسالها إلى قناة المشرف أو تسجيلها)
    logger.info(f"تم استلام ملف العلامات. جاري المعالجة...")

    # 3. تحليل ملف PDF
    try:
        grades_data = parse_grades_pdf(pdf_path) # تم تصحيح اسم الدالة
        
        # 4. التحقق من البيانات المستخرجة (تم تصحيح طريقة التحقق)
        if not grades_data:
            logger.warning("فشل تحليل ملف PDF أو لا يحتوي على بيانات علامات.")
            # يمكن إرسال رسالة خطأ للمشرف هنا
            os.remove(pdf_path)
            return

        # 5. معالجة البيانات
        student_results, admin_pdf_buffer = process_grades(grades_data, course_name="علامات المادة")
        
        # 6. إرسال النتائج الفردية (تم تصحيح المنطق لاستخدام student_results)
        if student_results:
            for user_id, result in student_results.items():
                # استخراج بيانات الطالب من قاعدة البيانات للحصول على الرقم الجامعي والاسم
                student_info = get_student_info_by_user_id(user_id)
                if not student_info:
                    logger.warning(f"الطالب ذو user_id {user_id} مسجل ولكن لا توجد معلومات في قاعدة البيانات.")
                    continue
                
                student_id, student_name, _, _ = student_info
                
                # إنشاء مخطط التوزيع
                plot_buffer = create_normal_distribution_plot(
                    result['all_grades'], 
                    result['grade'], 
                    result['mean'], 
                    result['std_dev']
                )
                
                # إرسال الرسالة
                message_text = (
                    f"نتيجتك في المادة:\n"
                    f"الرقم الجامعي: {student_id}\n"
                    f"الاسم: {student_name if student_name else 'غير متوفر'}\n"
                    f"الدرجة: {result['grade']:.2f}\n"
                    f"النسبة المئوية (Percentile): {result['percentile']:.2f}%\n"
                    f"هذا يعني أنك أفضل من {result['percentile']:.2f}% من زملائك."
                )
                
                # إرسال الصورة والرسالة
                await context.bot.send_photo(
                    chat_id=user_id,
                    photo=plot_buffer,
                    caption=message_text
                )
                
                logger.info(f"تم إرسال النتيجة للطالب {student_id} ({user_id}).")
        
        # 7. إرسال تقرير المشرف
        if admin_pdf_buffer:
            await context.bot.send_document(
                chat_id=STATISTICS_OUTPUT_CHANNEL_ID,
                document=admin_pdf_buffer,
                filename="تقرير_إحصائيات_العلامات.pdf",
                caption="تقرير إحصائيات العلامات الشامل."
            )
            logger.info("تم إرسال تقرير المشرف بنجاح.")

    except Exception as e:
        logger.error(f"خطأ أثناء معالجة الملف: {e}")
        # إرسال رسالة خطأ للمشرف
        await context.bot.send_message(
            chat_id=STATISTICS_OUTPUT_CHANNEL_ID,
            text=f"❌ خطأ فادح أثناء معالجة ملف العلامات:\n{e}"
        )
    finally:
        # 8. تنظيف الملف المؤقت
        if os.path.exists(pdf_path):
            os.remove(pdf_path)

# --- الوظيفة الرئيسية ---

def main() -> None:
    """تبدأ تشغيل البوت."""
    # تهيئة قاعدة البيانات
    init_db()
    
    # إنشاء التطبيق
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # إضافة معالجات الأوامر
    application.add_handler(CommandHandler("start", start))
    
    # معالج الرسائل النصية (للتسجيل)
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_registration))
    
    # معالج المستندات (لتحليل ملفات PDF)
    application.add_handler(MessageHandler(filters.Document.ALL, handle_document))

    # بدء تشغيل البوت
    logger.info("بدء تشغيل البوت...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()

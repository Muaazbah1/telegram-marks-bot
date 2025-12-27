import logging
import os
import io
from telegram import Update, Bot
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# استيراد الدوال من الملفات الأخرى
from config import TELEGRAM_BOT_TOKEN, STATISTICS_OUTPUT_CHANNEL_ID, UNIVERSITIES
from database import init_db, register_student, get_student_info_by_user_id, get_student_info_by_id, get_all_students, update_student_name
from pdf_parser import parse_grades_pdf # تم تصحيح اسم الدالة
from data_processor import process_grades, create_grades_histogram, create_admin_report_pdf, fix_arabic

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
    """
    يعالج المستندات المرسلة (ملفات PDF) لتحليل العلامات وإرسال النتائج.
    """
    user_id = update.effective_user.id
    
    # التحقق من أن الملف هو PDF
    if update.message.document and update.message.document.mime_type == 'application/pdf':
        
        # 1. التحقق من أن المستخدم هو المشرف
        if str(user_id) != STATISTICS_OUTPUT_CHANNEL_ID:
            await update.message.reply_text("عذراً، لا يمكن إلا للمشرف إرسال ملفات العلامات.")
            return

        pdf_path = None
        try:
            # 2. تنزيل الملف
            file = await update.message.document.get_file()
            pdf_path = os.path.join("/tmp", update.message.document.file_name)
            await file.download_to_drive(pdf_path)
            
            await update.message.reply_text("تم استلام الملف. يرجى الانتظار، تتم معالجة العلامات...")

            # 3. تحليل ملف PDF
            grades_data = parse_grades_pdf(pdf_path)
            if not grades_data:
                await update.message.reply_text("فشل تحليل ملف PDF. قد يكون التنسيق غير مدعوم أو لا يحتوي على بيانات علامات.")
                os.remove(pdf_path)
                return

            # 4. معالجة البيانات
            course_name = update.message.document.file_name.replace(".pdf", "")
            student_results, admin_pdf_buffer = process_grades(grades_data, course_name=course_name)
            
            # 5. إرسال النتائج الفردية
            if student_results:
                for user_id, result in student_results.items():
                    # التحقق من معلومات الطالب
                    student_info = get_student_info_by_user_id(user_id)
                    if not student_info:
                        logger.warning(f"الطالب {user_id} مسجل ولكن لا توجد معلومات في قاعدة البيانات.")
                        continue
                    
                    student_id, student_name, _, _ = student_info
                    
                    # إنشاء مخطط الأعمدة (Histogram)
                    plot_buffer = create_grades_histogram(
                        result['all_grades'], 
                        result['grade']
                    )
                    
                    # تصحيح الاسم في الرسالة النصية (الحل النهائي)
                    fixed_name = fix_arabic(student_name)[::-1] if student_name else 'غير متوفر'
                    
                    # إرسال الرسالة
                    message_text = (
                        f"نتيجتك في المادة:\n"
                        f"الرقم الجامعي: {student_id}\n"
                        f"الاسم: {fixed_name}\n"
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
            
            # 6. إرسال تقرير المشرف (بعد إرسال النتائج الفردية)
            if admin_pdf_buffer:
                await context.bot.send_document(
                    chat_id=STATISTICS_OUTPUT_CHANNEL_ID,
                    document=admin_pdf_buffer,
                    filename=f"تقرير_علامات_{course_name}.pdf",
                    caption=f"✅ تم الانتهاء من معالجة ملف العلامات {course_name}.pdf.\n\nالتقرير الإحصائي الشامل مرفق."
                )
                await update.message.reply_text("✅ تم الانتهاء من معالجة الملف وإرسال التقرير الإحصائي إلى قناة المشرف.")

        except Exception as e:
            logger.error(f"خطأ أثناء معالجة الملف: {e}")
            await update.message.reply_text(f"❌ حدث خطأ غير متوقع أثناء معالجة الملف: {e}")
            # إرسال رسالة خطأ للمشرف
            await context.bot.send_message(
                chat_id=STATISTICS_OUTPUT_CHANNEL_ID,
                text=f"❌ خطأ فادح أثناء معالجة ملف العلامات:\n{e}"
            )
        finally:
            # 7. تنظيف الملف المؤقت
            if pdf_path and os.path.exists(pdf_path):
                os.remove(pdf_path)
    else:
        await update.message.reply_text("الرجاء إرسال ملف علامات بصيغة PDF.")


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

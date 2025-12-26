# bot.py
import logging
import os
import re
import pandas as pd
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler
from config import TELEGRAM_BOT_TOKEN, UNIVERSITIES, DB_NAME, MARKS_PDF_PATH, ADMIN_IDS, STATISTICS_OUTPUT_CHANNEL_ID, STATISTICS_OUTPUT_FILE, NORMAL_DISTRIBUTION_IMAGE
from database import Database
from pdf_parser import parse_pdf_marks
from data_processor import process_marks_data, generate_normal_distribution_plot

# إعداد التسجيل (Logging)
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# حالات المحادثة
SELECT_UNIVERSITY, SELECT_FACULTY, ENTER_STUDENT_ID = range(3)

# قاعدة البيانات
db = Database()

# --- الدوال المساعدة ---

def get_university_keyboard():
    """ينشئ لوحة مفاتيح لاختيار الجامعة."""
    keyboard = []
    for uni_name in UNIVERSITIES.keys():
        keyboard.append([InlineKeyboardButton(uni_name, callback_data=f"uni_{uni_name}")])
    return InlineKeyboardMarkup(keyboard)

def get_faculty_keyboard(university_name):
    """ينشئ لوحة مفاتيح لاختيار الكلية."""
    keyboard = []
    faculties = UNIVERSITIES.get(university_name, {})
    for faculty_name, faculty_code in faculties.items():
        keyboard.append([InlineKeyboardButton(faculty_name, callback_data=f"fac_{faculty_code}")])
    return InlineKeyboardMarkup(keyboard)

# --- معالجات الأوامر والرسائل ---

async def start_command(update: Update, context):
    """يرسل رسالة ترحيب ويطلب اختيار الجامعة."""
    user_id = update.effective_user.id
    
    # التحقق مما إذا كان الطالب مسجلاً مسبقاً
    student_info = db.get_student_info(user_id)
    if student_info and student_info[3] == 1: # is_registered == 1
        await update.message.reply_text(
            f"أهلاً بك مجدداً يا {update.effective_user.first_name}!\n"
            f"أنت مسجل حالياً لـ: {student_info[0]} - {student_info[1]} بالرقم الجامعي: {student_info[2]}\n"
            "للحصول على نتيجتك، أرسل الأمر /mark."
        )
        return

    # بدء عملية التسجيل
    await update.message.reply_text(
        "أهلاً بك في بوت العلامات! يرجى اختيار جامعتك لبدء التسجيل:",
        reply_markup=get_university_keyboard()
    )
    # حفظ حالة المحادثة
    context.user_data['state'] = SELECT_UNIVERSITY

async def callback_query_handler(update: Update, context):
    """يتعامل مع ضغطات الأزرار المضمنة (Inline Buttons)."""
    query = update.callback_query
    await query.answer()
    data = query.data
    
    user_id = query.from_user.id
    current_state = context.user_data.get('state')

    if data.startswith("uni_") and current_state == SELECT_UNIVERSITY:
        university_name = data.split("_")[1]
        context.user_data['university'] = university_name
        
        # الانتقال لاختيار الكلية
        await query.edit_message_text(
            f"لقد اخترت: {university_name}\nالآن، يرجى اختيار كليتك:",
            reply_markup=get_faculty_keyboard(university_name)
        )
        context.user_data['state'] = SELECT_FACULTY
        
    elif data.startswith("fac_") and current_state == SELECT_FACULTY:
        faculty_code = data.split("_")[1]
        
        # البحث عن اسم الكلية من الكود
        faculty_name = next((name for name, code in UNIVERSITIES.get(context.user_data['university'], {}).items() if code == faculty_code), "كلية غير معروفة")
        
        context.user_data['faculty'] = faculty_name
        
        # الانتقال لإدخال الرقم الجامعي
        await query.edit_message_text(
            f"لقد اخترت: {faculty_name}\nالآن، يرجى إرسال رقمك الجامعي (مثال: 202012345):"
        )
        context.user_data['state'] = ENTER_STUDENT_ID
        
    else:
        await query.edit_message_text("حدث خطأ أو انتهت صلاحية هذا الخيار. يرجى البدء من جديد باستخدام /start.")

async def handle_student_id(update: Update, context):
    """يتعامل مع إدخال الرقم الجامعي."""
    user_id = update.effective_user.id
    current_state = context.user_data.get('state')
    
    if current_state == ENTER_STUDENT_ID:
        student_id = update.message.text.strip()
        
        # التحقق من أن الرقم الجامعي يتكون من 9 أرقام (افتراض)
        if not re.match(r"^\d{5}$", student_id):
            await update.message.reply_text("الرقم الجامعي غير صحيح. يرجى إدخال 5 أرقام فقط.")
            return
            
        university = context.user_data.get('university')
        faculty = context.user_data.get('faculty')
        
        # حفظ البيانات في قاعدة البيانات
        if db.register_student(user_id, university, faculty, student_id):
            await update.message.reply_text(
                f"تم تسجيلك بنجاح!\n"
                f"الجامعة: {university}\n"
                f"الكلية: {faculty}\n"
                f"الرقم الجامعي: {student_id}\n"
                "فور صدور العلامات، سنرسل لك رسالة خاصة. يمكنك طلب نتيجتك في أي وقت باستخدام الأمر /mark."
            )
            # مسح حالة المحادثة
            context.user_data['state'] = None
        else:
            await update.message.reply_text(
                "عذراً، هذا الرقم الجامعي مسجل مسبقاً. يرجى التأكد من الرقم أو التواصل مع الدعم."
            )
    else:
        # إذا لم يكن في حالة إدخال الرقم الجامعي، يتجاهل الرسالة أو يطلب /start
        await update.message.reply_text("يرجى البدء باستخدام الأمر /start أولاً للتسجيل.")

async def get_mark_command(update: Update, context):
    """يرسل علامة الطالب والتحليل الإحصائي الخاص به."""
    user_id = update.effective_user.id
    
    student_info = db.get_student_info(user_id)
    if not student_info or student_info[3] == 0:
        await update.message.reply_text("أنت غير مسجل. يرجى البدء بالتسجيل باستخدام الأمر /start.")
        return
        
    student_id = student_info[2]
    mark_data = db.get_student_mark(student_id)
    
    if not mark_data:
        await update.message.reply_text("لم يتم إدخال العلامات بعد. يرجى المحاولة لاحقاً.")
        return
        
    mark, percentile = mark_data
    
    # 1. إرسال رسالة نصية
    message_text = (
        f"🎉 تهانينا يا {update.effective_user.first_name}! 🎉\n"
        f"رقمك الجامعي: {student_id}\n"
        f"علامتك هي: **{mark:.2f}**\n"
        f"موقعك الإحصائي (Percentile): **{percentile * 100:.2f}%**\n"
        "هذا يعني أنك تتفوق على حوالي "
        f"**{percentile * 100:.2f}%** من زملائك في هذا التوزيع."
    )
    await update.message.reply_text(message_text, parse_mode='Markdown')
    
    # 2. إرسال صورة التوزيع الطبيعي
    
    # جلب جميع العلامات لرسم التوزيع
    all_marks_data = db.get_all_marks()
    if not all_marks_data:
        await update.message.reply_text("لا يمكن رسم التوزيع لعدم توفر بيانات العلامات الكافية.")
        return
        
    # تحويل البيانات إلى الشكل المطلوب للمعالجة
    marks_for_plot = [(row[0], row[1]) for row in all_marks_data]
    
    # إنشاء DataFrame من البيانات
    marks_df = pd.DataFrame(marks_for_plot, columns=['student_id', 'mark'])
    
    # توليد الصورة الخاصة بالطالب
    student_plot_path = f"plot_{student_id}.png"
    generate_normal_distribution_plot(marks_df, mark, student_id, student_plot_path)
    
    await update.message.reply_photo(
        photo=student_plot_path,
        caption="صورة توضح موقع علامتك من التوزيع الطبيعي للعلامات."
    )
    
    # حذف الصورة بعد إرسالها
    os.remove(student_plot_path)

async def handle_pdf_upload(update: Update, context):
    """يتعامل مع تحميل ملف PDF من قبل المشرف."""
    user_id = update.effective_user.id
    
    # التحقق من أن المستخدم هو مشرف
    if user_id not in ADMIN_IDS:
        await update.message.reply_text("عذراً، لا تملك صلاحية رفع ملفات العلامات.")
        return
        
    # التحقق من أن الملف المرفوع هو PDF
    if update.message.document and update.message.document.mime_type == 'application/pdf':
        file_id = update.message.document.file_id
        new_file = await context.bot.get_file(file_id)
        
        # تحميل الملف
        await new_file.download_to_drive(MARKS_PDF_PATH)
        await update.message.reply_text(f"تم تحميل ملف العلامات بنجاح. جاري تحليل البيانات...")
        
        try:
            # 1. تحليل ملف PDF
            marks_data = parse_pdf_marks(MARKS_PDF_PATH)
            if not marks_data:
                await update.message.reply_text("فشل تحليل ملف PDF. لم يتم العثور على علامات. يرجى مراجعة تنسيق الملف.")
                return
                
            await update.message.reply_text(f"تم استخراج {len(marks_data)} علامة. جاري المعالجة الإحصائية...")
            
            # 2. المعالجة الإحصائية وحساب الـ percentiles
            # process_marks_data ترجع (db_data, stats, report_path, general_plot_path)
            db_data, stats, report_path, general_plot_path = process_marks_data(marks_data)
            
            # 3. حفظ البيانات في قاعدة البيانات
            db.save_marks(db_data)
            await update.message.reply_text("تم حفظ العلامات والتحليل الإحصائي في قاعدة البيانات بنجاح.")
            
            # 4. إرسال النتائج الإحصائية إلى قناة المشرف
            
            # إرسال التقرير النصي (Markdown)
            await context.bot.send_document(
                chat_id=STATISTICS_OUTPUT_CHANNEL_ID,
                document=report_path,
                caption="تقرير التحليل الإحصائي لعلامات الطلاب."
            )
            
            # إرسال صورة التوزيع الطبيعي العام
            await context.bot.send_photo(
                chat_id=STATISTICS_OUTPUT_CHANNEL_ID,
                photo=general_plot_path,
                caption="صورة التوزيع الطبيعي العام للعلامات."
            )
            
            # 5. إرسال العلامات الفردية للطلاب المسجلين
            await update.message.reply_text("جاري إرسال العلامات الفردية للطلاب المسجلين...")
            
            registered_students = db.get_all_registered_students()
            
            # نحتاج إلى DataFrame كامل لحساب الـ percentile ورسم التوزيع لكل طالب
            marks_df_full = pd.DataFrame(db_data, columns=['student_id', 'mark', 'percentile'])
            
            for telegram_id, student_id in registered_students:
                # البحث عن علامة الطالب في DataFrame
                student_row = marks_df_full[marks_df_full['student_id'] == student_id]
                
                if not student_row.empty:
                    mark = student_row['mark'].iloc[0]
                    percentile = student_row['percentile'].iloc[0]
                    
                    # توليد الصورة الخاصة بالطالب
                    student_plot_path = f"plot_{student_id}.png"
                    generate_normal_distribution_plot(marks_df_full, mark, student_id, student_plot_path)
                    
                    message_text = (
                        f"🎉 صدرت علاماتك! 🎉\n"
                        f"رقمك الجامعي: {student_id}\n"
                        f"علامتك هي: **{mark:.2f}**\n"
                        f"موقعك الإحصائي (Percentile): **{percentile * 100:.2f}%**"
                    )
                    
                    try:
                        await context.bot.send_message(
                            chat_id=telegram_id,
                            text=message_text,
                            parse_mode='Markdown'
                        )
                        await context.bot.send_photo(
                            chat_id=telegram_id,
                            photo=student_plot_path,
                            caption="صورة توضح موقع علامتك من التوزيع الطبيعي للعلامات."
                        )
                    except Exception as e:
                        logger.error(f"فشل إرسال رسالة للطالب {telegram_id}: {e}")
                        
                    # حذف الصورة بعد إرسالها
                    if os.path.exists(student_plot_path):
                        os.remove(student_plot_path)
                        
            await update.message.reply_text("اكتمل إرسال العلامات الفردية للطلاب المسجلين.")
            
        except Exception as e:
            logger.error(f"خطأ أثناء معالجة ملف PDF: {e}")
            await update.message.reply_text(f"حدث خطأ أثناء معالجة الملف: {e}")
            
        finally:
            # حذف ملف PDF بعد الانتهاء
            if os.path.exists(MARKS_PDF_PATH):
                os.remove(MARKS_PDF_PATH)
                
    else:
        await update.message.reply_text("يرجى إرسال ملف PDF يحتوي على العلامات.")

async def error_handler(update: Update, context):
    """يسجل الأخطاء التي تسببها التحديثات."""
    logger.error("حدث خطأ: %s", context.error)
    if update and update.effective_message:
        await update.effective_message.reply_text("عذراً، حدث خطأ غير متوقع. يرجى المحاولة لاحقاً.")

def main():
    """يبدأ تشغيل البوت."""
    if TELEGRAM_BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
        logger.error("يرجى تعديل ملف config.py وإضافة TELEGRAM_BOT_TOKEN الخاص بك.")
        return

    # إنشاء التطبيق وتمرير التوكن
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # معالجات الأوامر
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("mark", get_mark_command))
    
    # معالج الاستعلامات المضمنة (Inline Query)
    application.add_handler(CallbackQueryHandler(callback_query_handler))
    
    # معالج رسائل النص (لإدخال الرقم الجامعي)
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_student_id))
    
    # معالج تحميل ملف PDF (للمشرفين)
    application.add_handler(MessageHandler(filters.Document.ALL, handle_pdf_upload))

    # معالج الأخطاء
    application.add_error_handler(error_handler)

    # بدء البوت
    logger.info("بدء تشغيل البوت...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()

# telegram_marks_bot/bot.py
import logging
import os
import re
import pandas as pd
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler, ConversationHandler
from config import TELEGRAM_BOT_TOKEN, ADMIN_IDS, STATISTICS_OUTPUT_CHANNEL_ID
from database import Database
from pdf_parser import parse_pdf_marks, convert_arabic_to_latin
from data_processor import process_marks_data, plot_normal_distribution
from tabulate import tabulate
try:
    from fpdf import FPDF
except ImportError:
    logger.error("مكتبة fpdf2 غير مثبتة. يرجى تشغيل 'pip install fpdf2' أو التأكد من تحديث requirements.txt.")
    exit()

# إعداد التسجيل (Logging)
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# حالات المحادثة
(SELECT_UNIVERSITY, SELECT_FACULTY, ENTER_STUDENT_ID) = range(3)

# قاعدة البيانات
db = Database()

# --- وظائف المساعدة ---

def get_registration_keyboard():
    """ينشئ لوحة مفاتيح لاختيار الجامعة."""
    keyboard = [
        [InlineKeyboardButton("جامعة حلب", callback_data='uni_aleppo')],
    ]
    return InlineKeyboardMarkup(keyboard)

def get_faculty_keyboard():
    """ينشئ لوحة مفاتيح لاختيار الكلية."""
    keyboard = [
        [InlineKeyboardButton("كلية الطب البشري", callback_data='fac_medicine')],
    ]
    return InlineKeyboardMarkup(keyboard)

# --- معالجات الأوامر ---

async def start(update: Update, context):
    """يبدأ المحادثة ويطلب اختيار الجامعة."""
    user_id = update.effective_user.id
    
    # التحقق مما إذا كان الطالب مسجلاً بالفعل
    if db.get_student_registration(user_id):
        await update.message.reply_text(
            "أهلاً بك مجدداً! أنت مسجل بالفعل. يمكنك استخدام الأمر /mark للحصول على علامتك فور صدورها."
        )
        return ConversationHandler.END
        
    await update.message.reply_text(
        "أهلاً بك في بوت العلامات. يرجى اختيار الجامعة:",
        reply_markup=get_registration_keyboard()
    )
    return SELECT_UNIVERSITY

async def button_callback(update: Update, context):
    """يعالج ضغطات الأزرار المضمنة."""
    query = update.callback_query
    await query.answer()
    data = query.data
    user_id = query.from_user.id
    
    if data.startswith('uni_'):
        university = data.split('_')[1]
        context.user_data['university'] = university
        await query.edit_message_text(
            f"تم اختيار: {university}. يرجى اختيار الكلية:",
            reply_markup=get_faculty_keyboard()
        )
        return SELECT_FACULTY
        
    elif data.startswith('fac_'):
        faculty = data.split('_')[1]
        context.user_data['faculty'] = faculty
        await query.edit_message_text(
            f"تم اختيار: {faculty}. يرجى إرسال رقمك الجامعي (5 أرقام):"
        )
        return ENTER_STUDENT_ID

async def enter_student_id(update: Update, context):
    """يعالج إدخال الرقم الجامعي ويحفظ التسجيل."""
    user_id = update.effective_user.id
    
    # تحويل الأرقام العربية إلى لاتينية قبل التحقق
    student_id = convert_arabic_to_latin(update.message.text.strip())
    
    # التحقق من أن الرقم الجامعي يتكون من 5 أرقام
    if not re.match(r"^\d{5}$", student_id):
        await update.message.reply_text("الرقم الجامعي غير صحيح. يرجى إدخال 5 أرقام فقط.")
        return ENTER_STUDENT_ID
        
    university = context.user_data.get('university')
    faculty = context.user_data.get('faculty')
    
    # حفظ التسجيل في قاعدة البيانات
    db.register_student(user_id, student_id, university, faculty)
    
    await update.message.reply_text(
        f"تم تسجيلك بنجاح!\nالجامعة: {university}\nالكلية: {faculty}\nالرقم الجامعي: {student_id}\n\n"
        "ستصلك رسالة بعلامتك فور صدورها. يمكنك استخدام الأمر /mark للاستعلام في أي وقت."
    )
    return ConversationHandler.END

async def cancel(update: Update, context):
    """يلغي عملية التسجيل."""
    await update.message.reply_text("تم إلغاء عملية التسجيل.")
    return ConversationHandler.END

async def get_mark(update: Update, context):
    """يرسل علامة الطالب والتحليل الإحصائي الخاص به."""
    user_id = update.effective_user.id
    
    # 1. التحقق من التسجيل
    registration = db.get_student_registration(user_id)
    if not registration:
        await update.message.reply_text("أنت غير مسجل. يرجى استخدام الأمر /start للتسجيل أولاً.")
        return
        
    student_id = registration[1]
    
    # 2. التحقق من وجود العلامة
    mark_data = db.get_student_mark(student_id)
    if not mark_data:
        await update.message.reply_text("لم تصدر علامتك بعد. يرجى المحاولة لاحقاً.")
        return
        
    # 3. استخراج البيانات
    final_mark = mark_data[1]
    percentile = mark_data[2]
    # all_columns هو سلسلة نصية تمثل قائمة الأعمدة، يجب تحويلها إلى قائمة
    all_columns_str = mark_data[3]
    # استخدام eval بحذر، أو استخدام طريقة أكثر أمانًا مثل json.loads إذا تم تخزينها كـ JSON
    # بما أننا نستخدم sqlite، نفترض أنها مخزنة كسلسلة نصية قابلة للتحويل إلى قائمة
    try:
        all_columns = eval(all_columns_str)
    except:
        all_columns = [all_columns_str] # في حال فشل التحويل، نضع السلسلة كما هي
    
    # 4. إنشاء رسالة مفصلة بجميع الأعمدة
    
    # تحويل قائمة الأعمدة إلى جدول tabulate
    table_data = [
        ["البيان", "القيمة"]
    ]
    
    # إضافة جميع الأعمدة المستخرجة
    # يمكننا افتراض أن العمود الأول هو الاسم، والثاني هو الرقم الجامعي، والثالث هو العلامة النهائية
    # ولكن لضمان المرونة، سنعرضها كأعمدة مرقمة
    for i, col_value in enumerate(all_columns):
        table_data.append([f"العمود {i+1}", str(col_value)])
        
    # إضافة العلامة والـ percentile
    table_data.append(["العلامة النهائية", f"{final_mark:.2f}"])
    table_data.append(["الـ Percentile", f"{percentile:.2f}%"])
    
    mark_table = tabulate(table_data, headers="firstrow", tablefmt="fancy_grid", numalign="left", stralign="right")
    
    message_text = (
        f"🎉 **علامتك النهائية صدرت!** 🎉\n\n"
        f"الرقم الجامعي: `{student_id}`\n\n"
        f"```\n{mark_table}\n```\n\n"
        f"موقعك الإحصائي: أنت أفضل من **{percentile:.2f}%** من زملائك."
    )
    
    # 5. توليد صورة التوزيع الطبيعي الخاصة بالطالب
    
    # نحتاج إلى جميع العلامات لإنشاء الرسم البياني
    all_marks_data = db.get_all_marks()
    if not all_marks_data:
        await update.message.reply_text(message_text)
        return
        
    # تحويل البيانات إلى DataFrame
    df = pd.DataFrame(all_marks_data, columns=['student_id', 'final_mark', 'percentile', 'all_columns'])
    
    # إنشاء مجلد مؤقت لحفظ الصور
    temp_dir = "temp_plots"
    os.makedirs(temp_dir, exist_ok=True)
    
    # توليد الرسم البياني
    plot_path = os.path.join(temp_dir, f"plot_{student_id}.png")
    plot_normal_distribution(df['final_mark'], final_mark, plot_path)
    
    # 6. إرسال الرسالة والصورة
    await update.message.reply_photo(
        photo=plot_path,
        caption=message_text,
        parse_mode='Markdown'
    )
    
    # 7. تنظيف الملف المؤقت
    os.remove(plot_path)
    os.rmdir(temp_dir) # حذف المجلد المؤقت بعد الاستخدام

async def handle_document(update: Update, context):
    """يعالج ملفات PDF المرسلة من المشرف."""
    user_id = update.effective_user.id
    
    # 1. التحقق من أن الملف هو PDF
    if update.message.document.mime_type != 'application/pdf':
        await update.message.reply_text("يرجى إرسال ملف PDF فقط.")
        return
        
    # 2. التحقق من صلاحية المشرف (أو حساب Pyrogram المعاد توجيه الملف منه)
    if user_id not in ADMIN_IDS:
        await update.message.reply_text("عذراً، لا تملك صلاحية معالجة ملفات العلامات.")
        return
        
    await update.message.reply_text("تم استلام ملف العلامات. جاري المعالجة...")
    
    # 3. تحميل الملف
    file_id = update.message.document.file_id
    new_file = await context.bot.get_file(file_id)
    
    temp_dir = "temp_files"
    os.makedirs(temp_dir, exist_ok=True)
    pdf_path = os.path.join(temp_dir, f"{file_id}.pdf")
    
    await new_file.download_to_drive(pdf_path)
    
    try:
        # 4. تحليل ملف PDF
        df, headers = parse_pdf_marks(pdf_path)
        
        # 5. معالجة البيانات الإحصائية
        db_data, stats, image_path, pdf_report_path = process_marks_data(df, temp_dir)
        
        # 6. حفظ العلامات في قاعدة البيانات
        db.save_marks(db_data)
        
        # 7. إرسال التقرير الإحصائي إلى القناة
        
        # إنشاء رسالة تلخيصية
        summary_table = [
            ["الإحصائية", "القيمة"],
            ["المتوسط", f"{stats['Mean']:.2f}"],
            ["الانحراف المعياري", f"{stats['Standard Deviation (SD)']:.2f}"],
            ["العدد الكلي", f"{stats['Total Students']}"]
        ]
        summary_text = tabulate(summary_table, headers="firstrow", tablefmt="fancy_grid", numalign="left", stralign="right")
        
        caption = (
            "📊 **تقرير التحليل الإحصائي لعلامات الطلاب** 📊\n\n"
            f"```\n{summary_text}\n```\n\n"
            "يرجى الاطلاع على الملف المرفق للحصول على التقرير الكامل وترتيب الطلاب."
        )
        
        # إرسال التقرير كملف PDF
        await context.bot.send_document(
            chat_id=STATISTICS_OUTPUT_CHANNEL_ID,
            document=pdf_report_path,
            caption=caption,
            parse_mode='Markdown'
        )
        
        # 8. إرسال إشعار للمشرف
        await update.message.reply_text(
            "✅ **اكتملت المعالجة بنجاح!**\n\n"
            f"تم تحليل {stats['Total Students']} علامة وحفظها في قاعدة البيانات.\n"
            f"تم إرسال التقرير الإحصائي إلى القناة: {STATISTICS_OUTPUT_CHANNEL_ID}."
        )
        
    except ValueError as e:
        await update.message.reply_text(f"❌ خطأ أثناء معالجة ملف PDF: {e}")
        logger.error(f"خطأ أثناء معالجة ملف PDF: {e}")
    except Exception as e:
        await update.message.reply_text(f"❌ حدث خطأ غير متوقع أثناء المعالجة: {e}")
        logger.error(f"خطأ غير متوقع: {e}")
    finally:
        # 9. تنظيف الملفات المؤقتة
        if os.path.exists(pdf_path):
            os.remove(pdf_path)
        if os.path.exists(image_path):
            os.remove(image_path)
        if os.path.exists(pdf_report_path):
            os.remove(pdf_report_path)
        if os.path.exists(temp_dir):
            # محاولة حذف المجلد المؤقت
            try:
                os.rmdir(temp_dir)
            except OSError:
                # إذا لم يكن فارغاً، نتجاهل الخطأ
                pass

def main():
    """يبدأ تشغيل البوت."""
    logger.info("بدء تشغيل البوت...")
    
    # إنشاء التطبيق
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    
    # معالج المحادثة للتسجيل
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            SELECT_UNIVERSITY: [CallbackQueryHandler(button_callback, pattern='^uni_')],
            SELECT_FACULTY: [CallbackQueryHandler(button_callback, pattern='^fac_')],
            ENTER_STUDENT_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, enter_student_id)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
    
    application.add_handler(conv_handler)
    
    # معالج أمر الحصول على العلامة
    application.add_handler(CommandHandler("mark", get_mark))
    
    # معالج ملفات PDF المرسلة من المشرف
    application.add_handler(MessageHandler(filters.Document.ALL, handle_document))
    
    # بدء البوت
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    # التأكد من وجود مكتبة fpdf2
    try:
        from fpdf import FPDF
    except ImportError:
        logger.error("مكتبة fpdf2 غير مثبتة. يرجى تشغيل 'pip install fpdf2' أو التأكد من تحديث requirements.txt.")
        exit()
        
  

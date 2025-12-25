# config.py

# إعدادات بوت تليجرام
TELEGRAM_BOT_TOKEN = "8308461865:AAG7viIjYF7C050AnkLebXQ5pasgzYSSdK0"
# معرف القناة التي سيتم الاستماع إليها لتحميل ملفات PDF الجديدة
TELEGRAM_CHANNEL_USERNAME = "@jjgradebot" # مثال: @Aleppo_Med_Marks

# إعدادات قاعدة البيانات
DB_NAME = "students_marks.db"

# إعدادات الجامعة والكلية
# يمكن توسيع هذه القائمة لاحقاً
UNIVERSITIES = {
    "جامعة حلب": {
        "كلية الطب البشري": "طب بشري"
    }
}

# إعدادات ملف العلامات
MARKS_PDF_PATH = "marks.pdf" # المسار الذي سيتم حفظ ملف العلامات فيه مؤقتاً

# إعدادات التحليل الإحصائي
# يجب استبداله بمعرف القناة (Channel ID) التي سيرسل إليها البوت النتائج الإحصائية
# يجب أن يكون المعرف على شكل -100xxxxxxxxxx
STATISTICS_OUTPUT_CHANNEL_ID = -100123456789 
STATISTICS_OUTPUT_FILE = "Statistics_Report.md"
NORMAL_DISTRIBUTION_IMAGE = "Normal_Distribution.png"

# قائمة بمعرفات المستخدمين (Telegram IDs) المسموح لهم بإرسال ملفات العلامات
ADMIN_IDS = [1406058239] # استبدل بمعرف التليجرام الخاص بك

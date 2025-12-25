# channel_monitor.py
import logging
import os
from pyrogram import Client, filters
from pyrogram.errors import SessionPasswordNeeded, PhoneCodeInvalid, FloodWait
from config import TELEGRAM_BOT_TOKEN # نحتاج فقط للتوكن للحصول على اسم البوت

# إعداد التسجيل (Logging)
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# --- إعدادات Pyrogram ---
# يجب الحصول على هذه القيم من موقع my.telegram.org
API_ID = 34958063 # استبدل بمعرف API الخاص بك
API_HASH = "19095cb702477bb170752463a3cd46a0" # استبدل بـ API Hash الخاص بك
BOT_USERNAME = "@My_gradesbot" # استبدل باسم المستخدم للبوت الرسمي (بدون @)
CHANNEL_USERNAME = "@jjgradebot" # استبدل باسم مستخدم القناة (مثال: @Aleppo_Med_Marks)

# --- دالة معالجة رسائل القناة ---
async def handle_channel_post(client, message):
    """
    تستمع لرسائل القناة، وإذا كان الملف المرفق هو PDF، تعيد توجيهه إلى البوت الرسمي.
    """
    # التحقق من أن الرسالة من القناة المحددة
    if message.chat.username == CHANNEL_USERNAME.lstrip('@'):
        # التحقق من أن الرسالة تحتوي على مستند وأن نوعه هو PDF
        if message.document and message.document.mime_type == "application/pdf":
            logger.info(f"تم العثور على ملف PDF جديد في القناة: {CHANNEL_USERNAME}")
            
            try:
                # إعادة توجيه الرسالة إلى البوت الرسمي
                await message.forward(BOT_USERNAME)
                logger.info(f"تم إعادة توجيه ملف PDF بنجاح إلى البوت: {BOT_USERNAME}")
                
                # يمكن إرسال رسالة تأكيد إلى القناة (إذا كان الحساب مشرفاً)
                # await client.send_message(CHANNEL_USERNAME, "تم استلام ملف العلامات وبدء المعالجة.")
                
            except FloodWait as e:
                logger.error(f"FloodWait: يجب الانتظار {e.value} ثوانٍ قبل إرسال المزيد.")
            except Exception as e:
                logger.error(f"فشل إعادة توجيه الرسالة: {e}")

def main():
    """
    تبدأ تشغيل حساب المستخدم المبرمج.
    """
    if API_ID == 1234567 or API_HASH == "YOUR_API_HASH":
        logger.error("يرجى تعديل ملف channel_monitor.py وإضافة API_ID و API_HASH الخاصين بك.")
        return
        
    # يمكن استخراج اسم البوت من التوكن إذا لم يتم تحديده
    # ولكن يفضل أن يتم تحديده يدوياً في config.py أو هنا
    
    # إنشاء العميل (Client)
    # "my_account" هو اسم ملف الجلسة الذي سيتم إنشاؤه
    app = Client("my_account", api_id=API_ID, api_hash=API_HASH)
    
    # إضافة معالج الرسائل
    app.add_handler(
        filters.chat(CHANNEL_USERNAME) & filters.document,
        handle_channel_post
    )
    
    logger.info("بدء تشغيل مراقب القناة (Pyrogram)...")
    
    try:
        app.run()
    except Exception as e:
        logger.error(f"خطأ أثناء تشغيل Pyrogram: {e}")

if __name__ == '__main__':
    main()

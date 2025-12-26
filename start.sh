#!/bin/bash

# هذا الملف يقوم بتشغيل كلا العمليتين (البوت والمراقب) معاً

# تشغيل البوت الرسمي في الخلفية
echo "Starting Telegram Bot (bot.py)..."
python bot.py &

# تشغيل مراقب القناة في المقدمة
# ملاحظة: يجب أن يكون ملف my_account.session موجوداً في نفس المجلد
echo "Starting Channel Monitor (channel_monitor.py)..."
python channel_monitor.py

# إذا توقفت العملية الأخيرة، ستتوقف الحاوية.
# يمكن استخدام supervisord كبديل أكثر قوة إذا لزم الأمر.

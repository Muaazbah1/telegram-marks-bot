#!/bin/bash

# 1. تثبيت حزمة الخطوط
sudo apt-get update
sudo apt-get install -y ttf-dejavu-core

# 2. إنشاء مجلد محلي للخطوط
mkdir -p /app/fonts

# 3. نسخ الخطوط المطلوبة إلى المجلد المحلي
# المسار الافتراضي لخطوط DejaVu بعد التثبيت
cp /usr/share/fonts/truetype/dejavu/DejaVuSans.ttf /app/fonts/
cp /usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf /app/fonts/

# ... (باقي أوامر بدء تشغيل البوت)


# تشغيل البوت الرسمي في الخلفية
echo "Starting Telegram Bot (bot.py)..."
python bot.py &
BOT_PID=$! # حفظ معرف العملية

# تشغيل مراقب القناة في الخلفية
echo "Starting Channel Monitor (channel_monitor.py)..."
python channel_monitor.py &
MONITOR_PID=$! # حفظ معرف العملية
#!/bin/bash

# تثبيت حزمة خطوط DejaVu لدعم اللغة العربية في تقارير PDF


# ... (باقي أوامر بدء تشغيل البوت)

# الانتظار حتى تنتهي إحدى العمليتين
wait -n

# إذا توقفت إحدى العمليتين، قم بقتل الأخرى وإغلاق الحاوية
echo "One of the processes stopped. Shutting down container."

# قتل العملية الأخرى لضمان التنظيف
kill $BOT_PID $MONITOR_PID

exit 1

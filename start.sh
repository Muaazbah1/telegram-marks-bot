#!/bin/bash

# --- مرحلة الإعداد: تثبيت الخطوط وضمان وجودها ---

# 1. تثبيت الأدوات الأساسية (curl) وحزمة الخطوط
# نستخدم أمر واحد لضمان التثبيت
sudo apt-get update
sudo apt-get install -y curl ttf-dejavu-core

# 2. إنشاء مجلد محلي للخطوط
mkdir -p /app/fonts

# 3. محاولة نسخ خطوط DejaVu (المسار الأصلي)
if [ -f /usr/share/fonts/truetype/dejavu/DejaVuSans.ttf ]; then
    cp /usr/share/fonts/truetype/dejavu/DejaVuSans.ttf /app/fonts/
    cp /usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf /app/fonts/
    echo "تم نسخ خطوط DejaVu بنجاح."
else
    echo "خطأ: لم يتم العثور على خطوط DejaVu في المسار المتوقع. محاولة تنزيل Noto Sans كبديل."
    # 4. تنزيل خطوط Noto Sans كبديل باستخدام curl (أكثر موثوقية من wget)
    curl -L -o /app/fonts/NotoSansArabic-Regular.ttf https://github.com/googlefonts/noto-fonts/raw/main/hinted/ttf/NotoSansArabic/NotoSansArabic-Regular.ttf
    curl -L -o /app/fonts/NotoSansArabic-Bold.ttf https://github.com/googlefonts/noto-fonts/raw/main/hinted/ttf/NotoSansArabic/NotoSansArabic-Bold.ttf
    
    # يجب التأكد من أن data_processor.py يستخدم Noto Sans في هذه الحالة
    # (تم تعديل data_processor.py في رسالة سابقة لاستخدام Noto كبديل )
fi

# --- مرحلة التشغيل: بدء تشغيل البوت ---

# تشغيل البوت الرسمي في الخلفية
echo "Starting Telegram Bot (bot.py)..."
python bot.py &
BOT_PID=$! # حفظ معرف العملية

# تشغيل مراقب القناة في الخلفية
echo "Starting Channel Monitor (channel_monitor.py)..."
python channel_monitor.py &
MONITOR_PID=$! # حفظ معرف العملية

# الانتظار حتى تنتهي إحدى العمليتين
wait -n

# إذا توقفت إحدى العمليتين، قم بقتل الأخرى وإغلاق الحاوية
echo "One of the processes stopped. Shutting down container."

# قتل العملية الأخرى لضمان التنظيف
kill $BOT_PID $MONITOR_PID

exit 1

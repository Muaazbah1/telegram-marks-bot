#!/bin/bash

# 1. إنشاء مجلد محلي للخطوط
mkdir -p /app/fonts

# 2. تنزيل الخطوط مباشرة إلى المجلد المحلي
# نستخدم خطوط Noto Sans العربية كبديل موثوق به ويدعم Unicode بشكل ممتاز
# إذا كان خط DejaVu هو المطلوب تحديداً، يمكن تنزيله أيضاً، لكن Noto Sans هو الأفضل للويب.
# سنلتزم بـ DejaVu حالياً لتجنب تغيير الكود في data_processor.py

# تنزيل خطوط DejaVu (نستخدم رابط مباشر لمصدر موثوق)
# ملاحظة: هذا الرابط قد يتغير، لكنه يمثل طريقة التنزيل المباشر
# سنستخدم طريقة التثبيت عبر apt-get مرة أخرى، ولكن سنضيف أمر التحقق من المسار.

# الطريقة الأفضل: التأكد من التثبيت ثم النسخ
sudo apt-get update
sudo apt-get install -y ttf-dejavu-core

# التحقق من وجود الخطوط قبل النسخ
if [ -f /usr/share/fonts/truetype/dejavu/DejaVuSans.ttf ]; then
    cp /usr/share/fonts/truetype/dejavu/DejaVuSans.ttf /app/fonts/
    cp /usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf /app/fonts/
    echo "تم نسخ خطوط DejaVu بنجاح."
else
    echo "خطأ: لم يتم العثور على خطوط DejaVu في المسار المتوقع."
    # كحل بديل، سنقوم بتنزيل خطوط Noto Sans (وهي بديل ممتاز للعربية)
    wget -O /app/fonts/NotoSansArabic-Regular.ttf https://github.com/googlefonts/noto-fonts/raw/main/hinted/ttf/NotoSansArabic/NotoSansArabic-Regular.ttf
    wget -O /app/fonts/NotoSansArabic-Bold.ttf https://github.com/googlefonts/noto-fonts/raw/main/hinted/ttf/NotoSansArabic/NotoSansArabic-Bold.ttf
    
    # يجب تعديل data_processor.py لاستخدام Noto Sans إذا تم تنزيله
fi

# ... (باقي أوامر بدء تشغيل البوت )

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

#!/bin/bash

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

#!/bin/bash

# تشغيل البوت الرسمي في الخلفية
echo "Starting Telegram Bot (bot.py)..."
python bot.py &
BOT_PID=$! # حفظ معرف العملية

# تشغيل مراقب القناة في الخلفية
echo "Starting Channel Monitor (channel_monitor.py)..."
python channel_monitor.py &
MONITOR_PID=$! # حفظ معرف العملية

# الانتظار حتى تنتهي إحدى العمليتين (في الوضع الطبيعي لن تنتهي أبداً)
# هذا يضمن أن الحاوية لا تغلق
wait -n

# إذا وصلت إلى هنا، فهذا يعني أن إحدى العمليتين قد توقفت.
echo "One of the processes stopped. Shutting down container."

# قتل العملية الأخرى لضمان التنظيف
kill $BOT_PID $MONITOR_PID

exit 1

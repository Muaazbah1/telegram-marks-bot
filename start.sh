#!/bin/bash

# تشغيل البوت الرسمي في الخلفية
echo "Starting Telegram Bot (bot.py)..."
python bot.py &

# تشغيل مراقب القناة في المقدمة
echo "Starting Channel Monitor (channel_monitor.py)..."
python channel_monitor.py

# إضافة أمر انتظار لمنع الحاوية من الإغلاق
wait

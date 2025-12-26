#!/bin/bash

# تشغيل مراقب القناة في الخلفية
echo "Starting Channel Monitor (channel_monitor.py) in background..."
python channel_monitor.py &

# تشغيل البوت الرسمي في المقدمة (هذا هو الذي سيبقى قيد التشغيل)
echo "Starting Telegram Bot (bot.py) in foreground..."
python bot.py

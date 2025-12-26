# Dockerfile

# استخدام صورة Python رسمية كقاعدة
FROM python:3.11-slim

# تعيين دليل العمل داخل الحاوية
WORKDIR /app

# نسخ ملفات التبعيات وتثبيتها
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# نسخ باقي ملفات المشروع
COPY . .

# جعل ملف التشغيل قابلاً للتنفيذ
RUN chmod +x entrypoint.sh

# الأمر الذي سيتم تنفيذه عند بدء تشغيل الحاوية
CMD ["./start.sh"]

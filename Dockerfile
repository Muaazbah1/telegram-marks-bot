# Dockerfile

# استخدام صورة Python رسمية كقاعدة
FROM python:3.11-slim

# تعيين دليل العمل داخل الحاوية
WORKDIR /app

# نسخ ملفات التبعيات وتثبيتها
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
# تثبيت خط عربي يدعم التوصيل (لـ fpdf2)
RUN apt-get update && apt-get install -y \
    fonts-noto-extra \
    && rm -rf /var/lib/apt/lists/*

# نسخ باقي ملفات المشروع
COPY . .

# جعل ملف التشغيل قابلاً للتنفيذ
RUN chmod +x start.sh

# الأمر الذي سيتم تنفيذه عند بدء تشغيل الحاوية
CMD ["./start.sh"]

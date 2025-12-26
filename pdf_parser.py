import pdfplumber
import re
import logging

logger = logging.getLogger(__name__)

def parse_grades_pdf(pdf_path):
    """
    يحلل ملف PDF للعلامات ويستخرج الرقم الجامعي، الاسم، والدرجة.
    يفترض أن كل سطر يحتوي على: رقم جامعي (5 أرقام)، اسم الطالب، ودرجة (رقم).
    """
    grades_data = []
    
    # النمط العام للبحث عن سطر يحتوي على رقم جامعي (5 أرقام) ودرجة (رقم)
    # هذا النمط يفترض أن الاسم يقع بين الرقم الجامعي والدرجة
    # مثال: 12345 محمد علي 85
    # سنستخدم نمطاً مرناً للبحث عن 5 أرقام متبوعة بنص متبوع برقم
    # النمط: (\d{5}) - 5 أرقام (الرقم الجامعي)
    # (.+?) - أي نص بينهما (الاسم)
    # (\d{1,3}) - رقم من 1 إلى 3 خانات (الدرجة)
    # قد تحتاج هذه الأنماط إلى تعديل دقيق بناءً على شكل ملف PDF الفعلي.
    # سنستخدم نمطاً يركز على استخراج 5 أرقام، ثم النص، ثم رقم الدرجة.
    # بما أننا لا نعرف التنسيق الدقيق، سنستخدم نمطاً عاماً ونقوم بالتنظيف لاحقاً.
    
    # النمط الأكثر أماناً: البحث عن 5 أرقام في بداية السطر أو بعد مسافة، متبوعة بنص، متبوعة برقم.
    # بما أننا لا نعرف التنسيق الدقيق، سنعتمد على استخراج كل النص في السطر ثم محاولة فصله.
    
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                # استخراج النص من الصفحة
                text = page.extract_text()
                if not text:
                    continue
                
                # تقسيم النص إلى أسطر
                lines = text.split('\n')
                
                for line in lines:
                    # البحث عن الرقم الجامعي (5 أرقام) في السطر
                    match_id = re.search(r'(\d{5})', line)
                    if match_id:
                        student_id = match_id.group(1)
                        
                        # محاولة استخراج الدرجة (نفترض أنها رقم صحيح)
                        # نبحث عن رقم في نهاية السطر أو بعد مسافة كبيرة
                        # هذا الجزء هو الأكثر صعوبة بدون معرفة التنسيق
                        
                        # مثال مبسط: نفترض أن الدرجة هي آخر رقم في السطر
                        all_numbers = re.findall(r'\d+', line)
                        if all_numbers:
                            # نفترض أن الدرجة هي آخر رقم غير الرقم الجامعي
                            grade = None
                            for num in reversed(all_numbers):
                                if num != student_id and len(num) <= 3: # الدرجة لا تزيد عن 3 خانات
                                    grade = int(num)
                                    break
                            
                            if grade is not None:
                                # استخراج الاسم: إزالة الرقم الجامعي والدرجة من السطر
                                # هذا الجزء يتطلب تنظيفاً دقيقاً
                                
                                # إزالة الرقم الجامعي والدرجة من السطر للحصول على الاسم
                                name_part = line.replace(student_id, '', 1)
                                name_part = name_part.replace(str(grade), '', 1)
                                
                                # تنظيف الاسم من الأرقام والرموز الإضافية والمسافات الزائدة
                                student_name = re.sub(r'[^ \u0600-\u06FF\u0750-\u077F\uFB50-\uFDFF\uFE70-\uFEFF]+', ' ', name_part).strip()
                                
                                # قد يكون الاسم فارغاً إذا كان التنسيق معقداً، لكن سنحاول
                                if student_name:
                                    grades_data.append({
                                        'student_id': student_id,
                                        'student_name': student_name,
                                        'grade': grade
                                    })
                                else:
                                    # إذا فشل استخراج الاسم، نسجل البيانات بدون اسم مؤقتاً
                                    grades_data.append({
                                        'student_id': student_id,
                                        'student_name': None,
                                        'grade': grade
                                    })
                                    logger.warning(f"فشل استخراج الاسم للرقم الجامعي {student_id} في السطر: {line}")
                                    
    except Exception as e:
        logger.error(f"خطأ في تحليل ملف PDF: {e}")
        return []

    return grades_data

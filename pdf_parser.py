import pdfplumber
import re
import logging

logger = logging.getLogger(__name__)

def parse_grades_pdf(pdf_path):
    """
    يحلل ملف PDF للعلامات باستخدام خاصية extract_tables.
    يفترض أن الجدول يحتوي على:
    - الرقم الجامعي (5 أرقام)
    - الاسم: العمود الثالث من اليمين
    - العلامة: العمود الثالث من اليسار
    """
    grades_data = []
    
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                # استخراج الجداول من الصفحة
                tables = page.extract_tables()
                
                for table in tables:
                    # تخطي صفوف الرأس (Headers)
                    data_rows = table[1:] 
                    
                    for row in data_rows:
                        # التأكد من أن الصف يحتوي على عدد كافٍ من الأعمدة
                        if not row or len(row) < 5: # نفترض 5 أعمدة على الأقل
                            continue
                            
                        # 1. استخراج الرقم الجامعي (5 أرقام)
                        # نفترض أن الرقم الجامعي هو أول رقم مكون من 5 خانات في الصف
                        student_id = None
                        for cell in row:
                            if cell:
                                match_id = re.search(r'(\d{5})', cell)
                                if match_id:
                                    student_id = match_id.group(1)
                                    break
                        
                        if not student_id:
                            continue

                        # 2. استخراج العلامة (العمود الثالث من اليسار)
                        # بما أن الصفوف تبدأ من اليسار، فإن العمود الثالث هو row[2]
                        grade_str = row[2]
                        grade = None
                        if grade_str:
                            try:
                                # محاولة استخراج رقم صحيح أو عشري
                                grade = float(re.search(r'\d+(\.\d+)?', grade_str).group(0))
                            except:
                                continue # تخطي إذا لم يتم العثور على علامة صالحة

                        # 3. استخراج الاسم (العمود الثالث من اليمين)
                        # إذا كان الصف يحتوي على N عمود، فإن العمود الثالث من اليمين هو row[N-3]
                        name_index = len(row) - 3
                        student_name = row[name_index]
                        
                        # تنظيف الاسم من المسافات الزائدة
                        if student_name:
                            student_name = student_name.strip()
                        
                        if student_id and grade is not None:
                            grades_data.append({
                                'student_id': student_id,
                                'student_name': student_name,
                                'grade': grade
                            })
                            
    except Exception as e:
        logger.error(f"خطأ في تحليل ملف PDF: {e}")
        return []

    return grades_data

# telegram_marks_bot/pdf_parser.py (التصحيح)
import re
import pandas as pd
import fitz  # PyMuPDF
import logging

logger = logging.getLogger(__name__)

# دالة لتحويل الأرقام العربية إلى لاتينية (تم إعادتها إلى المستوى الأعلى)
def convert_arabic_to_latin(text):
    """يحول الأرقام العربية (٠-٩) إلى أرقام لاتينية (0-9)."""
    arabic_to_latin = str.maketrans('٠١٢٣٤٥٦٧٨٩', '0123456789')
    return text.translate(arabic_to_latin)

def parse_pdf_marks(pdf_path):
    """
    يحلل ملف PDF لاستخراج الرقم الجامعي والعلامة النهائية وجميع الأعمدة.
    
    الافتراضات:
    1. الرقم الجامعي (5 أرقام) هو العمود الثاني من اليمين.
    2. العلامة النهائية هي العمود الثالث من اليسار.
    3. يتم استخراج جميع الأعمدة كنصوص.
    """
    
    marks_data = []
    
    try:
        doc = fitz.open(pdf_path)
        
        # قائمة لتخزين رؤوس الأعمدة (إذا تم العثور عليها)
        headers = []
        
        for page_num in range(doc.page_count):
            page = doc.load_page(page_num)
            text = page.get_text("text")
            
            # تقسيم النص إلى أسطر
            lines = text.split('\n')
            
            for line in lines:
                # تقسيم السطر إلى أعمدة (افتراضياً بالمسافات)
                columns = line.split()
                
                if not columns:
                    continue
                    
                # محاولة استخراج رؤوس الأعمدة من أول سطر غير فارغ
                if not headers and any(re.search(r'[أ-ي]', col) for col in columns):
                    headers = columns
                    continue
                
                # يجب أن يكون هناك ما لا يقل عن 3 أعمدة (الاسم، الرقم الجامعي، العلامة النهائية)
                if len(columns) < 3:
                    continue
                    
                try:
                    # 1. استخراج الرقم الجامعي (العمود الثاني من اليمين)
                    # يجب أن يكون 5 أرقام
                    student_id_raw = columns[-2]
                    student_id_latin = convert_arabic_to_latin(student_id_raw)
                    
                    if not re.match(r"^\d{5}$", student_id_latin):
                        continue # تجاهل إذا لم يكن 5 أرقام
                        
                    student_id = student_id_latin
                    
                    # 2. استخراج العلامة النهائية (العمود الثالث من اليسار)
                    final_mark_raw = columns[2]
                    final_mark_latin = convert_arabic_to_latin(final_mark_raw)
                    final_mark = float(final_mark_latin)
                    
                    # 3. تخزين جميع الأعمدة الأصلية (بالعربية)
                    marks_data.append({
                        'student_id': student_id,
                        'final_mark': final_mark,
                        'all_columns': columns # تخزين جميع الأعمدة الأصلية
                    })
                    
                except (ValueError, IndexError) as e:
                    # تجاهل الأسطر التي لا يمكن تحليلها كبيانات علامات
                    logger.debug(f"تجاهل السطر: {line} - خطأ: {e}")
                    continue
                    
        doc.close()
        
        if not marks_data:
            raise ValueError("لم يتم العثور على أي بيانات علامات صالحة في ملف PDF. يرجى التأكد من تنسيق الملف.")
            
        df = pd.DataFrame(marks_data)
        return df, headers
        
    except Exception as e:
        logger.error(f"خطأ عام أثناء تحليل PDF: {e}")
        raise ValueError(f"خطأ عام أثناء تحليل PDF: {e}")

# مثال للاستخدام (للتجربة فقط)
if __name__ == '__main__':
    # يجب أن يكون لديك ملف PDF تجريبي هنا
    # df, headers = parse_pdf_marks("path/to/your/marks.pdf")
    # print(df.head())
    # print(headers)
    pass

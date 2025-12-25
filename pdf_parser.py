# telegram_marks_bot/pdf_parser.py
import re
import pandas as pd
import fitz  # PyMuPDF
import logging

logger = logging.getLogger(__name__)

# دالة لتحويل الأرقام العربية إلى لاتينية
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
                # تنظيف السطر من المسافات الزائدة
                cleaned_line = line.strip()
                if not cleaned_line:
                    continue
                
                # تقسيم السطر إلى أعمدة بناءً على المسافات المتعددة
                columns = re.split(r'\s{2,}', cleaned_line)
                
                # إزالة الأعمدة الفارغة
                columns = [col.strip() for col in columns if col.strip()]
                
                if not columns:
                    continue
                
                # محاولة استخراج رؤوس الأعمدة من أول سطر غير فارغ
                if not headers and not re.search(r'\d', cleaned_line):
                    headers = columns
                    continue
                
                # محاولة استخراج البيانات
                try:
                    # 1. تحديد الرقم الجامعي (العمود الثاني من اليمين)
                    # يجب أن يكون الرقم الجامعي 5 أرقام
                    
                    # نستخدم التعبير المنتظم للبحث عن 5 أرقام متتالية (لاتينية أو عربية)
                    # ونفترض أنه العمود الثاني من اليمين
                    
                    # تحويل جميع الأعمدة إلى لاتينية مؤقتاً للتحقق من الأرقام
                    latin_columns = [convert_arabic_to_latin(col) for col in columns]
                    
                    # الرقم الجامعي هو العمود الثاني من اليمين (index -2)
                    if len(latin_columns) >= 2:
                        student_id_raw = latin_columns[-2]
                        # البحث عن 5 أرقام متتالية في العمود
                        match = re.search(r'(\d{5})', student_id_raw)
                        
                        if match:
                            student_id = match.group(1)
                        else:
                            # إذا لم نجد 5 أرقام متتالية، نتجاهل هذا السطر كبيانات طالب
                            continue
                    else:
                        continue
                        
                    # 2. تحديد العلامة النهائية (العمود الثالث من اليسار)
                    # العلامة النهائية هي العمود الثالث من اليسار (index 2)
                    if len(latin_columns) >= 3:
                        final_mark_raw = latin_columns[2]
                        # محاولة تحويل العلامة إلى رقم (قد تكون العلامة رقم عشري)
                        final_mark = float(re.sub(r'[^\d.]', '', final_mark_raw))
                    else:
                        continue
                        
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

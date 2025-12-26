# telegram_marks_bot/pdf_parser.py (باستخدام pdfplumber)
import re
import pandas as pd
import logging
import pdfplumber # المكتبة الجديدة
import json

logger = logging.getLogger(__name__)

# دالة لتحويل الأرقام العربية إلى لاتينية
def convert_arabic_to_latin(text):
    """يحول الأرقام العربية (٠-٩) إلى أرقام لاتينية (0-9)."""
    arabic_to_latin = str.maketrans('٠١٢٣٤٥٦٧٨٩', '0123456789')
    return text.translate(arabic_to_latin)

def parse_pdf_marks(pdf_path):
    """
    يحلل ملف PDF باستخدام pdfplumber لاستخراج العلامات من الجداول.
    
    الافتراضات:
    1. الرقم الجامعي (5 أرقام) هو العمود الثاني من اليمين.
    2. العلامة النهائية هي العمود الثالث من اليسار.
    """
    
    marks_data = []
    headers = []
    
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                # استخراج الجداول من الصفحة
                tables = page.extract_tables()
                
                for table in tables:
                    # افتراض أن الصف الأول هو رؤوس الأعمدة
                    if not headers and table:
                        headers = [str(h) for h in table[0] if h is not None]
                        
                    # معالجة الصفوف (بدءاً من الصف الثاني إذا كان هناك رؤوس)
                    data_rows = table[1:] if headers else table
                    
                    for row in data_rows:
                        # تصفية القيم الفارغة وتحويلها إلى سلاسل نصية
                        columns = [str(col).strip() for col in row if col is not None]
                        
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
                            
                            # 3. تخزين جميع الأعمدة الأصلية
                            marks_data.append({
                                'student_id': student_id,
                                'final_mark': final_mark,
                                'all_columns': columns # تخزين جميع الأعمدة الأصلية
                            })
                            
                        except (ValueError, IndexError) as e:
                            logger.debug(f"تجاهل السطر: {row} - خطأ: {e}")
                            continue
                            
        if not marks_data:
            raise ValueError("لم يتم العثور على أي بيانات علامات صالحة في ملف PDF. يرجى التأكد من أن الملف يحتوي على جداول واضحة.")
            
        df = pd.DataFrame(marks_data)
        return df, headers
        
    except Exception as e:
        logger.error(f"خطأ عام أثناء تحليل PDF: {e}")
        raise ValueError(f"خطأ عام أثناء تحليل PDF: {e}")

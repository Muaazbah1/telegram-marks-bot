import pdfplumber
import pandas as pd
import re
import logging

logger = logging.getLogger(__name__)

# قاموس لتحويل الأرقام العربية إلى لاتينية
ARABIC_TO_LATIN = {
    '٠': '0', '١': '1', '٢': '2', '٣': '3', '٤': '4',
    '٥': '5', '٦': '6', '٧': '7', '٨': '8', '٩': '9'
}

def convert_arabic_numbers(text):
    """تحويل الأرقام العربية في النص إلى أرقام لاتينية."""
    if isinstance(text, str):
        for arabic, latin in ARABIC_TO_LATIN.items():
            text = text.replace(arabic, latin)
    return text

def parse_pdf_marks(pdf_path):
    """
    يحلل ملف PDF باستخدام pdfplumber لاستخراج أرقام الطلاب وعلاماتهم.
    :param pdf_path: المسار إلى ملف PDF.
    :return: DataFrame يحتوي على عمودين: 'student_id' و 'mark'.
    """
    all_marks = []
    
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                # استخراج الجداول من الصفحة
                tables = page.extract_tables()
                
                for table in tables:
                    for row in table:
                        if not row or len(row) < 3:
                            continue
                        
                        # تنظيف الصف من القيم الفارغة
                        cleaned_row = [convert_arabic_numbers(str(cell).strip()) for cell in row if cell is not None and str(cell).strip() != '']
                        
                        if len(cleaned_row) < 3:
                            continue
                        
                        # الترتيب المتوقع للأعمدة:
                        # 1. الرقم الجامعي (5 أرقام) - العمود الثاني من اليمين
                        # 2. العلامة النهائية - العمود الثالث من اليسار
                        
                        # البحث عن الرقم الجامعي (5 أرقام)
                        # العمود الثاني من اليمين هو cleaned_row[-2]
                        student_id_str = cleaned_row[-2]
                        
                        # البحث عن العلامة (قد تكون رقماً صحيحاً أو عشرياً)
                        # العمود الثالث من اليسار هو cleaned_row[2]
                        mark_str = cleaned_row[2]
                        
                        # تنظيف وتحويل الرقم الجامعي
                        student_id_match = re.search(r'\b(\d{5})\b', student_id_str)
                        
                        if student_id_match:
                            student_id = student_id_match.group(1)
                            
                            # تنظيف وتحويل العلامة
                            try:
                                mark = float(mark_str)
                                all_marks.append({'student_id': student_id, 'mark': mark})
                            except ValueError:
                                # قد يكون العمود الثالث ليس علامة، تجاهل هذا الصف
                                continue
                                
    except Exception as e:
        logger.error(f"خطأ في تحليل ملف PDF: {e}")
        return pd.DataFrame()

    return pd.DataFrame(all_marks)

# لا حاجة لـ if __name__ == '__main__': هنا

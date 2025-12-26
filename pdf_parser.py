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
                tables = page.extract_tables()
                
                for table in tables:
                    # تخطي الصف الأول (رؤوس الأعمدة)
                    for row in table[1:]:
                        if not row or len(row) < 3:
                            continue
                        
                        # تنظيف الصف من القيم الفارغة وتحويل الأرقام العربية
                        cleaned_row = [convert_arabic_numbers(str(cell).strip()) for cell in row if cell is not None and str(cell).strip() != '']
                        
                        if len(cleaned_row) < 3:
                            continue
                        
                        # 1. استخراج الرقم الجامعي (العمود الثاني من اليمين)
                        if len(cleaned_row) >= 2:
                            student_id_str = cleaned_row[-2]
                            student_id_match = re.search(r'\b(\d{5})\b', student_id_str)
                        else:
                            continue
                        
                        # 2. استخراج العلامة (العمود الثالث من اليسار) - تم التأكيد على أن هذا هو الموقع الصحيح
                        if len(cleaned_row) >= 3:
                            mark_str = cleaned_row[2]
                        else:
                            continue
                        
                        
                        if student_id_match:
                            student_id = student_id_match.group(1)
                            
                            # تنظيف وتحويل العلامة
                            try:
                                mark = float(mark_str)
                                
                                # **التعديل الجديد: تصفية العلامات التي تزيد عن 100**
                                if mark <= 100:
                                    all_marks.append({'student_id': student_id, 'mark': mark})
                                else:
                                    logger.warning(f"تم تجاهل علامة غير صالحة ({mark}) للطالب {student_id}")
                                    
                            except ValueError:
                                continue
                                
    except Exception as e:
        logger.error(f"خطأ في تحليل ملف PDF: {e}")
        return pd.DataFrame()

    return pd.DataFrame(all_marks)

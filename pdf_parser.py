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
                # استخدام إعدادات pdfplumber الافتراضية لاستخراج الجداول
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
                        
                        # حسب السياق التقني:
                        # - الرقم الجامعي (5 أرقام) في العمود الثاني من اليمين
                        # - العلامة النهائية في العمود الثالث من اليسار
                        
                        # 1. استخراج الرقم الجامعي (العمود الثاني من اليمين)
                        # يجب أن يكون طول الصف على الأقل 2 ليكون هناك عمود ثاني من اليمين
                        if len(cleaned_row) >= 2:
                            student_id_str = cleaned_row[-2]
                            student_id_match = re.search(r'\b(\d{5})\b', student_id_str)
                        else:
                            continue # تخطي الصف إذا كان قصيراً جداً
                        
                        # 2. استخراج العلامة (العمود الثالث من اليسار)
                        # يجب أن يكون طول الصف على الأقل 3 ليكون هناك عمود ثالث من اليسار
                        if len(cleaned_row) >= 3:
                            mark_str = cleaned_row[2]
                        else:
                            continue # تخطي الصف إذا كان قصيراً جداً
                        
                        
                        if student_id_match:
                            student_id = student_id_match.group(1)
                            
                            # تنظيف وتحويل العلامة
                            try:
                                # محاولة تحويل العلامة إلى رقم عائم (float)
                                mark = float(mark_str)
                                all_marks.append({'student_id': student_id, 'mark': mark})
                            except ValueError:
                                # تجاهل الصف إذا لم تكن العلامة رقماً صالحاً
                                continue
                                
    except Exception as e:
        logger.error(f"خطأ في تحليل ملف PDF: {e}")
        return pd.DataFrame()

    return pd.DataFrame(all_marks)

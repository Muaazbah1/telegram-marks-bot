# pdf_parser.py (تصحيح المرونة في تحديد الأعمدة)
# ... (بقية الكود)

def parse_pdf_marks(pdf_path):
    # ... (بقية الكود)
    
    for page_num in range(doc.page_count):
        # ... (بقية الكود)
        
        for line in lines:
            # تقسيم السطر إلى أعمدة (افتراضياً بالمسافات)
            columns = line.split()
            
            if not columns or len(columns) < 3:
                continue
                
            # ... (بقية كود headers)
            
            try:
                # 1. البحث عن الرقم الجامعي (5 أرقام) في أي مكان في السطر
                student_id = None
                final_mark = None
                
                for col in columns:
                    col_latin = convert_arabic_to_latin(col)
                    
                    # البحث عن الرقم الجامعي (5 أرقام)
                    if re.match(r"^\d{5}$", col_latin):
                        student_id = col_latin
                        
                    # البحث عن العلامة النهائية (رقم يمكن تحويله إلى float)
                    try:
                        mark_value = float(col_latin)
                        # افتراض أن العلامة النهائية هي العمود الثالث من اليسار
                        if columns.index(col) == 2:
                            final_mark = mark_value
                    except ValueError:
                        continue
                
                if not student_id or final_mark is None:
                    continue # تجاهل إذا لم يتم العثور على الرقم الجامعي أو العلامة النهائية
                    
                # 3. تخزين جميع الأعمدة الأصلية (بالعربية)
                marks_data.append({
                    'student_id': student_id,
                    'final_mark': final_mark,
                    'all_columns': columns # تخزين جميع الأعمدة الأصلية
                })
                
            except Exception as e:
                logger.debug(f"تجاهل السطر: {line} - خطأ: {e}")
                continue
                
    # ... (بقية الكود)

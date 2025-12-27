# ... (الكود الكامل لـ data_processor.py الذي أرسلته سابقًا)
import pandas as pd
import numpy as np
from scipy.stats import norm
import matplotlib.pyplot as plt
from fpdf import FPDF
import logging
import io
from database import get_all_students, get_student_info_by_id, update_student_name

logger = logging.getLogger(__name__)

# إعداد الخط العربي لـ Matplotlib
plt.rcParams['font.family'] = 'DejaVu Sans'
plt.rcParams['font.sans-serif'] = ['DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False 

# ... (دالة create_normal_distribution_plot)

# ... (فئة PDF)

# ... (دالة create_admin_report_pdf)

def process_grades(grades_data, course_name="المادة"):
    """
    يعالج بيانات العلامات، ويحدث أسماء الطلاب في قاعدة البيانات،
    ويجهز البيانات لإرسالها للطلاب ولتقرير المشرف.
    """
    if not grades_data:
        logger.warning("لا توجد بيانات علامات للمعالجة.")
        return None, None

    # 1. إنشاء DataFrame (هذا هو السطر الذي يحل المشكلة)
    df = pd.DataFrame(grades_data)
    df['student_id'] = df['student_id'].astype(str)
    df['grade'] = pd.to_numeric(df['grade'], errors='coerce')
    df.dropna(subset=['grade'], inplace=True)

    # 2. تحديث أسماء الطلاب في قاعدة البيانات
    for index, row in df.iterrows():
        student_id = row['student_id']
        student_name = row['student_name']
        
        if student_name and pd.notna(student_name):
            update_student_name(student_id, student_name)

    # 3. حساب الإحصائيات
    mean_grade = df['grade'].mean()
    std_dev = df['grade'].std()
    
    # 4. حساب النسبة المئوية (Percentile)
    df['percentile'] = df['grade'].rank(pct=True) * 100
    df['percentile'] = df['percentile'].round(2)

    # 5. دمج بيانات الطلاب المسجلين
    registered_students = get_all_students()
    registered_df = pd.DataFrame(registered_students, columns=['user_id', 'student_id', 'student_name_db', 'university', 'college'])
    registered_df['student_id'] = registered_df['student_id'].astype(str)

    # دمج البيانات: نستخدم الاسم المستخرج من PDF إذا كان موجوداً، وإلا نستخدم الاسم من قاعدة البيانات
    merged_df = pd.merge(df, registered_df, on='student_id', how='left') # <--- هذا هو الدمج الصحيح
    
    # استخدام الاسم المستخرج من PDF إذا كان موجوداً، وإلا الاسم من قاعدة البيانات
    merged_df['final_name'] = merged_df['student_name'].combine_first(merged_df['student_name_db'])
    
    # 6. تجهيز بيانات تقرير المشرف (مع الترتيب والاسم)
    admin_report_df = merged_df.sort_values(by='grade', ascending=False).reset_index(drop=True)
    admin_report_df['Rank'] = admin_report_df.index + 1
    
    # اختيار الأعمدة للتقرير
    admin_report_data = admin_report_df[['Rank', 'student_id', 'final_name', 'grade', 'percentile']].rename(columns={
        'Rank': 'الترتيب',
        'student_id': 'الرقم الجامعي',
        'final_name': 'اسم الطالب',
        'grade': 'الدرجة',
        'percentile': 'النسبة المئوية'
    })

    # 7. تجهيز بيانات الطلاب الفردية
    student_results = {}
    for index, row in merged_df.iterrows():
        user_id = row['user_id']
        if pd.notna(user_id):
            student_results[int(user_id)] = {
                'grade': row['grade'],
                'percentile': row['percentile'],
                'mean': mean_grade,
                'std_dev': std_dev,
                'all_grades': df['grade'].tolist()
            }

    # 8. إنشاء تقرير المشرف PDF
    admin_pdf_buffer = create_admin_report_pdf(admin_report_data, mean_grade, std_dev, course_name)

    return student_results, admin_pdf_buffer

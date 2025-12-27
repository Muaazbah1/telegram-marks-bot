import pandas as pd
import numpy as np
from scipy.stats import norm
import matplotlib.pyplot as plt
from fpdf import FPDF
import logging
import io
import arabic_reshaper
from bidi.algorithm import get_display
from database import get_all_students, get_student_info_by_id, update_student_name

logger = logging.getLogger(__name__)

# دالة تصحيح النص العربي
    # محتوى الجدول
    pdf.set_font('Noto', '', 10) # استخدام خط Noto
    for index, row in admin_report_df.iterrows():
        # البيانات بترتيب عكسي لتناسب العرض من اليمين لليسار
        data = [
            f'{row["النسبة المئوية"]:.2f}%',
            f'{row["الدرجة"]:.2f}',
            row["اسم الطالب"] if row["اسم الطالب"] else 'غير متوفر',
            row["الرقم الجامعي"],
            str(row["الترتيب"])
        ]
        
        for i, item in enumerate(reversed(data)):
            # تم تطبيق fix_arabic على النص الذي قد يكون عربياً
            pdf.cell(col_widths[i], 6, fix_arabic(str(item)), 1, 0, 'C')
        pdf.ln()

# إعداد الخط العربي لـ Matplotlib (نحتفظ بـ DejaVu هنا لأنه يعمل بشكل جيد مع Matplotlib)
plt.rcParams['font.family'] = 'DejaVu Sans'
plt.rcParams['font.sans-serif'] = ['DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False # لدعم إشارة السالب

# ... (باقي الاستيرادات والدوال)

def create_normal_distribution_plot(grades, student_grade, mean, std_dev):
    """
    ينشئ مخطط توزيع طبيعي يظهر موقع الطالب.
    """
    fig, ax = plt.subplots(figsize=(8, 5))
    
    # رسم التوزيع الطبيعي
    x = np.linspace(min(grades) - 5, max(grades) + 5, 100)
    p = norm.pdf(x, mean, std_dev)
    ax.plot(x, p, 'k', linewidth=2)
    
    # تظليل منطقة الدرجة
    if std_dev > 0:
        fill_x = np.linspace(min(grades) - 5, student_grade, 100)
        fill_p = norm.pdf(fill_x, mean, std_dev)
        ax.fill_between(fill_x, fill_p, color='skyblue', alpha=0.5)
    
    # وضع علامة على درجة الطالب
    # تطبيق fix_arabic على التسمية
    ax.axvline(student_grade, color='red', linestyle='--', linewidth=1.5, label=fix_arabic(f'درجتك: {student_grade}'))
    
    # وضع علامة على المتوسط
    # تطبيق fix_arabic على التسمية
    ax.axvline(mean, color='green', linestyle=':', linewidth=1, label=fix_arabic(f'المتوسط: {mean:.2f}'))

    # إعداد المحاور والعناوين
    # تطبيق fix_arabic على العنوان
    ax.set_title(fix_arabic('توزيع العلامات الطبيعي'), fontsize=14)
    # تطبيق fix_arabic على تسمية المحور
    ax.set_xlabel(fix_arabic('الدرجة'), fontsize=12)
    ax.set_ylabel(fix_arabic('الكثافة'), fontsize=12)
    
    # تطبيق fix_arabic على مفتاح الرسم
    ax.legend(loc='upper left')
    ax.grid(True, linestyle='--', alpha=0.6)
    
    # حفظ المخطط في مخزن مؤقت
    buf = io.BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight')
    plt.close(fig)
    buf.seek(0)
    return buf

# ... (باقي الدوال)


class PDF(FPDF):
    """فئة مخصصة لإنشاء تقارير PDF تدعم اللغة العربية."""
    def header(self):
        # تم تطبيق fix_arabic
        self.set_font('Noto', 'B', 15)
        self.cell(0, 10, fix_arabic('تقرير إحصائيات العلامات'), 0, 1, 'C')

    def footer(self):
        self.set_y(-15)
        # تم تطبيق fix_arabic
        self.set_font('Noto', 'I', 8)
        self.cell(0, 10, fix_arabic(f'صفحة {self.page_no()}/{{nb}}'), 0, 0, 'C')

def create_admin_report_pdf(admin_report_df, mean_grade, std_dev, course_name):
    """
    ينشئ تقرير PDF شامل للمشرف يحتوي على الإحصائيات وجدول الترتيب.
    """
    pdf = PDF('P', 'mm', 'A4')
    
    # إضافة خطوط Noto Sans (المسار المحلي)
    pdf.add_font('Noto', '', 'fonts/NotoSansArabic-Regular.ttf', uni=True)
    pdf.add_font('Noto', 'B', 'fonts/NotoSansArabic-Bold.ttf', uni=True)
    pdf.add_font('Noto', 'I', 'fonts/NotoSansArabic-Regular.ttf', uni=True) # إضافة خط مائل (نستخدم العادي)
    
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.alias_nb_pages()
    pdf.add_page()
    
    # استخدام خط Noto
    pdf.set_font('Noto', '', 12)

    # الإحصائيات العامة
    # تم تطبيق fix_arabic
    pdf.cell(0, 10, fix_arabic(f'المادة: {course_name}'), 0, 1, 'R')
    pdf.cell(0, 10, fix_arabic(f'متوسط الدرجات: {mean_grade:.2f}'), 0, 1, 'R')
    pdf.cell(0, 10, fix_arabic(f'الانحراف المعياري: {std_dev:.2f}'), 0, 1, 'R')
    pdf.ln(5)

    # جدول الترتيب
    pdf.set_font('Noto', 'B', 10) # استخدام خط Noto
    col_widths = [20, 30, 60, 20, 30] # عرض الأعمدة
    
    # رؤوس الجدول (بالعربية، تحتاج إلى ترتيب عكسي)
    headers = ['النسبة المئوية', 'الدرجة', 'اسم الطالب', 'الرقم الجامعي', 'الترتيب']
    
    # رسم رؤوس الجدول
    pdf.set_fill_color(200, 220, 255)
    for i, header in enumerate(reversed(headers)):
        # تم تطبيق fix_arabic
        pdf.cell(col_widths[i], 7, fix_arabic(header), 1, 0, 'C', 1)
    pdf.ln()

    # محتوى الجدول
    pdf.set_font('Noto', '', 10) # استخدام خط Noto
    for index, row in admin_report_df.iterrows():
        # البيانات بترتيب عكسي لتناسب العرض من اليمين لليسار
        data = [
            f'{row["النسبة المئوية"]:.2f}%',
            f'{row["الدرجة"]:.2f}',
            row["اسم الطالب"] if row["اسم الطالب"] else 'غير متوفر',
            row["الرقم الجامعي"],
            str(row["الترتيب"])
        ]
        
        for i, item in enumerate(reversed(data)):
            # تم تطبيق fix_arabic على النص الذي قد يكون عربياً
            pdf.cell(col_widths[i], 6, fix_arabic(str(item)), 1, 0, 'C')
        pdf.ln()

    # حفظ التقرير في مخزن مؤقت (تم تصحيح مشكلة bytearray)
    pdf_output = pdf.output(dest='S')
    if isinstance(pdf_output, str):
        pdf_buffer = io.BytesIO(pdf_output.encode('latin1'))
    else:
        pdf_buffer = io.BytesIO(pdf_output)
        
    pdf_buffer.seek(0)
    return pdf_buffer

def process_grades(grades_data, course_name="المادة"):
    """
    يعالج بيانات العلامات، ويحدث أسماء الطلاب في قاعدة البيانات،
    ويجهز البيانات لإرسالها للطلاب ولتقرير المشرف.
    """
    if not grades_data:
        logger.warning("لا توجد بيانات علامات للمعالجة.")
        return None, None

    # 1. إنشاء DataFrame
    df = pd.DataFrame(grades_data)
    df['student_id'] = df['student_id'].astype(str)
    df['grade'] = pd.to_numeric(df['grade'], errors='coerce')
    df.dropna(subset=['grade'], inplace=True)

    # 2. تحديث أسماء الطلاب في قاعدة البيانات
    for index, row in df.iterrows():
        student_id = row['student_id']
        student_name = row['student_name']
        
        if student_name and pd.notna(student_name):
            # تحديث الاسم في قاعدة البيانات
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
    merged_df = pd.merge(df, registered_df, on='student_id', how='left')
    
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

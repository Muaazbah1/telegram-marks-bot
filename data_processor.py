# telegram_marks_bot/data_processor.py
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import norm
from tabulate import tabulate
from fpdf import FPDF
import os

# دالة لرسم التوزيع الطبيعي
def plot_normal_distribution(marks, student_mark, output_path):
    """
    يرسم التوزيع الطبيعي للعلامات ويحدد موقع علامة الطالب.
    
    التعديلات:
    - التسميات بالإنجليزية.
    - المحور X من 0 إلى 100.
    - المحور Y يمثل عدد الطلاب (التكرار).
    """
    
    # حساب المتوسط والانحراف المعياري
    mu = marks.mean()
    sigma = marks.std()
    
    # إعداد الرسم البياني
    plt.figure(figsize=(10, 6))
    
    # رسم المدرج التكراري (Histogram)
    # bins: عدد الفئات، density=False لتمثيل عدد الطلاب (التكرار) على المحور Y
    plt.hist(marks, bins=20, range=(0, 100), density=False, alpha=0.6, color='g', label='Marks Distribution')
    
    # رسم منحنى التوزيع الطبيعي (Normal Distribution Curve)
    # إنشاء نقاط للمنحنى من 0 إلى 100
    xmin, xmax = 0, 100
    x = np.linspace(xmin, xmax, 100)
    
    # حساب مقياس المنحنى ليناسب المدرج التكراري (Normalization)
    # scale_factor = (عدد الطلاب * عرض الفئة)
    bin_width = (xmax - xmin) / 20
    scale_factor = len(marks) * bin_width
    
    p = norm.pdf(x, mu, sigma) * scale_factor
    
    plt.plot(x, p, 'k', linewidth=2, label=f'Normal Distribution ($\mu$={mu:.2f}, $\sigma$={sigma:.2f})')
    
    # تحديد موقع علامة الطالب
    plt.axvline(student_mark, color='r', linestyle='--', linewidth=2, label=f'Your Mark ({student_mark:.2f})')
    
    # إعداد المحاور والتسميات بالإنجليزية
    plt.title('Marks Distribution and Your Position', fontsize=16)
    plt.xlabel('Final Mark (0-100)', fontsize=14)
    plt.ylabel('Number of Students (Frequency)', fontsize=14)
    
    # تحديد مدى المحور X من 0 إلى 100
    plt.xlim(0, 100)
    
    plt.legend()
    plt.grid(True, linestyle='--', alpha=0.7)
    
    # حفظ الصورة
    plt.savefig(output_path)
    plt.close()
    
    return output_path

# دالة لحساب الإحصائيات
def calculate_statistics(df):
    """
    يحسب الإحصائيات الأساسية والـ percentile لكل طالب.
    """
    marks = df['final_mark']
    
    # الإحصائيات الأساسية
    stats = {
        "Mean": marks.mean(),
        "Median": marks.median(),
        "Standard Deviation (SD)": marks.std(),
        "Min Mark": marks.min(),
        "Max Mark": marks.max(),
        "Total Students": len(marks)
    }
    
    # حساب الـ percentile لكل طالب
    # percentile = (عدد الطلاب الذين حصلوا على علامة أقل من علامة الطالب / إجمالي عدد الطلاب) * 100
    df['percentile'] = df['final_mark'].rank(pct=True) * 100
    
    return stats, df

# دالة لإنشاء تقرير إحصائي كملف PDF
def create_statistics_report_pdf(stats, df_with_percentile, image_path, output_path):
    """
    ينشئ تقرير إحصائي شامل بصيغة PDF.
    """
    
    # تعريف فئة PDF مخصصة
    class PDF(FPDF):
        def header(self):
            self.set_font("Arial", "B", 16)
            self.cell(0, 10, "Statistical Analysis Report", 0, 1, "C")
            self.ln(5)

        def footer(self):
            self.set_y(-15)
            self.set_font("Arial", "I", 8)
            self.cell(0, 10, f"Page {self.page_no()}/{{nb}}", 0, 0, "C")

    pdf = PDF()
    pdf.alias_nb_pages()
    pdf.add_page()
    
    pdf.set_font("Arial", "", 12)
    pdf.cell(0, 10, f"Total Students: {stats['Total Students']}", 0, 1)
    
    # جدول الإحصائيات الأساسية
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 10, "Summary Statistics:", 0, 1)
    
    # تحويل الإحصائيات إلى جدول tabulate
    stats_table = [
        ["Metric", "Value"],
        ["Mean", f"{stats['Mean']:.2f}"],
        ["Median", f"{stats['Median']:.2f}"],
        ["Standard Deviation (SD)", f"{stats['Standard Deviation (SD)']:.2f}"],
        ["Min Mark", f"{stats['Min Mark']:.2f}"],
        ["Max Mark", f"{stats['Max Mark']:.2f}"]
    ]
    
    # استخدام tabulate لإنشاء نص الجدول
    table_text = tabulate(stats_table, headers="firstrow", tablefmt="fancy_grid")
    
    # إضافة الجدول كنص إلى PDF
    pdf.set_font("Courier", "", 10) # استخدام خط أحادي المسافة للجدول
    for line in table_text.split('\n'):
        pdf.cell(0, 5, line, 0, 1)
        
    pdf.ln(5)
    
    # إضافة الرسم البياني
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 10, "Marks Distribution Plot:", 0, 1)
    pdf.image(image_path, x=10, y=pdf.get_y(), w=180)
    pdf.ln(110) # ترك مسافة بعد الصورة
    
    # إضافة جدول ترتيب الطلاب (أفضل 10)
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 10, "Top 10 Students by Mark:", 0, 1)
    
    # فرز الطلاب
    top_students = df_with_percentile.sort_values(by='final_mark', ascending=False).head(10)
    
    # إعداد بيانات الجدول
    table_data = []
    for index, row in top_students.iterrows():
        # نفترض أن العمود الأول في all_columns هو اسم الطالب
        # بما أننا لا نعرف ترتيب الأعمدة، سنستخدم الرقم الجامعي والعلامة والـ percentile
        student_name = row['all_columns'][1] if len(row['all_columns']) > 1 else "N/A"
        table_data.append([
            row['student_id'],
            student_name,
            f"{row['final_mark']:.2f}",
            f"{row['percentile']:.2f}%"
        ])
        
    # إضافة الجدول كنص إلى PDF
    pdf.set_font("Courier", "", 10)
    table_text = tabulate(table_data, headers=["Student ID", "Name", "Mark", "Percentile"], tablefmt="fancy_grid")
    for line in table_text.split('\n'):
        pdf.cell(0, 5, line, 0, 1)
        
    pdf.output(output_path, "F")
    return output_path

# الدالة الرئيسية للمعالجة
def process_marks_data(df, output_dir):
    """
    تنفذ جميع خطوات المعالجة: حساب الإحصائيات، رسم التوزيع، وإنشاء التقرير.
    """
    
    # 1. حساب الإحصائيات والـ percentile
    stats, df_with_percentile = calculate_statistics(df)
    
    # 2. رسم التوزيع الطبيعي
    image_path = os.path.join(output_dir, "normal_distribution.png")
    # نستخدم المتوسط كعلامة افتراضية للرسم العام
    plot_normal_distribution(df['final_mark'], df['final_mark'].mean(), image_path) 
    
    # 3. إنشاء تقرير PDF
    pdf_path = os.path.join(output_dir, "statistical_report.pdf")
    create_statistics_report_pdf(stats, df_with_percentile, image_path, pdf_path)
    
    # 4. تحويل DataFrame إلى قائمة من الصفوف لتخزينها في قاعدة البيانات
    # (student_id, final_mark, percentile, all_columns)
    db_data = df_with_percentile[['student_id', 'final_mark', 'percentile', 'all_columns']].values.tolist()
    
    return db_data, stats, image_path, pdf_path

# telegram_marks_bot/data_processor.py
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import norm
from tabulate import tabulate
from fpdf import FPDF # مكتبة لإنشاء ملفات PDF
import os
import logging

logger = logging.getLogger(__name__)

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
    # np.histogram لحساب التكرارات وتحديد الـ bins
    hist, bins = np.histogram(marks, bins=20, range=(0, 100))
    
    # رسم المدرج التكراري
    plt.hist(marks, bins=bins, density=False, alpha=0.6, color='g', label='Marks Distribution')
    
    # رسم منحنى التوزيع الطبيعي (Normal Distribution Curve)
    # نحتاج إلى تحويل منحنى الكثافة إلى منحنى تكرار
    xmin, xmax = plt.xlim()
    x = np.linspace(xmin, xmax, 100)
    
    # حساب منحنى الكثافة (PDF)
    p = norm.pdf(x, mu, sigma)
    
    # تحويل منحنى الكثافة إلى منحنى تكرار (للتطابق مع المحور Y)
    # عامل التحويل هو (مجموع التكرارات * عرض الفئة)
    scale_factor = len(marks) * (bins[1] - bins[0])
    
    plt.plot(x, p * scale_factor, 'k', linewidth=2, label='Normal Distribution')
    
    # تحديد موقع علامة الطالب
    plt.axvline(student_mark, color='r', linestyle='dashed', linewidth=2, label=f'Your Mark: {student_mark:.2f}')
    
    # إعداد المحاور والتسميات
    plt.title("Marks Distribution Analysis", fontsize=16)
    plt.xlabel("Final Mark (0-100)", fontsize=14)
    plt.ylabel("Number of Students (Frequency)", fontsize=14)
    plt.xlim(0, 100) # تحديد المحور X من 0 إلى 100
    plt.legend()
    plt.grid(True, linestyle='--', alpha=0.7)
    
    # حفظ الرسم البياني
    plt.savefig(output_path)
    plt.close()

def calculate_statistics(df):
    """يحسب الإحصائيات الأساسية والـ percentile لكل طالب."""
    
    marks = df['final_mark']
    
    # الإحصائيات الأساسية
    stats = {
        "Total Students": len(marks),
        "Mean": marks.mean(),
        "Median": marks.median(),
        "Standard Deviation (SD)": marks.std(),
        "Min Mark": marks.min(),
        "Max Mark": marks.max(),
    }
    
    # حساب الـ percentile لكل طالب
    # percentile = (عدد الطلاب الذين حصلوا على علامة أقل) / (العدد الكلي للطلاب) * 100
    df['percentile'] = marks.rank(pct=True) * 100
    
    return stats, df

def create_statistics_report_pdf(stats, df_with_percentile, image_path, output_path):
    """ينشئ تقرير إحصائي بصيغة PDF."""
    
    pdf = FPDF()
    pdf.add_page()
    
    # إعداد الخط (يجب أن يدعم اللغة العربية)
    # بما أننا نستخدم fpdf2، يجب إضافة خط يدعم العربية
    # لتجنب مشاكل الخطوط في البيئة المعزولة، سنستخدم الخطوط الافتراضية للغة الإنجليزية
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, "Statistical Marks Report", 0, 1, 'C')
    
    # قسم الإحصائيات
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 10, "1. Summary Statistics:", 0, 1)
    
    pdf.set_font("Arial", "", 10)
    for key, value in stats.items():
        pdf.cell(0, 5, f"{key}: {value:.2f}", 0, 1)
        
    # قسم الرسم البياني
    pdf.cell(0, 10, "", 0, 1) # سطر فارغ
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 10, "2. Normal Distribution Plot:", 0, 1)
    
    # إضافة الصورة
    pdf.image(image_path, x=10, y=pdf.get_y(), w=180)
    pdf.set_y(pdf.get_y() + 100) # تحريك المؤشر بعد الصورة
    
    # قسم ترتيب الطلاب
    pdf.cell(0, 10, "", 0, 1) # سطر فارغ
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 10, "3. Student Ranking (Top 10):", 0, 1)
    
    # ترتيب الطلاب
    df_sorted = df_with_percentile.sort_values(by='final_mark', ascending=False).head(10)
    
    # تحويل البيانات إلى جدول نصي باستخدام tabulate
    table_data = []
    for index, row in df_sorted.iterrows():
        # يجب أن تكون الأعمدة المستخرجة هي القائمة المخزنة في all_columns
        # سنستخدم أول عمودين فقط (افتراضياً الاسم والرقم الجامعي)
        name = row['all_columns'][0] if len(row['all_columns']) > 0 else "N/A"
        student_id = row['student_id']
        mark = f"{row['final_mark']:.2f}"
        percentile = f"{row['percentile']:.2f}%"
        table_data.append([name, student_id, mark, percentile])
        
    # إنشاء جدول tabulate
    headers = ["Name (First Col)", "Student ID", "Mark", "Percentile"]
    table_text = tabulate(table_data, headers=headers, tablefmt="fancy_grid")
    
    # إضافة الجدول إلى PDF (كـ نص عادي بسبب قيود الخطوط)
    pdf.set_font("Courier", "", 8) # استخدام خط أحادي المسافة لـ tabulate
    for line in table_text.split('\n'):
        pdf.cell(0, 4, line, 0, 1)
        
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
    # all_columns يتم تحويلها إلى قائمة Python قبل التخزين
    db_data = []
    for index, row in df_with_percentile.iterrows():
        db_data.append((
            row['student_id'], 
            row['final_mark'], 
            row['percentile'], 
            row['all_columns'].tolist() if isinstance(row['all_columns'], np.ndarray) else row['all_columns']
        ))
    
    return db_data, stats, image_path, pdf_path

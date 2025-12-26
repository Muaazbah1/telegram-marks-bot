import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os
from scipy.stats import norm
from tabulate import tabulate
from fpdf import FPDF # مكتبة fpdf2 تستخدم FPDF كاسم للكلاس
import logging

logger = logging.getLogger(__name__)

# إعدادات الخطوط بالإنجليزية
plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['font.sans-serif'] = ['DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

# إعدادات الخطوط العربية لـ FPDF
# يجب أن يكون هذا الخط متوفراً في بيئة التشغيل (Hugging Face)
# سنستخدم خطاً افتراضياً، ولكن قد تحتاج إلى تثبيت خط عربي في Dockerfile
ARABIC_FONT_PATH = "DejaVuSans.ttf" # افتراضياً، سنستخدم خطاً موجوداً

class PDFReport(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 15)
        self.cell(0, 10, 'Marks Distribution Report', 0, 1, 'C')

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')

def process_marks(marks_df):
    """
    Calculates basic statistics for the marks dataset.
    :param marks_df: DataFrame with a 'mark' column.
    :return: Dictionary with statistics.
    """
    marks = marks_df['mark']
    stats = {
        'count': len(marks),
        'mean': marks.mean(),
        'std_dev': marks.std(),
        'min': marks.min(),
        'max': marks.max()
    }
    return stats

def generate_normal_distribution_plot(marks, student_mark, output_path):
    """
    Generates a Histogram plot showing the distribution of marks and the student's position.
    Y-axis is the count of students (Frequency).
    X-axis is capped at 100.
    :param marks: Series of marks.
    :param student_mark: The student's mark to highlight.
    :param output_path: Path to save the image file.
    """
    
    # إعدادات الخطوط بالإنجليزية
    plt.rcParams['font.family'] = 'sans-serif'
    plt.rcParams['font.sans-serif'] = ['DejaVu Sans']
    plt.rcParams['axes.unicode_minus'] = False

    # إنشاء الرسم البياني
    plt.figure(figsize=(8, 5)) # تقليل حجم الصورة
    
    # عمود لكل علامة (bins=101)
    n, bins, patches = plt.hist(marks, bins=101, range=(0, 101), edgecolor='black', alpha=0.7, color='skyblue')

    # تحديد موقع الطالب
    # نجد الفئة التي تقع فيها علامة الطالب
    for patch, bin_start, bin_end in zip(patches, bins[:-1], bins[1:]):
        if bin_start <= student_mark < bin_end:
            patch.set_facecolor('red') # تلوين فئة الطالب باللون الأحمر
            break
    
    # إضافة خط عمودي عند علامة الطالب
    if student_mark != -1: # لا ترسم الخط إذا كان الرسم البياني عاماً
        plt.axvline(student_mark, color='red', linestyle='--', linewidth=2, label=f'Your Mark: {student_mark}')

    # إضافة تسميات وعنوان بالإنجليزية
    plt.title('Marks Distribution Histogram', fontsize=16, fontweight='bold')
    plt.xlabel('Mark', fontsize=14)
    plt.ylabel('Number of Students (Frequency)', fontsize=14)
    plt.xticks(np.arange(0, 101, 10)) # تحديد علامات المحور السيني كل 10
    plt.legend(loc='upper left', fontsize=12)
    plt.grid(axis='y', linestyle='--', alpha=0.6)

    # حفظ الرسم البياني - تم تقليل DPI إلى 75
    plt.savefig(output_path, dpi=75)
    plt.close()

def generate_text_report(marks_df, stats):
    """
    ينشئ تقرير نصي منسق (Markdown) يحتوي على جدول الترتيب والإحصائيات.
    """
    # 1. الإحصائيات
    stats_report = (
        f"**1. Summary Statistics**\n"
        f"| Metric | Value |\n"
        f"| :--- | :--- |\n"
        f"| Total Students | {stats['count']} |\n"
        f"| Mean | {stats['mean']:.2f} |\n"
        f"| Standard Deviation | {stats['std_dev']:.2f} |\n"
        f"| Minimum Mark | {stats['min']} |\n"
        f"| Maximum Mark | {stats['max']} |\n\n"
    )

    # 2. جدول الترتيب
    # حساب الترتيب
    ranked_df = marks_df.sort_values(by='mark', ascending=False).reset_index(drop=True)
    ranked_df['Rank'] = ranked_df.index + 1
    
    # إعادة ترتيب الأعمدة
    ranked_df = ranked_df[['Rank', 'student_id', 'mark']]
    
    # توليد جدول Markdown باستخدام tabulate
    ranking_table = tabulate(ranked_df, headers='keys', tablefmt='pipe', showindex=False)
    
    ranking_report = (
        f"**2. Student Ranking Table (Highest to Lowest)**\n"
        f"{ranking_table}\n"
    )
    
    return stats_report + ranking_report

def generate_full_report_pdf(marks_df, stats, plot_path, output_path):
    """
    ينشئ تقرير PDF شامل يحتوي على الإحصائيات وجدول الترتيب والرسم البياني.
    """
    pdf = PDFReport('P', 'mm', 'A4')
    pdf.add_page()
    
    # 1. الإحصائيات
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 10, '1. Summary Statistics', 0, 1, 'L')
    
    # تحويل الإحصائيات إلى جدول FPDF
    stats_data = [
        ['Metric', 'Value'],
        ['Total Students', str(stats['count'])],
        ['Mean', f"{stats['mean']:.2f}"],
        ['Standard Deviation', f"{stats['std_dev']:.2f}"],
        ['Minimum Mark', str(stats['min'])],
        ['Maximum Mark', str(stats['max'])]
    ]
    
    pdf.set_font('Arial', '', 10)
    col_width = pdf.w / 3.0
    row_height = 8
    
    for row in stats_data:
        pdf.cell(col_width, row_height, row[0], 1, 0, 'L')
        pdf.cell(col_width, row_height, row[1], 1, 1, 'L')
    
    pdf.ln(10)
    
    # 2. جدول الترتيب
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 10, '2. Student Ranking Table (Highest to Lowest)', 0, 1, 'L')
    
    # حساب الترتيب
    ranked_df = marks_df.sort_values(by='mark', ascending=False).reset_index(drop=True)
    ranked_df['Rank'] = ranked_df.index + 1
    
    # إعادة ترتيب الأعمدة
    ranked_df = ranked_df[['Rank', 'student_id', 'mark']]
    
    # تحويل DataFrame إلى قائمة صفوف
    ranking_data = [ranked_df.columns.tolist()] + ranked_df.values.tolist()
    
    pdf.set_font('Arial', '', 10)
    col_width = pdf.w / 4.0
    
    for row in ranking_data:
        pdf.cell(col_width, row_height, str(row[0]), 1, 0, 'C')
        pdf.cell(col_width, row_height, str(row[1]), 1, 0, 'C')
        pdf.cell(col_width, row_height, str(row[2]), 1, 1, 'C')
        
    pdf.ln(10)
    
    # 3. الرسم البياني
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 10, '3. Marks Distribution Histogram', 0, 1, 'L')
    
    # إضافة الصورة
    pdf.image(plot_path, x=10, w=180)
    
    pdf.output(output_path, 'F')

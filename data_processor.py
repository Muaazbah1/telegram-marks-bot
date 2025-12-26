import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os
from scipy.stats import norm
from fpdf import FPDF # مكتبة fpdf2 تستخدم FPDF كاسم للكلاس

# إعدادات الخطوط بالإنجليزية
plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['font.sans-serif'] = ['DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

# إعدادات الخطوط العربية لـ FPDF
# يجب أن يكون هذا الخط متوفراً في بيئة التشغيل (Koyeb)
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

    def chapter_title(self, title):
        self.set_font('Arial', 'B', 12)
        self.cell(0, 10, title, 0, 1, 'L')
        self.ln(2)

    def chapter_body(self, body):
        self.set_font('Arial', '', 10)
        self.multi_cell(0, 5, body)
        self.ln()

    def print_table(self, df):
        # إضافة الخط العربي لدعم الجدول
        try:
            self.add_font('Arabic', '', ARABIC_FONT_PATH, uni=True)
            self.set_font('Arabic', '', 10)
        except:
            self.set_font('Arial', '', 10) # الرجوع إلى Arial إذا فشل الخط العربي

        # عرض الأعمدة
        col_width = self.w / (len(df.columns) + 1)
        row_height = 7
        
        # رؤوس الأعمدة
        self.set_fill_color(200, 220, 255)
        for col in df.columns:
            self.cell(col_width, row_height, str(col), 1, 0, 'C', 1)
        self.ln()

        # صفوف البيانات
        self.set_font('Arial', '', 10)
        for index, row in df.iterrows():
            for item in row:
                self.cell(col_width, row_height, str(item), 1, 0, 'C')
            self.ln()
        self.ln()


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
    plt.figure(figsize=(10, 6))
    
    # **التعديل الجديد: عمود لكل علامة (bins=101)**
    # bins: 101 لضمان فئة لكل علامة من 0 إلى 100
    n, bins, patches = plt.hist(marks, bins=101, range=(0, 101), edgecolor='black', alpha=0.7, color='skyblue')

    # تحديد موقع الطالب
    # نجد الفئة التي تقع فيها علامة الطالب
    for patch, bin_start, bin_end in zip(patches, bins[:-1], bins[1:]):
        if bin_start <= student_mark < bin_end:
            patch.set_facecolor('red') # تلوين فئة الطالب باللون الأحمر
            break
    
    # إضافة خط عمودي عند علامة الطالب
    plt.axvline(student_mark, color='red', linestyle='--', linewidth=2, label=f'Your Mark: {student_mark}')

    # إضافة تسميات وعنوان بالإنجليزية
    plt.title('Marks Distribution Histogram', fontsize=16, fontweight='bold')
    plt.xlabel('Mark', fontsize=14)
    plt.ylabel('Number of Students (Frequency)', fontsize=14)
    plt.xticks(np.arange(0, 101, 10)) # تحديد علامات المحور السيني كل 10
    plt.legend(loc='upper left', fontsize=12)
    plt.grid(axis='y', linestyle='--', alpha=0.6)

    # حفظ الرسم البياني
    plt.savefig(output_path)
    plt.close()

def generate_full_report_pdf(marks_df, stats, plot_path, output_pdf_path):
    """
    ينشئ تقرير PDF شامل يحتوي على جدول الترتيب والإحصائيات والرسم البياني.
    """
    pdf = PDFReport('P', 'mm', 'A4')
    pdf.add_page()

    # 1. الإحصائيات
    stats_text = (
        f"Statistics:\n"
        f"Total Students: {stats['count']}\n"
        f"Mean: {stats['mean']:.2f}\n"
        f"Standard Deviation: {stats['std_dev']:.2f}\n"
        f"Minimum Mark: {stats['min']}\n"
        f"Maximum Mark: {stats['max']}"
    )
    pdf.chapter_title("1. Summary Statistics")
    pdf.chapter_body(stats_text)

    # 2. جدول الترتيب
    # حساب الترتيب
    ranked_df = marks_df.sort_values(by='mark', ascending=False).reset_index(drop=True)
    ranked_df['Rank'] = ranked_df.index + 1
    
    # إعادة ترتيب الأعمدة
    ranked_df = ranked_df[['Rank', 'student_id', 'mark']]
    
    pdf.chapter_title("2. Student Ranking Table (Highest to Lowest)")
    pdf.print_table(ranked_df)

    # 3. الرسم البياني
    pdf.chapter_title("3. Marks Distribution Histogram")
    pdf.image(plot_path, x=10, w=180)

    pdf.output(output_pdf_path, 'F')
    return output_pdf_path

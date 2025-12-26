import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os
from scipy.stats import norm
from tabulate import tabulate # إضافة tabulate

# إعدادات الخطوط بالإنجليزية
plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['font.sans-serif'] = ['DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

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

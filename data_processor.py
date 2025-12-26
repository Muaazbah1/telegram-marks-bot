import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os
from scipy.stats import norm # تم الاحتفاظ بها في حال الحاجة

# تم تغيير الخطوط إلى الإنجليزية لتجنب مشكلة التقطيع
# إذا كنت تريد المحاولة مرة أخرى باللغة العربية، يجب تثبيت خط عربي في Dockerfile
# ولكن لتجنب التعقيد، سنستخدم الإنجليزية الآن كما طلبت
# سنستخدم الإنجليزية في التسميات لتجنب مشكلة التقطيع
# يجب تعديل bot.py أيضاً لتغيير تسميات الصورة إلى الإنجليزية

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
    
    # **التعديل الجديد: استخدام مدرج تكراري (Histogram)**
    # bins: عدد الفئات، range: تحديد النطاق من 0 إلى 100
    n, bins, patches = plt.hist(marks, bins=20, range=(0, 100), edgecolor='black', alpha=0.7, color='skyblue')

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

import pandas as pd
import numpy as np
from scipy.stats import norm
import matplotlib.pyplot as plt
import os
# تم إزالة استيراد NORMAL_DISTRIBUTION_IMAGE من config.py
# لأن المسار يتم تمريره مباشرة إلى الدالة في bot.py

def process_marks(marks_df):
    """
    يحسب الإحصائيات الأساسية لمجموعة العلامات.
    :param marks_df: DataFrame يحتوي على عمود 'mark'.
    :return: قاموس بالإحصائيات.
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
    ينشئ رسم بياني للتوزيع الطبيعي مع تحديد موقع الطالب.
    :param marks: سلسلة (Series) من العلامات.
    :param student_mark: علامة الطالب المراد تحديدها.
    :param output_path: المسار لحفظ ملف الصورة.
    """
    # حساب المتوسط والانحراف المعياري
    mu = marks.mean()
    sigma = marks.std()

    # إنشاء نطاق قيم لمحور السينات
    x = np.linspace(marks.min() - 5, marks.max() + 5, 100)

    # حساب دالة كثافة الاحتمال (PDF) للتوزيع الطبيعي
    pdf = norm.pdf(x, mu, sigma)

    # إنشاء الرسم البياني
    plt.figure(figsize=(10, 6))
    plt.plot(x, pdf, 'k', linewidth=2)

    # تظليل المنطقة تحت المنحنى
    plt.fill_between(x, pdf, color='skyblue', alpha=0.5)

    # تحديد موقع الطالب
    student_pdf = norm.pdf(student_mark, mu, sigma)
    plt.plot(student_mark, student_pdf, 'ro', markersize=10, label=f'علامتك: {student_mark}')
    plt.axvline(student_mark, color='r', linestyle='--', linewidth=1)

    # إضافة تسميات وعنوان
    plt.title('توزيع العلامات الطبيعي', fontsize=16, fontweight='bold')
    plt.xlabel('العلامة', fontsize=14)
    plt.ylabel('الكثافة الاحتمالية', fontsize=14)
    plt.legend(loc='upper left', fontsize=12)
    plt.grid(True, linestyle='--', alpha=0.6)

    # حفظ الرسم البياني
    plt.savefig(output_path)
    plt.close()

# لا حاجة لـ if __name__ == '__main__': هنا

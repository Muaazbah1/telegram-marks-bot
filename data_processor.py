# data_processor.py
import pandas as pd
import numpy as np
from scipy.stats import norm
import matplotlib.pyplot as plt
from config import NORMAL_DISTRIBUTION_IMAGE, STATISTICS_OUTPUT_FILE

# لضمان دعم اللغة العربية في الرسوم البيانية
plt.rcParams['font.family'] = 'DejaVu Sans'
plt.rcParams['font.sans-serif'] = ['DejaVu Sans']

def calculate_statistics(marks_df):
    """
    يحسب الإحصائيات الوصفية للعلامات.
    marks_df: DataFrame يحتوي على عمود 'mark'.
    """
    marks = marks_df['mark']
    stats = {
        "العدد الكلي للطلاب": len(marks),
        "المتوسط الحسابي (Mean)": marks.mean(),
        "الانحراف المعياري (SD)": marks.std(),
        "الوسيط (Median)": marks.median(),
        "أعلى علامة (Max)": marks.max(),
        "أدنى علامة (Min)": marks.min(),
        "التباين (Variance)": marks.var(),
        "الالتواء (Skewness)": marks.skew(),
        "التفرطح (Kurtosis)": marks.kurt()
    }
    return stats

def calculate_percentiles(marks_df):
    """
    يحسب الـ percentile لكل علامة.
    """
    marks = marks_df['mark'].sort_values(ascending=True)
    n = len(marks)
    
    # حساب الـ percentile: (الرتبة / العدد الكلي)
    # نستخدم method='min' لضمان أن العلامة الأقل تأخذ أقل percentile
    percentiles = (marks.rank(method='min') / n)
    
    marks_df['percentile'] = percentiles
    return marks_df

def generate_normal_distribution_plot(marks_df, student_mark=None, student_id=None, output_path=NORMAL_DISTRIBUTION_IMAGE):
    """
    يرسم التوزيع الطبيعي للعلامات ويحدد موقع علامة الطالب عليه.
    """
    marks = marks_df['mark']
    mu, std = marks.mean(), marks.std()
    
    plt.figure(figsize=(10, 6))
    
    # رسم المدرج التكراري (Histogram) للعلامات
    plt.hist(marks, bins=15, density=True, alpha=0.6, color='g', label='توزيع العلامات الفعلي')
    
    # رسم منحنى التوزيع الطبيعي (Normal Distribution Curve)
    xmin, xmax = plt.xlim()
    x = np.linspace(xmin, xmax, 100)
    p = norm.pdf(x, mu, std)
    plt.plot(x, p, 'k', linewidth=2, label='منحنى التوزيع الطبيعي')
    
    title = "توزيع العلامات الطبيعي"
    
    # تحديد موقع علامة الطالب
    if student_mark is not None:
        # رسم خط عمودي عند علامة الطالب
        plt.axvline(student_mark, color='r', linestyle='--', linewidth=2, label=f'علامتك: {student_mark:.2f}')
        
        # إضافة نص يوضح موقع الطالب
        if student_id:
            title = f"توزيع العلامات الطبيعي - موقع الطالب {student_id}"
        
        # تظليل المنطقة التي تسبق علامة الطالب (الـ percentile)
        percentile_area = np.linspace(xmin, student_mark, 100)
        # نحتاج إلى حساب الـ PDF على المنطقة المظللة
        pdf_area = norm.pdf(percentile_area, mu, std)
        plt.fill_between(percentile_area, pdf_area, color='red', alpha=0.3)

    plt.title(title, fontsize=16)
    plt.xlabel("العلامة", fontsize=14)
    plt.ylabel("الكثافة الاحتمالية", fontsize=14)
    plt.legend(loc='upper right')
    plt.grid(True, linestyle='--', alpha=0.7)
    
    # حفظ الصورة
    plt.savefig(output_path)
    plt.close()
    
    return output_path

def create_report_markdown(stats, marks_df):
    """
    ينشئ تقرير Markdown يحتوي على الإحصائيات وترتيب الطلاب.
    """
    report = "# تقرير تحليل علامات الطلاب\n\n"
    report += "## الإحصائيات الوصفية للعلامات\n"
    report += "| الإحصائية | القيمة |\n"
    report += "| :--- | :--- |\n"
    for key, value in stats.items():
        report += f"| {key} | {value:.2f} |\n"
    report += "\n"
    
    report += "## ترتيب الطلاب حسب العلامة\n"
    # ترتيب الطلاب تنازلياً حسب العلامة
    ranked_df = marks_df.sort_values(by='mark', ascending=False).reset_index(drop=True)
    ranked_df.index = ranked_df.index + 1 # بدء الترتيب من 1
    
    # إضافة عمود الترتيب
    ranked_df.insert(0, 'الترتيب', ranked_df.index)
    
    report += ranked_df[['الترتيب', 'student_id', 'mark', 'percentile']].to_markdown(index=False, floatfmt=".2f")
    
    # حفظ التقرير
    with open(STATISTICS_OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write(report)
        
    return STATISTICS_OUTPUT_FILE

def process_marks_data(marks_data):
    """
    الدالة الرئيسية لمعالجة العلامات.
    marks_data: قائمة من القوائم/الصفوف: [(student_id, mark), ...]
    """
    # تحويل البيانات إلى DataFrame
    marks_df = pd.DataFrame(marks_data, columns=['student_id', 'mark'])
    
    # حساب الـ percentiles
    marks_df = calculate_percentiles(marks_df)
    
    # حساب الإحصائيات
    stats = calculate_statistics(marks_df)
    
    # توليد تقرير Markdown
    report_path = create_report_markdown(stats, marks_df)
    
    # توليد رسم التوزيع الطبيعي العام
    general_plot_path = generate_normal_distribution_plot(marks_df)
    
    # تحويل DataFrame إلى قائمة من الصفوف لتخزينها في قاعدة البيانات
    # (student_id, mark, percentile)
    db_data = marks_df[['student_id', 'mark', 'percentile']].values.tolist()
    
    return db_data, stats, report_path, general_plot_path

if __name__ == '__main__':
    # مثال للاستخدام والاختبار
    np.random.seed(42)
    # توليد 100 علامة بتوزيع طبيعي بمتوسط 75 وانحراف معياري 10
    sample_marks = np.random.normal(loc=75, scale=10, size=100)
    # تحويل العلامات إلى قائمة من الصفوف (الرقم الجامعي، العلامة)
    sample_data = [(f"2020{i+1:05d}", mark) for i, mark in enumerate(sample_marks)]
    
    db_data, stats, report_path, general_plot_path = process_marks_data(sample_data)
    
    print("--- الإحصائيات ---")
    for k, v in stats.items():
        print(f"{k}: {v:.2f}")
        
    print(f"\nتم توليد تقرير Markdown: {report_path}")
    print(f"تم توليد صورة التوزيع الطبيعي العام: {general_plot_path}")
    
    # مثال على رسم علامة طالب محدد
    marks_df = pd.DataFrame(sample_data, columns=['student_id', 'mark'])
    marks_df = calculate_percentiles(marks_df)
    student_id = "202000050"
    student_mark = marks_df[marks_df['student_id'] == student_id]['mark'].iloc[0]
    student_plot_path = f"plot_{student_id}.png"
    generate_normal_distribution_plot(marks_df, student_mark, student_id, student_plot_path)
    print(f"تم توليد صورة التوزيع الطبيعي للطالب {student_id}: {student_plot_path}")

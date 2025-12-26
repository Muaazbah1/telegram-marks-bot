import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os
from scipy.stats import norm
from tabulate import tabulate
from fpdf import FPDF
from fpdf.fonts import FontFace # لاستخدام الخطوط العربية
import logging

logger = logging.getLogger(__name__)

# إعدادات الخطوط بالإنجليزية
plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['font.sans-serif'] = ['DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

# مسار الخط العربي (يجب أن يكون متوفراً بعد تثبيته في Dockerfile)
# Noto Sans Arabic هو خط يدعم التوصيل
ARABIC_FONT_PATH = "/usr/share/fonts/truetype/noto/NotoSansArabic-Regular.ttf"

class PDFReport(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 15)
        self.cell(0, 10, 'Marks Distribution Report', 0, 1, 'C')

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')

# ... (باقي الدوال process_marks و generate_normal_distribution_plot و generate_text_report تبقى كما هي)

def generate_full_report_pdf(marks_df, stats, plot_path, output_path):
    """
    ينشئ تقرير PDF شامل يحتوي على الإحصائيات وجدول الترتيب والرسم البياني.
    """
    pdf = PDFReport('P', 'mm', 'A4')
    
    # إضافة الخط العربي
    try:
        pdf.add_font('NotoSans', '', ARABIC_FONT_PATH, uni=True)
    except Exception as e:
        logger.error(f"Failed to load Arabic font: {e}")
        # استخدام خط احتياطي إذا فشل تحميل الخط العربي
        pdf.add_font('Arial', '', 'arial.ttf', uni=True) 
        
    pdf.add_page()
    
    # 1. الإحصائيات
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 10, '1. Summary Statistics', 0, 1, 'L')
    
    # ... (كود الإحصائيات يبقى كما هو)
    
    pdf.ln(10)
    
    # 2. جدول الترتيب
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 10, '2. Student Ranking Table (Highest to Lowest)', 0, 1, 'L')
    
    # حساب الترتيب
    # يجب دمج بيانات الاسم مع العلامات
    # بما أن marks_df لا يحتوي على الاسم، سنفترض أننا سنستخدم الاسم من قاعدة البيانات
    
    # سنقوم بتبسيط التقرير لاستخدام البيانات المتاحة حالياً
    # (الاسم غير متاح في marks_df، لذا سنستخدمه من قاعدة البيانات)
    
    # *******************************************************************
    # **ملاحظة هامة:** لإضافة الاسم إلى التقرير، يجب أن يتم استرجاع الاسم
    # من قاعدة البيانات ودمجه مع marks_df قبل استدعاء هذه الدالة.
    # *******************************************************************
    
    # سنقوم بإنشاء DataFrame جديد للتقرير يحتوي على الاسم
    
    # *******************************************************************
    # **لتبسيط الأمر، سنقوم بتعديل bot.py ليمرر DataFrame يحتوي على الاسم**
    # *******************************************************************
    
    # سنقوم بتعديل هذا الجزء في bot.py ليمرر الاسم
    
    # مؤقتاً، سنستخدم الأعمدة المتاحة حالياً
    
    # حساب الترتيب
    ranked_df = marks_df.sort_values(by='mark', ascending=False).reset_index(drop=True)
    ranked_df['Rank'] = ranked_df.index + 1
    
    # الأعمدة المطلوبة: Rank, student_id, student_name, mark
    # بما أن الاسم غير موجود هنا، سنستخدم الأعمدة المتاحة
    ranking_data = [
        ['Rank', 'Student ID', 'Mark']
    ] + ranked_df[['Rank', 'student_id', 'mark']].values.tolist()
    
    pdf.set_font('Arial', '', 10)
    col_width = pdf.w / 4.0
    row_height = 8
    
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
    
    pdf.output(output_path)

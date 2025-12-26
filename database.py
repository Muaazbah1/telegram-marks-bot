import sqlite3
import logging
from config import DB_NAME

logger = logging.getLogger(__name__)

def init_db():
    """تهيئة قاعدة البيانات وإنشاء الجداول."""
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        # جدول الطلاب: user_id هو مفتاح أساسي، student_id فريد
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS students (
                user_id INTEGER PRIMARY KEY,
                student_id TEXT NOT NULL UNIQUE,
                student_name TEXT,
                university TEXT,
                college TEXT
            )
        """)
        conn.commit()
        conn.close()
        logger.info("تم تهيئة قاعدة البيانات بنجاح.")
    except Exception as e:
        logger.error(f"خطأ في تهيئة قاعدة البيانات: {e}")

def register_student(user_id, student_id, university, college):
    """تسجيل طالب جديد (الرقم الجامعي فقط). الاسم سيتم إضافته لاحقاً."""
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        
        # استخدام INSERT OR IGNORE لتسجيل الطالب لأول مرة
        cursor.execute(
            "INSERT OR IGNORE INTO students (user_id, student_id, university, college) VALUES (?, ?, ?, ?)",
            (user_id, student_id, university, college)
        )
        conn.commit()
        conn.close()
        logger.info(f"تم تسجيل الطالب {student_id} بنجاح (بدون اسم مبدئياً).")
    except Exception as e:
        logger.error(f"خطأ في تسجيل الطالب: {e}")

def update_student_name(student_id, student_name):
    """تحديث اسم الطالب بعد استخراجه من ملف العلامات."""
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE students SET student_name = ? WHERE student_id = ?",
            (student_name, student_id)
        )
        conn.commit()
        conn.close()
        logger.info(f"تم تحديث اسم الطالب {student_id} إلى {student_name} بنجاح.")
    except Exception as e:
        logger.error(f"خطأ في تحديث اسم الطالب: {e}")

def get_student_info_by_id(student_id):
    """الحصول على معلومات طالب معين باستخدام رقمه الجامعي."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT user_id, student_name, university, college FROM students WHERE student_id = ?", (student_id,))
    info = cursor.fetchone()
    conn.close()
    return info

def get_student_info_by_user_id(user_id):
    """الحصول على معلومات طالب معين باستخدام Telegram user ID."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT student_id, student_name, university, college FROM students WHERE user_id = ?", (user_id,))
    info = cursor.fetchone()
    conn.close()
    return info

def get_all_students():
    """الحصول على قائمة بجميع الطلاب المسجلين."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT user_id, student_id, student_name, university, college FROM students")
    students = cursor.fetchall()
    conn.close()
    return students

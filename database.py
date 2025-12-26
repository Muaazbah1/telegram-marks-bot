import sqlite3
import logging
from config import DB_NAME

logger = logging.getLogger(__name__)

def init_db():
    """تهيئة قاعدة البيانات وإنشاء الجداول."""
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS students (
                user_id INTEGER PRIMARY KEY,
                student_id TEXT NOT NULL UNIQUE,
                student_name TEXT,  -- تمت الإضافة
                university TEXT,
                college TEXT
            )
        """)
        conn.commit()
        conn.close()
        logger.info("تم تهيئة قاعدة البيانات بنجاح.")
    except Exception as e:
        logger.error(f"خطأ في تهيئة قاعدة البيانات: {e}")

def register_student(user_id, student_id, student_name, university, college):
    """تسجيل طالب جديد أو تحديث بياناته."""
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        
        # استخدام INSERT OR REPLACE لضمان أن التسجيل يتم مرة واحدة فقط
        cursor.execute(
            "INSERT OR REPLACE INTO students (user_id, student_id, student_name, university, college) VALUES (?, ?, ?, ?, ?)",
            (user_id, student_id, student_name, university, college)
        )
        conn.commit()
        conn.close()
        logger.info(f"تم تسجيل/تحديث الطالب {student_id} ({student_name}) بنجاح.")
    except Exception as e:
        logger.error(f"خطأ في تسجيل الطالب: {e}")

def get_student_info(student_id):
    """الحصول على معلومات طالب معين."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT user_id, student_name, university, college FROM students WHERE student_id = ?", (student_id,))
    info = cursor.fetchone()
    conn.close()
    return info

def get_all_students():
    """الحصول على قائمة بجميع الطلاب المسجلين."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    # تم تعديل الاستعلام لإضافة student_name
    cursor.execute("SELECT user_id, student_id, student_name, university, college FROM students")
    students = cursor.fetchall()
    conn.close()
    return students

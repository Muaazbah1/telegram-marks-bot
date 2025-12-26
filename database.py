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
                student_name TEXT,
                university TEXT,
                college TEXT
            )
        """)
        # إضافة جدول جديد لحالة التسجيل المؤقتة
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS registration_state (
                user_id INTEGER PRIMARY KEY,
                state TEXT NOT NULL,
                student_id TEXT
            )
        """)
        conn.commit()
        conn.close()
        logger.info("تم تهيئة قاعدة البيانات بنجاح.")
    except Exception as e:
        logger.error(f"خطأ في تهيئة قاعدة البيانات: {e}")

# ... (باقي دوال تسجيل الطلاب تبقى كما هي)

# دوال جديدة للتعامل مع حالة التسجيل
def get_registration_state(user_id):
    """الحصول على حالة التسجيل الحالية للمستخدم."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT state, student_id FROM registration_state WHERE user_id = ?", (user_id,))
    result = cursor.fetchone()
    conn.close()
    if result:
        return {'state': result[0], 'student_id': result[1]}
    return None

def set_registration_state(user_id, state, student_id=None):
    """تحديث حالة التسجيل للمستخدم."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT OR REPLACE INTO registration_state (user_id, state, student_id) VALUES (?, ?, ?)",
        (user_id, state, student_id)
    )
    conn.commit()
    conn.close()

def clear_registration_state(user_id):
    """مسح حالة التسجيل بعد الانتهاء."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM registration_state WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()

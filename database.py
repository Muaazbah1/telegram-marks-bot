# database.py
import sqlite3
from config import DB_NAME

class Database:
    def __init__(self):
        self.conn = sqlite3.connect(DB_NAME)
        self.cursor = self.conn.cursor()
        self.create_tables()

    def create_tables(self):
        # جدول لتخزين بيانات تسجيل الطلاب
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS students (
                telegram_id INTEGER PRIMARY KEY,
                university TEXT,
                faculty TEXT,
                student_id TEXT UNIQUE,
                is_registered INTEGER DEFAULT 0
            )
        """)
        
        # جدول لتخزين العلامات والتحليل الإحصائي
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS marks (
                student_id TEXT PRIMARY KEY,
                mark REAL,
                percentile REAL,
                FOREIGN KEY (student_id) REFERENCES students(student_id)
            )
        """)
        self.conn.commit()

    def register_student(self, telegram_id, university, faculty, student_id):
        """يسجل الطالب أو يحدث بياناته."""
        try:
            self.cursor.execute("""
                INSERT OR REPLACE INTO students (telegram_id, university, faculty, student_id, is_registered)
                VALUES (?, ?, ?, ?, 1)
            """, (telegram_id, university, faculty, student_id))
            self.conn.commit()
            return True
        except sqlite3.IntegrityError:
            # قد يحدث هذا إذا كان الرقم الجامعي مسجلًا بالفعل لمعرف تليجرام آخر
            return False

    def get_student_info(self, telegram_id):
        """يسترجع معلومات التسجيل للطالب."""
        self.cursor.execute("SELECT university, faculty, student_id, is_registered FROM students WHERE telegram_id = ?", (telegram_id,))
        return self.cursor.fetchone()

    def get_student_mark(self, student_id):
        """يسترجع علامة الطالب والـ percentile."""
        self.cursor.execute("SELECT mark, percentile FROM marks WHERE student_id = ?", (student_id,))
        return self.cursor.fetchone()

    def get_all_registered_students(self):
        """يسترجع جميع الطلاب المسجلين الذين قاموا ببدء البوت."""
        self.cursor.execute("SELECT telegram_id, student_id FROM students WHERE is_registered = 1")
        return self.cursor.fetchall()

    def get_all_marks(self):
        """يسترجع جميع العلامات المخزنة مرتبة تنازلياً."""
        self.cursor.execute("SELECT student_id, mark, percentile FROM marks ORDER BY mark DESC")
        return self.cursor.fetchall()

    def save_marks(self, marks_data):
        """
        يحفظ العلامات في جدول marks.
        marks_data هو قائمة من القوائم/الصفوف: [(student_id, mark, percentile), ...]
        """
        # مسح العلامات القديمة قبل إدخال الجديدة
        self.cursor.execute("DELETE FROM marks")
        self.conn.commit()
        
        # إدخال العلامات الجديدة
        self.cursor.executemany("""
            INSERT INTO marks (student_id, mark, percentile)
            VALUES (?, ?, ?)
        """, marks_data)
        self.conn.commit()
        return self.cursor.rowcount

    def close(self):
        self.conn.close()

if __name__ == '__main__':
    # مثال للاستخدام والاختبار
    db = Database()
    print("Database and tables created successfully.")
    
    # تسجيل طالب تجريبي
    db.register_student(123456789, "جامعة حلب", "كلية الطب البشري", "202012345")
    print(f"Student info: {db.get_student_info(123456789)}")
    
    # حفظ علامات تجريبية
    sample_marks = [
        ("202012345", 85.5, 0.75), # الطالب المسجل
        ("999999999", 90.0, 0.90)  # طالب غير مسجل (سيتم إدخاله في جدول marks)
    ]
    db.save_marks(sample_marks)
    print(f"Mark for 202012345: {db.get_student_mark('202012345')}")
    
    db.close()

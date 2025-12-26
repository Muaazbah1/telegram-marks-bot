# telegram_marks_bot/database.py
import sqlite3
import logging
import json # لإدارة تخزين قائمة الأعمدة

logger = logging.getLogger(__name__)

class Database:
    def __init__(self, db_name="bot_data.db"):
        self.db_name = db_name
        self.conn = None
        self.cursor = None
        self._connect()
        self._create_tables()

    def _connect(self):
        """يتصل بقاعدة البيانات."""
        try:
            self.conn = sqlite3.connect(self.db_name, check_same_thread=False)
            self.cursor = self.conn.cursor()
        except sqlite3.Error as e:
            logger.error(f"خطأ في الاتصال بقاعدة البيانات: {e}")

    def _create_tables(self):
        """ينشئ الجداول المطلوبة."""
        if not self.conn:
            return
            
        # جدول لتسجيل الطلاب
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS students (
                user_id INTEGER PRIMARY KEY,
                student_id TEXT NOT NULL,
                university TEXT,
                faculty TEXT
            )
        """)
        
        # جدول لتخزين العلامات
        # all_columns سيتم تخزينها كسلسلة JSON
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS marks (
                student_id TEXT PRIMARY KEY,
                final_mark REAL,
                percentile REAL,
                all_columns TEXT
            )
        """)
        self.conn.commit()

    def register_student(self, user_id, student_id, university, faculty):
        """يسجل طالب جديد أو يحدث تسجيل موجود."""
        if not self.conn:
            return
            
        self.cursor.execute("""
            INSERT OR REPLACE INTO students (user_id, student_id, university, faculty)
            VALUES (?, ?, ?, ?)
        """, (user_id, student_id, university, faculty))
        self.conn.commit()

    def get_student_registration(self, user_id):
        """يسترجع تسجيل الطالب."""
        if not self.conn:
            return None
            
        self.cursor.execute("SELECT student_id, university, faculty FROM students WHERE user_id = ?", (user_id,))
        return self.cursor.fetchone()

    def save_marks(self, marks_data):
        """يحفظ بيانات العلامات الجديدة."""
        if not self.conn:
            return
            
        # marks_data هي قائمة من الصفوف: (student_id, final_mark, percentile, all_columns)
        data_to_insert = []
        for row in marks_data:
            student_id, final_mark, percentile, all_columns = row
            # تحويل قائمة الأعمدة إلى سلسلة JSON قبل التخزين
            all_columns_json = json.dumps(all_columns)
            data_to_insert.append((student_id, final_mark, percentile, all_columns_json))
            
        self.cursor.executemany("""
            INSERT OR REPLACE INTO marks (student_id, final_mark, percentile, all_columns)
            VALUES (?, ?, ?, ?)
        """, data_to_insert)
        self.conn.commit()

    def get_student_mark(self, student_id):
        """يسترجع علامة طالب معين."""
        if not self.conn:
            return None
            
        self.cursor.execute("SELECT student_id, final_mark, percentile, all_columns FROM marks WHERE student_id = ?", (student_id,))
        result = self.cursor.fetchone()
        
        if result:
            # تحويل سلسلة JSON إلى قائمة عند الاسترجاع
            student_id, final_mark, percentile, all_columns_json = result
            try:
                all_columns = json.loads(all_columns_json)
            except:
                all_columns = all_columns_json # في حال فشل التحويل
            return (student_id, final_mark, percentile, all_columns)
        return None

    def get_all_marks(self):
        """يسترجع جميع العلامات."""
        if not self.conn:
            return []
            
        # يجب أن تكون الأعمدة المسترجعة هي الأربعة المطلوبة فقط
        self.cursor.execute("SELECT student_id, final_mark, percentile, all_columns FROM marks")
        results = self.cursor.fetchall()
        
        # تحويل سلسلة JSON إلى قائمة عند الاسترجاع
        processed_results = []
        for student_id, final_mark, percentile, all_columns_json in results:
            try:
                all_columns = json.loads(all_columns_json)
            except:
                all_columns = all_columns_json
            # هنا يتم إعادة 4 عناصر فقط
            processed_results.append((student_id, final_mark, percentile, all_columns))
            
        return processed_results


    def close(self):
        """يغلق الاتصال بقاعدة البيانات."""
        if self.conn:
            self.conn.close()

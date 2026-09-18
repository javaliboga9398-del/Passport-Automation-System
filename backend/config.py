import os
from pathlib import Path
from dotenv import load_dotenv

# Base Directory of Project
BASE_DIR = Path(__file__).resolve().parent.parent

# Load environment variables
load_dotenv(BASE_DIR / '.env')

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'passport_automation_secret_key_2026_se_lab')

    # Upload folder configuration
    UPLOAD_FOLDER = os.getenv('UPLOAD_FOLDER')

    if UPLOAD_FOLDER:
        UPLOAD_FOLDER = Path(UPLOAD_FOLDER)

        if not UPLOAD_FOLDER.is_absolute():
            UPLOAD_FOLDER = BASE_DIR / UPLOAD_FOLDER
    else:
        UPLOAD_FOLDER = BASE_DIR / 'uploads' / 'documents'

    UPLOAD_FOLDER = str(UPLOAD_FOLDER)

    MAX_CONTENT_LENGTH = int(
        os.getenv('MAX_CONTENT_LENGTH', 5 * 1024 * 1024)
    )

    ALLOWED_EXTENSIONS = {'pdf', 'jpg', 'jpeg', 'png'}

    # Database Configuration
    DB_TYPE = os.getenv('DB_TYPE', 'mysql').lower()
    MYSQL_HOST = os.getenv('MYSQL_HOST', 'localhost')
    MYSQL_PORT = os.getenv('MYSQL_PORT', '3306')
    MYSQL_USER = os.getenv('MYSQL_USER', 'root')
    MYSQL_PASSWORD = os.getenv('MYSQL_PASSWORD', '')
    MYSQL_DB = os.getenv('MYSQL_DB', 'passport_db')

    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    @classmethod
    def get_database_uri(cls):
        """
        Dynamically determine database URI.
        Attempts MySQL connection; if credentials are unset or MySQL is not reachable,
        gracefully falls back to SQLite to guarantee the application runs everywhere.
        """
        if cls.DB_TYPE == 'mysql':
            try:
                import pymysql
                # Test connection to MySQL server
                conn = pymysql.connect(
                    host=cls.MYSQL_HOST,
                    port=int(cls.MYSQL_PORT),
                    user=cls.MYSQL_USER,
                    password=cls.MYSQL_PASSWORD,
                    connect_timeout=2
                )
                # Create database if not exists
                with conn.cursor() as cursor:
                    cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{cls.MYSQL_DB}` DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;")
                conn.commit()
                conn.close()
                
                # Encode password safely if needed
                pw_part = f":{cls.MYSQL_PASSWORD}" if cls.MYSQL_PASSWORD else ""
                uri = f"mysql+pymysql://{cls.MYSQL_USER}{pw_part}@{cls.MYSQL_HOST}:{cls.MYSQL_PORT}/{cls.MYSQL_DB}?charset=utf8mb4"
                print(f"[DB] Connected to MySQL database '{cls.MYSQL_DB}' at {cls.MYSQL_HOST}:{cls.MYSQL_PORT}")
                return uri
            except Exception as e:
                sqlite_path = BASE_DIR / 'passport_db.sqlite'
                print(f"[DB Notice] MySQL connection failed ({e}).")
                print(f"[DB Fallback] Falling back to SQLite database at: {sqlite_path}")
                return f"sqlite:///{sqlite_path}"
        else:
            sqlite_path = BASE_DIR / 'passport_db.sqlite'
            return f"sqlite:///{sqlite_path}"

    @property
    def SQLALCHEMY_DATABASE_URI(self):
        return self.get_database_uri()

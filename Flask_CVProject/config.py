import os
from urllib.parse import quote_plus

# Load environment variables from .env file if available
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # python-dotenv không bắt buộc

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'you-will-never-guess'
    
    # SQL Server database configuration
    # Có thể cấu hình qua environment variables hoặc dùng giá trị mặc định
    DB_SERVER = os.environ.get('DB_SERVER') or 'LAPTOP-TRPSO5N5\\HAOPHAN'
    DB_DATABASE = os.environ.get('DB_DATABASE') or 'DACN5'
    DB_USERNAME = os.environ.get('DB_USERNAME') or 'fang1'
    DB_PASSWORD = os.environ.get('DB_PASSWORD') or 'fang1'
    DB_DRIVER = os.environ.get('DB_DRIVER') or 'ODBC Driver 17 for SQL Server'
    
    encoded_password = quote_plus(DB_PASSWORD)
    SQLALCHEMY_DATABASE_URI = (
        f"mssql+pyodbc://{DB_USERNAME}:{encoded_password}@{DB_SERVER}/{DB_DATABASE}"
        f"?driver={quote_plus(DB_DRIVER)}"
        f"&TrustServerCertificate=yes"
        f"&encoding=utf-8"
        f"&charset=utf8"
        f"&use_unicode=1"
    )
    
    # SQLite database (nếu muốn test nhanh, uncomment dòng này và comment dòng trên)
    # SQLALCHEMY_DATABASE_URI = 'sqlite:///cvision.db'
    
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # SQLAlchemy engine options để đảm bảo UTF-8
    # Lưu ý: Với SQL Server qua pyodbc, cần đảm bảo columns là NVARCHAR/NTEXT
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,  # Kiểm tra kết nối trước khi sử dụng
        'pool_recycle': 3600,   # Tái sử dụng connection sau 1 giờ
        'pool_reset_on_return': 'commit',
        'echo': False,  # Set True để debug SQL queries
    }
    
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY') or 'super-secret-jwt-key'

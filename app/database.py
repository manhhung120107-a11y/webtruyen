import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# 1. Tải các biến môi trường từ file .env lên hệ thống
load_dotenv()

# 2. Đọc các thông số cấu hình bằng thư viện os
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")

# 3. Tạo đường dẫn kết nối tự động điền thông số
SQLALCHEMY_DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# 4. Cấu hình Engine kết nối và BẮT BUỘC bật SSL Mode cho cơ sở dữ liệu Aiven Cloud
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"ssl": {"ssl_mode": "REQUIRED"}}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Hàm tạo phiên làm việc với database cho mỗi request
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
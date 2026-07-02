import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv

# Đọc các biến cấu hình từ file .env
load_dotenv()

# Lấy đường dẫn kết nối
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL")

# Tạo "động cơ" kết nối tới PostgreSQL
engine = create_engine(SQLALCHEMY_DATABASE_URL)

# Tạo một phiên làm việc (Session) mỗi khi có yêu cầu truy xuất dữ liệu
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Khởi tạo Base class (Để sau này các bảng dữ liệu sẽ kế thừa từ đây)
Base = declarative_base()

# Hàm cung cấp kết nối Database cho các API
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
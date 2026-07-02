import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
# [QUAN TRỌNG NHẤT]: Bắt buộc phải import StaticFiles
from fastapi.staticfiles import StaticFiles

from core.database import engine
from modules.documents import models as doc_models
from modules.auth import models as auth_models
from modules.auth.router import router as auth_router
from modules.documents.router import router as document_router

# Tạo các bảng trong Database (nếu chưa có)
auth_models.Base.metadata.create_all(bind=engine)
doc_models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="ISO 15189 Manager API")

# Cấu hình CORS cho phép Frontend (Vue) gọi API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Trong thực tế nên đổi thành ["http://localhost:5173"]
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ========================================================
# [ĐÃ FIX LỖI 404]: MỞ CỔNG PHÁT SÓNG THƯ MỤC UPLOADS
# ========================================================
# 1. Tìm đường dẫn tuyệt đối của thư mục backend
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# 2. Trỏ chính xác đến thư mục data/uploads
UPLOAD_DIR = os.path.join(BASE_DIR, "data", "uploads")

# 3. Đảm bảo thư mục luôn tồn tại để FastAPI không bị sập lúc khởi động
os.makedirs(UPLOAD_DIR, exist_ok=True)

# 4. Mở cổng: Khi Frontend gọi "http://127.0.0.1:8000/uploads/...", FastAPI sẽ vào thư mục UPLOAD_DIR lấy file trả về
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")
# ========================================================


# Nhúng các Router API của các module
app.include_router(auth_router)
app.include_router(document_router)

@app.get("/")
def read_root():
    return {"message": "Welcome to ISO 15189 Manager API"}
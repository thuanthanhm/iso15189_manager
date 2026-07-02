import os
import shutil
import uuid
import io
from datetime import datetime, timezone
from typing import List, Optional # [FIXED]: Added Optional

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from jose import jwt # [FIXED]: Will work after pip install

from core.database import get_db
from core.security import get_current_user, SECRET_KEY, ALGORITHM
from modules.auth.models import User
from modules.auth import models as auth_models # [FIXED]: Added auth_models import
from modules.documents import models, schemas

# ========================================================
# IMPORT THƯ VIỆN ĐÓNG DẤU AN TOÀN
# ========================================================
try:
    import fitz  # PyMuPDF
    HAS_FITZ = True
except ImportError:
    HAS_FITZ = False

router = APIRouter(prefix="/documents", tags=["Document Control"])

# ==========================================
# API QUẢN LÝ THƯ MỤC (FOLDERS)
# ==========================================

@router.post("/folders", response_model=schemas.FolderResponse)
def create_folder(
    folder_in: schemas.FolderCreate, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    if folder_in.parent_id:
        parent = db.query(models.Folder).filter(models.Folder.id == folder_in.parent_id).first()
        if not parent:
            raise HTTPException(status_code=404, detail="Thư mục cha không tồn tại")
    
    new_folder = models.Folder(name=folder_in.name, parent_id=folder_in.parent_id)
    db.add(new_folder)
    db.commit()
    db.refresh(new_folder)
    return new_folder

@router.get("/folders", response_model=List[schemas.FolderTreeResponse])
def get_folder_tree(
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    root_folders = db.query(models.Folder).filter(models.Folder.parent_id == None).all()
    return root_folders

@router.put("/folders/{folder_id}", response_model=schemas.FolderResponse)
def rename_folder(
    folder_id: int, 
    folder_in: schemas.FolderCreate, 
    db: Session = Depends(get_db)
):
    folder = db.query(models.Folder).filter(models.Folder.id == folder_id).first()
    if not folder:
        raise HTTPException(status_code=404, detail="Không tìm thấy thư mục")
    
    folder.name = folder_in.name
    db.commit()
    db.refresh(folder)
    return folder

@router.delete("/folders/{folder_id}")
def delete_folder(
    folder_id: int, 
    db: Session = Depends(get_db)
):
    folder = db.query(models.Folder).filter(models.Folder.id == folder_id).first()
    if not folder:
        raise HTTPException(status_code=404, detail="Không tìm thấy thư mục")
    
    db.delete(folder)
    db.commit()
    return {"message": "Đã xóa thư mục thành công"}


# ==========================================
# API QUẢN LÝ TÀI LIỆU VÀ PHIÊN BẢN
# ==========================================

@router.post("/", response_model=schemas.DocMasterResponse)
def create_document(
    doc_in: schemas.DocMasterCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # 1. Kiểm tra trùng lặp
    exist_master = db.query(models.DocMaster).filter(models.DocMaster.code == doc_in.code).first()
    if exist_master:
        raise HTTPException(status_code=400, detail="Mã tài liệu này đã tồn tại trong hệ thống!")
        
    folder = db.query(models.Folder).filter(models.Folder.id == doc_in.folder_id).first()
    if not folder:
        raise HTTPException(status_code=404, detail="Thư mục lưu trữ không tồn tại!")

    # 2. Tạo Vỏ Tài Liệu 
    new_master = models.DocMaster(
        code=doc_in.code,
        title=doc_in.title,
        doc_type=doc_in.doc_type,
        folder_id=doc_in.folder_id
    )
    db.add(new_master)
    db.commit()
    db.refresh(new_master) 

    # 3. Tạo Ruột Tài Liệu (Bản nháp 1.0) và LƯU FILE GỐC/HTML
    new_version = models.DocVersion(
        master_id=new_master.id,
        version_number="1.0",
        status="Draft",           
        created_by=current_user.id,
        content_html=doc_in.content_html,
        pdf_path=doc_in.file_path # [QUAN TRỌNG]: Gắn đường dẫn file gốc vào DB
    )
    db.add(new_version)
    db.commit()
    db.refresh(new_version) # [BẮT BUỘC]: Lấy ID của version vừa tạo để gắn biểu mẫu phụ

    # 4. Quét và lưu danh sách biểu mẫu đính kèm
    if doc_in.attachments:
        for att in doc_in.attachments:
            new_att = models.DocAttachment(
                version_id=new_version.id, # Gắn chặt vào ID của phiên bản
                file_name=att.file_name,
                file_path=att.file_path,
                file_type=att.file_type
            )
            db.add(new_att)
        db.commit()

    # 5. Refresh lại vỏ tài liệu để xuất ra Frontend đầy đủ cành lá
    db.refresh(new_master) 
    
    return new_master

@router.get("/folder/{folder_id}", response_model=List[schemas.DocMasterResponse])
def get_documents_by_folder(
    folder_id: int, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    docs = db.query(models.DocMaster).filter(models.DocMaster.folder_id == folder_id).all()
    return docs

@router.post("/versions/{version_id}/submit")
def submit_for_approval(
    version_id: int, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    version = db.query(models.DocVersion).filter(models.DocVersion.id == version_id).first()
    if not version:
        raise HTTPException(status_code=404, detail="Không tìm thấy phiên bản tài liệu")
    if version.status != "Draft":
        raise HTTPException(status_code=400, detail="Chỉ bản Nháp (Draft) mới được phép trình duyệt")
    
    version.status = "Pending"
    db.commit()
    return {"message": "Đã trình tài liệu lên cấp quản lý để phê duyệt"}

@router.post("/versions/{version_id}/approve")
def approve_document(
    version_id: int, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    version = db.query(models.DocVersion).filter(models.DocVersion.id == version_id).first()
    if not version:
        raise HTTPException(status_code=404, detail="Không tìm thấy phiên bản tài liệu")
    if version.status != "Pending":
        raise HTTPException(status_code=400, detail="Tài liệu chưa được trình duyệt, không thể phê duyệt")

    old_active = db.query(models.DocVersion).filter(
        models.DocVersion.master_id == version.master_id,
        models.DocVersion.status == "Active"
    ).first()
    
    if old_active:
        old_active.status = "Obsolete"

    version.status = "Active"
    version.approved_by = current_user.id
    version.approved_at = datetime.now(timezone.utc)
    db.commit()
    return {"message": "Đã phê duyệt và ban hành tài liệu thành công"}

# ==========================================
# API UPLOAD VÀ ENGINE ĐÓNG DẤU PDF
# ==========================================

CURRENT_FILE_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.dirname(os.path.dirname(CURRENT_FILE_DIR))
UPLOAD_DIR = os.path.join(BACKEND_DIR, "data", "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True) 

def apply_watermark_to_pdf(pdf_path: str):
    """Engine can thiệp vật lý lõi PDF: Đóng dấu xéo góc tự do & Fix triệt để lỗi font tiếng Việt"""
    if not HAS_FITZ:
        raise Exception("Môi trường Python hiện tại chưa nhận diện được thư viện PyMuPDF. Hãy kiểm tra lại venv.")
        
    temp_path = f"{pdf_path}.tmp"
    doc = None
    
    # 1. Định vị đường dẫn tuyệt đối đến font chữ hỗ trợ tiếng Việt Unicode trên hệ thống Windows
    font_path = "C:/Windows/Fonts/arial.ttf"
    if not os.path.exists(font_path):
        # Dự phòng trường hợp Windows cài trên ổ đĩa khác hoặc biến môi trường thay đổi
        font_path = os.path.join(os.environ.get("SystemRoot", "C:\\Windows"), "Fonts", "arial.ttf")
        
    try:
        doc = fitz.open(pdf_path)
        for page in doc:
            rect = page.rect # Lấy kích thước trang hiện tại
            
            # 2. Đăng ký font chữ tiếng Việt vào tài nguyên của trang PDF
            if os.path.exists(font_path):
                page.insert_font(fontname="Arial_VN", fontfile=font_path)
                font_name = "Arial_VN"
            else:
                # Nếu không tìm thấy font hệ thống, trả về font mặc định (nhưng có thể lỗi hiển thị dấu)
                font_name = "helv" 
            
            # 3. Thiết lập thông số dấu đóng
            text_str = "BẢN KIỂM SOÁT - KHOA GPB"
            font_size = 36
            
            # Xác định điểm tâm tuyệt đối của trang để làm trục xoay hình học
            center_point = fitz.Point(rect.width / 2, rect.height / 2)
            
            # Khởi tạo ma trận xoay góc tự do (Số âm để xoay ngược chiều kim đồng hồ, chéo từ dưới lên)
            # Bạn có thể đổi từ -35 sang -30 hoặc -45 tùy thuộc vào độ dốc mong muốn
            matrix = fitz.Matrix(-35) 
            
            # Tính toán điểm đặt chữ tương đối trước khi xoay:
            # Dịch điểm chèn sang bên trái một khoảng bằng nửa chiều rộng ước lượng của chuỗi chữ để đưa nó về đúng tâm
            insert_x = center_point.x - 220 
            insert_y = center_point.y
            insert_point = fitz.Point(insert_x, insert_y)
            
            # 4. Thực hiện dập chữ vào lõi trang sử dụng tham số morph biến đổi hình học nâng cao
            page.insert_text(
                insert_point,
                text_str,
                fontsize=font_size,
                fontname=font_name,       
                color=(1, 0, 0),       # Màu đỏ RGB
                fill_opacity=0.18,     # Độ mờ 18% (Đủ nhìn rõ nhưng không che mờ nội dung SOP bên dưới)
                morph=(center_point, matrix) # QUAN TRỌNG: Quay cụm chữ xung quanh điểm center_point bằng ma trận matrix
            )
        
        # Lưu file tạm thời
        doc.save(temp_path)
        
    except Exception as e:
        raise Exception(f"Lỗi can thiệp lõi PDF: {str(e)}")
        
    finally:
        # Giải phóng con trỏ file để hệ điều hành Windows nhả quyền khóa file vật lý
        if doc:
            doc.close()
            
    # Ghi đè file an toàn
    try:
        os.replace(temp_path, pdf_path)
    except Exception as e:
        if os.path.exists(temp_path):
            os.remove(temp_path)
        raise Exception(f"Lỗi ghi đè file Watermark: {str(e)}")


# 1. TRẢ LẠI API UPLOAD LƯU FILE SẠCH NGUYÊN BẢN
@router.post("/upload")
async def upload_document_file(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    file_ext = os.path.splitext(file.filename)[1].lower()
    allowed_exts = [".pdf", ".doc", ".docx", ".xls", ".xlsx"]
    if file_ext not in allowed_exts:
        raise HTTPException(status_code=400, detail="Định dạng file không được hỗ trợ!")

    unique_filename = f"{uuid.uuid4().hex}{file_ext}"
    physical_file_path = os.path.join(UPLOAD_DIR, unique_filename)
    db_relative_path = f"uploads/{unique_filename}"

    try:
        with open(physical_file_path, "wb+") as file_object:
            shutil.copyfileobj(file.file, file_object)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi ghi ổ cứng: {str(e)}")

    return {
        "original_name": file.filename,
        "saved_name": unique_filename,
        "file_path": db_relative_path, 
        "file_type": file_ext.replace(".", "").upper() 
    }

@router.get("/stream/{version_id}")
async def stream_watermarked_pdf(
    version_id: int,
    token: Optional[str] = None, 
    db: Session = Depends(get_db)
):
    """API Truyền luồng TỐC ĐỘ CAO (Zero Processing)"""
    if not token:
        raise HTTPException(status_code=401, detail="Thiếu mã xác thực an toàn")
    try:
        # Giải mã token để chắc chắn nhân viên hợp lệ
        jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except Exception:
        raise HTTPException(status_code=401, detail="Phiên truy cập đã hết hạn")

    version = db.query(models.DocVersion).filter(models.DocVersion.id == version_id).first()
    if not version or not version.pdf_path:
        raise HTTPException(status_code=404, detail="Không tìm thấy tệp tin")

    filename = os.path.basename(version.pdf_path)
    physical_path = os.path.join(UPLOAD_DIR, filename)

    if not os.path.exists(physical_path):
        raise HTTPException(status_code=404, detail="Tài liệu vật lý đã bị di dời")

    # Bắn thẳng file gốc cho Frontend xử lý, không can thiệp lõi (Nhanh gấp 10 lần)
    return FileResponse(physical_path, media_type="application/pdf")
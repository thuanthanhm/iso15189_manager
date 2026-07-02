from pydantic import BaseModel, ConfigDict
from typing import List, Optional
from datetime import datetime

# ==========================================
# KHUÔN DỮ LIỆU CHO THƯ MỤC (FOLDERS)
# ==========================================

class FolderBase(BaseModel):
    name: str
    parent_id: Optional[int] = None 

class FolderCreate(FolderBase):
    pass

class FolderResponse(FolderBase):
    id: int
    model_config = ConfigDict(from_attributes=True)

class FolderTreeResponse(FolderResponse):
    children: List['FolderTreeResponse'] = []
    model_config = ConfigDict(from_attributes=True)

FolderTreeResponse.model_rebuild()


# ==========================================
# KHUÔN DỮ LIỆU ĐÍNH KÈM (ATTACHMENTS)
# ==========================================

class AttachmentCreate(BaseModel):
    file_name: str
    file_path: str
    file_type: str

class AttachmentResponse(AttachmentCreate):
    id: int
    version_id: int
    model_config = ConfigDict(from_attributes=True)


# ==========================================
# KHUÔN DỮ LIỆU CHO TÀI LIỆU (DOC_MASTER & DOC_VERSION)
# ==========================================

# 1. Khuôn trả về của Ruột tài liệu (Phiên bản)
class DocVersionResponse(BaseModel):
    id: int
    version_number: str
    status: str
    content_html: Optional[str] = None
    pdf_path: Optional[str] = None
    created_at: datetime
    created_by: int
    approved_by: Optional[int] = None
    # [QUAN TRỌNG]: Trả về mảng đính kèm để màn hình Chi tiết hiển thị
    attachments: List[AttachmentResponse] = [] 
    
    model_config = ConfigDict(from_attributes=True)


# 2. Khuôn nhận dữ liệu khi User tạo Tài liệu mới (ĐÃ HỢP NHẤT)
class DocMasterCreate(BaseModel):
    code: str
    title: str
    doc_type: str       
    folder_id: int      
    content_html: Optional[str] = None
    file_path: Optional[str] = None # Hứng đường dẫn PDF gốc từ Vue
    attachments: Optional[List[AttachmentCreate]] = [] # Hứng danh sách biểu mẫu từ Vue


# 3. Khuôn trả về của Vỏ tài liệu 
class DocMasterResponse(BaseModel):
    id: int
    code: str
    title: str
    doc_type: str
    folder_id: int
    versions: List[DocVersionResponse] = [] 
    
    model_config = ConfigDict(from_attributes=True)
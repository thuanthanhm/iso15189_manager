from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from core.database import Base

# 1. BẢNG FOLDERS (Cấu trúc Cây thư mục lồng nhau)
class Folder(Base):
    __tablename__ = "folders"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    parent_id = Column(Integer, ForeignKey("folders.id"), nullable=True) 
    
    # [ĐÃ SỬA LỖI]: Tách rõ ràng đâu là quan hệ Mẹ (parent) và đâu là quan hệ Con (children)
    children = relationship("Folder", back_populates="parent", cascade="all, delete-orphan")
    parent = relationship("Folder", back_populates="children", remote_side=[id])
    
    documents = relationship("DocMaster", back_populates="folder")



# 2. BẢNG DOC_MASTERS (Vỏ tài liệu - Giữ tính ổn định của Mã số)
class DocMaster(Base):
    __tablename__ = "doc_masters"
    id = Column(Integer, primary_key=True, index=True)
    code = Column(String, unique=True, index=True)      # Mã ISO (VD: SOP.GPB.01)
    title = Column(String, index=True)                  # Tên tài liệu
    doc_type = Column(String)                           # Loại: PDF_INTERNAL, HTML_INTERNAL, EXTERNAL
    folder_id = Column(Integer, ForeignKey("folders.id"))
    
    folder = relationship("Folder", back_populates="documents")
    # Một tài liệu mẹ (Master) có thể có nhiều phiên bản (Versions)
    versions = relationship("DocVersion", back_populates="master", cascade="all, delete-orphan")

# 3. BẢNG DOC_VERSIONS (Ruột tài liệu - Chứa file và lịch sử phiên bản)
class DocVersion(Base):
    __tablename__ = "doc_versions"
    id = Column(Integer, primary_key=True, index=True)
    master_id = Column(Integer, ForeignKey("doc_masters.id"))
    version_number = Column(String, default="1.0")
    content_html = Column(Text, nullable=True)          # Nội dung bài viết (Nếu là dạng HTML)
    pdf_path = Column(String, nullable=True)            # File scan mộc đỏ (Nếu là dạng PDF)
    status = Column(String, default="Draft")            # Draft, Pending (Chờ duyệt), Active (Ban hành), Obsolete (Lỗi thời)
    
    # Lưu vết tác giả và người phê duyệt
    created_by = Column(Integer, ForeignKey("users.id"))
    approved_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    approved_at = Column(DateTime, nullable=True)
    
    master = relationship("DocMaster", back_populates="versions")
    creator = relationship("User", foreign_keys=[created_by])
    approver = relationship("User", foreign_keys=[approved_by])

# 4. BẢNG DOC_REVIEWS (Bằng chứng rà soát định kỳ)
class DocReview(Base):
    __tablename__ = "doc_reviews"
    id = Column(Integer, primary_key=True, index=True)
    version_id = Column(Integer, ForeignKey("doc_versions.id"))
    reviewer_id = Column(Integer, ForeignKey("users.id"))
    review_date = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    content = Column(Text)                              # Nội dung ghi nhận rà soát
    decision = Column(String)                           # Quyết định: KEEP (Giữ nguyên), UPDATE (Cần sửa), ARCHIVE (Hủy)

# 5. BẢNG DOC_ACKNOWLEDGEMENTS (Bằng chứng Đã đọc & Hiểu)
class DocAcknowledgement(Base):
    __tablename__ = "doc_acknowledgements"
    id = Column(Integer, primary_key=True, index=True)
    version_id = Column(Integer, ForeignKey("doc_versions.id"))
    user_id = Column(Integer, ForeignKey("users.id"))
    start_time = Column(DateTime)                       # Lúc mở file
    confirm_time = Column(DateTime, nullable=True)      # Lúc bấm nút "Đã hiểu"
    total_seconds = Column(Integer, default=0)          # Tổng thời gian đọc

# 6. BẢNG DOC_LINKS (Quản lý toàn vẹn liên kết chéo)
class DocLink(Base):
    __tablename__ = "doc_links"
    id = Column(Integer, primary_key=True, index=True)
    source_version_id = Column(Integer, ForeignKey("doc_versions.id")) # Bản đang có link
    target_master_id = Column(Integer, ForeignKey("doc_masters.id"))   # Trỏ về tài liệu gốc

# 7. BẢNG DOC_ATTACHMENTS (Lưu trữ file biểu mẫu, hồ sơ đính kèm phụ)
class DocAttachment(Base):
    __tablename__ = "doc_attachments"
    id = Column(Integer, primary_key=True, index=True)
    version_id = Column(Integer, ForeignKey("doc_versions.id")) # Gắn với phiên bản tài liệu nào
    file_name = Column(String)                                  # Tên hiển thị (VD: BM.01 - Sổ giao nhận)
    file_path = Column(String)                                  # Đường dẫn ổ cứng (VD: data/uploads/bm01.pdf)
    file_type = Column(String)                                  # Loại tệp (PDF, WORD, EXCEL)
    uploaded_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Mối quan hệ ngược lại với bảng Phiên bản (DocVersion)
    version = relationship("DocVersion", backref="attachments")
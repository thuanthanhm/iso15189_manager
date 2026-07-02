from sqlalchemy import Column, Integer, String, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from core.database import Base

class Role(Base):
    __tablename__ = "roles"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    description = Column(String)

    # Mối quan hệ: Một vai trò có thể có nhiều người dùng
    users = relationship("User", back_populates="role")

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    full_name = Column(String)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    is_active = Column(Boolean, default=True)
    
    # Khóa ngoại liên kết với bảng roles
    role_id = Column(Integer, ForeignKey("roles.id"))

    # Mối quan hệ: Người dùng thuộc về một vai trò
    role = relationship("Role", back_populates="users")
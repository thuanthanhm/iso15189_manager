from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from core.database import get_db
from core.security import verify_password, create_access_token
from modules.auth.models import User

# Khởi tạo bộ định tuyến cho chức năng Auth
router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    # 1. Tìm người dùng trong Database dựa vào username người ta nhập
    user = db.query(User).filter(User.username == form_data.username).first()
    
    # 2. Kiểm tra xem user có tồn tại không, và mật khẩu nhập vào (khi băm ra) có khớp không
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Tài khoản hoặc mật khẩu không chính xác",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 3. Nếu đúng hết, tạo thẻ Token chứa tên đăng nhập của họ
    access_token = create_access_token(data={"sub": user.username})
    
    # 4. Trả thẻ Token về cho Frontend
    return {"access_token": access_token, "token_type": "bearer"}
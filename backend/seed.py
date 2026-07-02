from core.database import SessionLocal
from modules.auth.models import Role, User
from core.security import get_password_hash

def seed_data():
    # Mở kết nối đến database
    db = SessionLocal()
    try:
        # 1. Kiểm tra và tạo Role Admin nếu chưa có
        admin_role = db.query(Role).filter(Role.name == "Admin").first()
        if not admin_role:
            admin_role = Role(name="Admin", description="Quản trị viên toàn quyền hệ thống ISO 15189")
            db.add(admin_role)
            db.commit()
            db.refresh(admin_role)
            print("=> Đã tạo thành công Role: Admin")

        # 2. Kiểm tra và tạo User Admin đầu tiên nếu chưa có
        admin_user = db.query(User).filter(User.username == "admin").first()
        if not admin_user:
            # Mã hóa mật khẩu trước khi lưu
            hashed_pw = get_password_hash("Admin@123") 
            
            admin_user = User(
                username="admin",
                full_name="Quản trị viên Hệ thống",
                email="admin@local.host",
                hashed_password=hashed_pw,
                role_id=admin_role.id
            )
            db.add(admin_user)
            db.commit()
            print("=> Đã tạo thành công tài khoản Admin!")
            print("   Tài khoản: admin")
            print("   Mật khẩu: Admin@123")
        else:
            print("=> Tài khoản Admin đã tồn tại trong hệ thống, không cần tạo lại.")

    except Exception as e:
        print(f"Có lỗi xảy ra: {e}")
    finally:
        # Luôn đóng kết nối khi hoàn thành
        db.close()

if __name__ == "__main__":
    print("Đang khởi tạo dữ liệu gốc...")
    seed_data()
"""
Script tạo admin trực tiếp - Tạo tài khoản admin nhanh chóng
Chạy: python create_admin_direct.py
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.extensions import db
from app.models.user import User
from werkzeug.security import generate_password_hash

def create_admin_direct():
    """Tạo admin trực tiếp với thông tin mặc định"""
    app = create_app()
    
    with app.app_context():
        print("=" * 60)
        print("TẠO TÀI KHOẢN ADMIN TRỰC TIẾP")
        print("=" * 60)
        
        # Thông tin admin mặc định
        email = "admin@cvision.com"
        password = "admin123"
        full_name = "Admin CVision"
        
        # Kiểm tra admin đã tồn tại chưa
        existing_admin = User.query.filter_by(email=email).first()
        if existing_admin:
            if existing_admin.role == 'admin':
                print(f"\n✓ Tài khoản admin '{email}' đã tồn tại!")
                print(f"  ID: {existing_admin.id}")
                print(f"  Role: {existing_admin.role}")
                print(f"  Status: {'Active' if existing_admin.is_active else 'Inactive'}")
                return True
            else:
                print(f"\n⚠ Tài khoản '{email}' tồn tại nhưng role là '{existing_admin.role}'")
                response = input("Bạn có muốn đổi thành admin? (y/n): ").strip().lower()
                if response == 'y':
                    existing_admin.role = 'admin'
                    existing_admin.is_active = True
                    db.session.commit()
                    print(f"✓ Đã cập nhật tài khoản '{email}' thành admin!")
                    return True
                else:
                    print("❌ Đã hủy bỏ")
                    return False
        
        # Tạo admin mới
        try:
            admin_user = User(
                email=email,
                password_hash=generate_password_hash(password),
                full_name=full_name,
                role='admin',
                is_active=True
            )
            
            db.session.add(admin_user)
            db.session.commit()
            
            print("\n" + "=" * 60)
            print("✅ TẠO TÀI KHOẢN ADMIN THÀNH CÔNG!")
            print("=" * 60)
            print(f"Email: {email}")
            print(f"Password: {password}")
            print(f"Họ tên: {full_name}")
            print(f"Role: admin")
            print(f"ID: {admin_user.id}")
            print("\nBạn có thể đăng nhập ngay bây giờ!")
            print("=" * 60)
            
            return True
            
        except Exception as e:
            db.session.rollback()
            print(f"\n❌ Lỗi khi tạo admin: {str(e)}")
            import traceback
            traceback.print_exc()
            return False

if __name__ == '__main__':
    import sys
    # Set UTF-8 encoding for Windows
    if sys.platform == 'win32':
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
        sys.stdin = io.TextIOWrapper(sys.stdin.buffer, encoding='utf-8')
    
    try:
        success = create_admin_direct()
        if not success:
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n\n❌ Đã hủy bỏ!")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Lỗi: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


"""
Script tạo admin đơn giản - Tạo admin với thông tin tùy chỉnh
Chạy: python create_admin_simple.py
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.extensions import db
from app.models.user import User
from werkzeug.security import generate_password_hash

def create_admin_simple():
    """Tạo admin với thông tin nhập từ bàn phím"""
    app = create_app()
    
    with app.app_context():
        print("=" * 60)
        print("TẠO TÀI KHOẢN ADMIN ĐƠN GIẢN")
        print("=" * 60)
        
        # Nhập thông tin
        email = input("\nNhập email admin: ").strip()
        if not email:
            print("❌ Email không được để trống!")
            return False
        
        # Kiểm tra email đã tồn tại
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            print(f"❌ Email '{email}' đã tồn tại!")
            if existing_user.role == 'admin':
                print(f"   Tài khoản này đã là admin (ID: {existing_user.id})")
            else:
                response = input(f"   Tài khoản có role '{existing_user.role}'. Đổi thành admin? (y/n): ").strip().lower()
                if response == 'y':
                    existing_user.role = 'admin'
                    existing_user.is_active = True
                    db.session.commit()
                    print(f"✅ Đã cập nhật '{email}' thành admin!")
                    return True
            return False
        
        password = input("Nhập mật khẩu: ").strip()
        if not password or len(password) < 6:
            print("❌ Mật khẩu phải có ít nhất 6 ký tự!")
            return False
        
        full_name = input("Nhập họ tên (tùy chọn, Enter để bỏ qua): ").strip()
        
        # Tạo admin
        try:
            admin_user = User(
                email=email,
                password_hash=generate_password_hash(password),
                full_name=full_name if full_name else None,
                role='admin',
                is_active=True
            )
            
            db.session.add(admin_user)
            db.session.commit()
            
            print("\n" + "=" * 60)
            print("✅ TẠO ADMIN THÀNH CÔNG!")
            print("=" * 60)
            print(f"Email: {email}")
            print(f"Họ tên: {full_name or 'Chưa có'}")
            print(f"Role: admin")
            print(f"ID: {admin_user.id}")
            print("\nBạn có thể đăng nhập ngay bây giờ!")
            print("=" * 60)
            
            return True
            
        except Exception as e:
            db.session.rollback()
            print(f"\n❌ Lỗi: {str(e)}")
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
        success = create_admin_simple()
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


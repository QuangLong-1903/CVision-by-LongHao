"""seed job categories

Revision ID: 9e22568df081
Revises: c816c98c2136
Create Date: 2025-12-03 19:30:04.692024

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic
revision = '9e22568df081'
down_revision = 'c816c98c2136'  # Alembic đã sinh sẵn
branch_labels = None
depends_on = None

def upgrade():
    job_categories = [
        "Công nghệ thông tin",
        "Khoa học dữ liệu & AI",
        "Thiết kế đồ họa & Multimedia",
        "Marketing & Truyền thông",
        "Kinh doanh & Bán hàng",
        "Tài chính & Ngân hàng",
        "Kế toán & Kiểm toán",
        "Quản trị nhân sự",
        "Giáo dục & Đào tạo",
        "Y tế & Chăm sóc sức khỏe",
        "Luật & Pháp lý",
        "Xây dựng & Kiến trúc",
        "Cơ khí & Kỹ thuật",
        "Điện tử & Viễn thông",
        "Logistics & Chuỗi cung ứng",
        "Du lịch & Khách sạn",
        "Nông nghiệp & Thực phẩm",
        "Thời trang & Mỹ phẩm",
        "Báo chí & Nội dung số",
        "Thương mại điện tử"
    ]

    conn = op.get_bind()
    for name in job_categories:
        conn.execute(
            sa.text("INSERT INTO job_categories (name, description) VALUES (:name, :desc)"),
            {"name": name, "desc": f"Ngành {name}"}
        )

def downgrade():
    conn = op.get_bind()
    conn.execute(sa.text("DELETE FROM job_categories"))
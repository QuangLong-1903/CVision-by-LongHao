"""
Script to seed job categories into database
Run this once to populate job_categories table
"""

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__))))

from app import create_app
from app.extensions import db
from app.models import JobCategory
from app.utils.classifier import CATEGORY_KEYWORDS

# Mô tả chi tiết cho từng chuyên ngành
CATEGORY_DESCRIPTIONS = {
    'Software Engineer': 'Lập trình viên phần mềm, phát triển ứng dụng web/mobile, làm việc với các ngôn ngữ lập trình như Python, Java, JavaScript, React, Vue, Angular, Node.js. Bao gồm Backend, Frontend, Full Stack Developer.',
    'Data Scientist': 'Chuyên gia phân tích dữ liệu, machine learning, AI. Làm việc với Python, R, SQL, Pandas, NumPy, TensorFlow, PyTorch, Scikit-learn. Phân tích dữ liệu lớn, xây dựng mô hình dự đoán.',
    'Project Manager': 'Quản lý dự án, điều phối team, quản lý timeline và budget. Làm việc với Agile, Scrum, Kanban. Sử dụng Jira, Confluence. Quản lý stakeholder và tài nguyên.',
    'Marketing': 'Marketing kỹ thuật số, SEO, SEM, Social Media Marketing. Quản lý chiến dịch quảng cáo, branding, content marketing. Làm việc với Google Ads, Facebook Ads, CRM.',
    'Designer': 'Thiết kế UI/UX, Graphic Design. Làm việc với Adobe Photoshop, Illustrator, Figma, Sketch. Thiết kế giao diện web/mobile, wireframe, prototype, brand identity.',
    'Business Analyst': 'Phân tích nghiệp vụ, thu thập yêu cầu, phân tích dữ liệu. Làm việc với SQL, Excel, Power BI. Tạo documentation, user stories, use cases, báo cáo và dashboard.',
    'DevOps Engineer': 'Quản lý infrastructure, CI/CD, Cloud. Làm việc với Docker, Kubernetes, AWS, Azure, GCP. Sử dụng Terraform, Ansible, Jenkins, GitLab. Tự động hóa deployment và monitoring.',
    'HR/Recruitment': 'Quản lý nhân sự, tuyển dụng, talent acquisition. Xử lý onboarding, employee relations, payroll. Quản lý training, performance management, compensation và benefits.',
    'Finance/Accounting': 'Kế toán, tài chính, phân tích tài chính. Làm việc với Excel, QuickBooks, SAP, ERP. Xử lý audit, tax, bookkeeping, budget, forecasting, financial reporting theo GAAP/IFRS.',
    'Sales': 'Bán hàng, phát triển kinh doanh, quản lý khách hàng. Làm việc với CRM, Salesforce. Quản lý pipeline, lead generation, negotiation, đạt quota và revenue targets.'
}

def seed_categories():
    """Seed job categories from classifier keywords"""
    app = create_app()
    
    with app.app_context():
        # Get all categories from classifier
        categories = list(CATEGORY_KEYWORDS.keys())
        
        created_count = 0
        existing_count = 0
        updated_count = 0
        
        for category_name in categories:
            # Check if category already exists
            existing = JobCategory.query.filter_by(name=category_name).first()
            
            if existing:
                # Update description if it's generic
                if existing.description and 'CVs classified as' in existing.description:
                    existing.description = CATEGORY_DESCRIPTIONS.get(category_name, existing.description)
                    print(f"[UPDATE] Updated description for '{category_name}'")
                    updated_count += 1
                else:
                    print(f"[OK] Category '{category_name}' already exists")
                existing_count += 1
            else:
                # Create new category
                new_category = JobCategory(
                    name=category_name,
                    description=CATEGORY_DESCRIPTIONS.get(category_name, f"CVs classified as {category_name} based on keyword matching")
                )
                db.session.add(new_category)
                print(f"[+] Created category '{category_name}'")
                created_count += 1
        
        try:
            db.session.commit()
            print(f"\n{'='*60}")
            print(f"[SUCCESS] Hoàn tất tạo chuyên ngành!")
            print(f"{'='*60}")
            print(f"   ✓ Đã tạo mới: {created_count} chuyên ngành")
            print(f"   ✓ Đã cập nhật: {updated_count} chuyên ngành")
            print(f"   ✓ Đã tồn tại: {existing_count} chuyên ngành")
            print(f"   📊 Tổng cộng: {len(categories)} chuyên ngành")
            print(f"\nDanh sách chuyên ngành:")
            for i, cat in enumerate(categories, 1):
                print(f"   {i}. {cat}")
            print(f"{'='*60}")
        except Exception as e:
            db.session.rollback()
            print(f"\n[ERROR] Lỗi khi tạo chuyên ngành: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
        
        return True

if __name__ == '__main__':
    import sys
    # Set UTF-8 encoding for Windows
    if sys.platform == 'win32':
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    
    print("Seeding job categories...\n")
    success = seed_categories()
    if success:
        print("\nDone!")
    else:
        print("\nFailed!")
        sys.exit(1)


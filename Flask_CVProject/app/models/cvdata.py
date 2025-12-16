"""
Model để lưu dữ liệu CV được nhập từ form (thay vì file upload)
"""

from app.extensions import db
from datetime import datetime
import json

class CVData(db.Model):
    __tablename__ = "cv_data"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    
    # Thông tin cá nhân
    full_name = db.Column(db.String(200))
    email = db.Column(db.String(200))
    phone = db.Column(db.String(50))
    address = db.Column(db.String(500))
    date_of_birth = db.Column(db.Date)
    linkedin = db.Column(db.String(500))
    website = db.Column(db.String(500))
    summary = db.Column(db.Text)  # Mục tiêu nghề nghiệp / Tóm tắt
    
    # Kinh nghiệm làm việc (JSON)
    experiences = db.Column(db.Text)  # JSON array
    
    # Học vấn (JSON)
    education = db.Column(db.Text)  # JSON array
    
    # Kỹ năng (JSON)
    skills = db.Column(db.Text)  # JSON array
    
    # Chứng chỉ / Giải thưởng (JSON)
    certifications = db.Column(db.Text)  # JSON array
    
    # Dự án (JSON)
    projects = db.Column(db.Text)  # JSON array
    
    # Ngôn ngữ (JSON)
    languages = db.Column(db.Text)  # JSON array
    
    # Template được chọn
    template = db.Column(db.String(50), default="classic")
    
    # AI enhanced content (nội dung đã được AI cải thiện)
    ai_enhanced_summary = db.Column(db.Text)
    ai_enhanced_experiences = db.Column(db.Text)  # JSON array
    ai_enhanced_skills = db.Column(db.Text)  # JSON array
    
    # Phân loại
    predicted_category_id = db.Column(db.Integer, db.ForeignKey("job_categories.id"))
    
    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    
    # Relationships
    user = db.relationship("User", backref="cv_data", lazy=True)
    category = db.relationship("JobCategory", backref="cv_data", lazy=True)
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'full_name': self.full_name,
            'email': self.email,
            'phone': self.phone,
            'address': self.address,
            'date_of_birth': self.date_of_birth.isoformat() if self.date_of_birth else None,
            'linkedin': self.linkedin,
            'website': self.website,
            'summary': self.summary,
            'experiences': json.loads(self.experiences) if self.experiences else [],
            'education': json.loads(self.education) if self.education else [],
            'skills': json.loads(self.skills) if self.skills else [],
            'certifications': json.loads(self.certifications) if self.certifications else [],
            'projects': json.loads(self.projects) if self.projects else [],
            'languages': json.loads(self.languages) if self.languages else [],
            'template': self.template,
            'ai_enhanced_summary': self.ai_enhanced_summary,
            'ai_enhanced_experiences': json.loads(self.ai_enhanced_experiences) if self.ai_enhanced_experiences else None,
            'ai_enhanced_skills': json.loads(self.ai_enhanced_skills) if self.ai_enhanced_skills else None,
            'predicted_category_id': self.predicted_category_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def __repr__(self):
        return f"<CVData {self.full_name or 'Untitled'}>"


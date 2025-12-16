from app.extensions import db
from datetime import datetime
from sqlalchemy import Unicode, UnicodeText

class JobPosting(db.Model):
    __tablename__ = "job_postings"

    id = db.Column(db.Integer, primary_key=True)
    recruiter_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    # Sử dụng Unicode/UnicodeText để đảm bảo hỗ trợ tiếng Việt
    title = db.Column(Unicode(200), nullable=False)
    description = db.Column(UnicodeText)
    requirements = db.Column(UnicodeText)
    location = db.Column(Unicode(200))
    salary_min = db.Column(db.Integer)
    salary_max = db.Column(db.Integer)
    category_id = db.Column(db.Integer, db.ForeignKey("job_categories.id"))
    employment_type = db.Column(Unicode(50))
    is_active = db.Column(db.Boolean, default=True)
    deadline = db.Column(db.DateTime)
    company_logo = db.Column(db.String(255))  # Đường dẫn đến logo công ty
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    recruiter = db.relationship("User", backref="job_postings", lazy=True)
    category = db.relationship("JobCategory", backref="job_postings", lazy=True)
    applications = db.relationship("JobApplication", backref="job", lazy=True, cascade="all, delete-orphan")
    job_applications = db.relationship("JobApplication", back_populates="job_posting")

    def __repr__(self):
        return f"<JobPosting {self.title}>"
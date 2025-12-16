from app.extensions import db
from datetime import datetime

class JobApplication(db.Model):
    __tablename__ = "job_applications"

    id = db.Column(db.Integer, primary_key=True)
    job_posting_id = db.Column(db.Integer, db.ForeignKey("job_postings.id"), nullable=False)
    cv_id = db.Column(db.Integer, db.ForeignKey("cvs.id"), nullable=False)
    candidate_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    status = db.Column(db.String(50), default="pending")
    notes = db.Column(db.Text)
    applied_at = db.Column(db.DateTime, default=datetime.utcnow)
    reviewed_at = db.Column(db.DateTime)

    candidate = db.relationship("User", foreign_keys=[candidate_id], backref="job_applications", lazy=True)
    cv = db.relationship("CV", backref="job_applications", lazy=True)
    job_posting = db.relationship("JobPosting", back_populates="job_applications")


    # job = db.relationship("JobPosting", backref="applications", lazy=True)

    def __repr__(self):
        return f"<JobApplication Job={self.job_posting_id}, CV={self.cv_id}, Status={self.status}>"

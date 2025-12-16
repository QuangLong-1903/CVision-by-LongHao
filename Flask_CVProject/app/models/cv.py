from app.extensions import db
from datetime import datetime
class CV(db.Model):
    __tablename__ = "cvs"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    file_name = db.Column(db.String(255), nullable=False)
    file_type = db.Column(db.String(50))
    file_size = db.Column(db.Integer)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)
    predicted_category_id = db.Column(db.Integer, db.ForeignKey("job_categories.id"))
    file_content = db.Column(db.Text)

    logs = db.relationship("ClassificationLog", backref="cv", lazy=True)
    queue = db.relationship("CVProcessingQueue", backref="cv", lazy=True)
    def __repr__(self):
        return f"<CV {self.file_name}>"

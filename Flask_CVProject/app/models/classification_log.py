from app import db
from datetime import datetime
class ClassificationLog(db.Model):
    __tablename__ = "classification_logs"

    id = db.Column(db.Integer, primary_key=True)
    cv_id = db.Column(db.Integer, db.ForeignKey("cvs.id"), nullable=False)
    predicted_category_id = db.Column(db.Integer, db.ForeignKey("job_categories.id"))
    confidence = db.Column(db.Float)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    mlmodel_id = db.Column(db.Integer, db.ForeignKey("ml_models.id"))
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)

    def __repr__(self):
        return f"<ClassificationLog CV={self.cv_id}, confidence={self.confidence}>"
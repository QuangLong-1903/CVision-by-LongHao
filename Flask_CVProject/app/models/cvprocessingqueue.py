from app.extensions import db
from datetime import datetime
class CVProcessingQueue(db.Model):
    __tablename__ = "cv_processing_queue"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)  
    cv_id = db.Column(db.Integer, db.ForeignKey("cvs.id"), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<CVProcessingQueue CV={self.cv_id}>"
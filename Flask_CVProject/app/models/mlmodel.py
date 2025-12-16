from app.extensions import db
from datetime import datetime
class MLModel(db.Model):
    __tablename__ = "ml_models"

    id = db.Column(db.Integer, primary_key=True)
    version = db.Column(db.String(50), unique=True, nullable=False)
    type = db.Column(db.String(100))
    training_date = db.Column(db.DateTime)
    metrics = db.Column(db.Text)
    precision = db.Column(db.Float)
    recall = db.Column(db.Float)
    f1_score = db.Column(db.Float)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    logs = db.relationship("ClassificationLog", backref="ml_model", lazy=True)

    def __repr__(self):
        return f"<MLModel {self.version}>"
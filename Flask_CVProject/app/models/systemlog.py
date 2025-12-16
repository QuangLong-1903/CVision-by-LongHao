from app.extensions import db
from datetime import datetime
class SystemLog(db.Model):
    __tablename__ = "system_logs"

    id = db.Column(db.Integer, primary_key=True)
    version = db.Column(db.String(50))
    ip_address = db.Column(db.String(50))
    timestamp = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<SystemLog {self.version}>"
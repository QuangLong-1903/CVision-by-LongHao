from app.extensions import db
from datetime import datetime

class JobCategory(db.Model):
    __tablename__ = "job_categories"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), unique=True, nullable=False)
    description = db.Column(db.Text)

    cvs = db.relationship("CV", backref="category", lazy=True)
    logs = db.relationship("ClassificationLog", backref="category", lazy=True)
    stats = db.relationship("CategoryStatistic", backref="category", lazy=True)

    def __repr__(self):
        return f"<JobCategory {self.name}>"

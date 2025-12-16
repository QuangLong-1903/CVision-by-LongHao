from app.extensions import db
from datetime import datetime
class CategoryStatistic(db.Model):
    __tablename__ = "category_statistics"

    id = db.Column(db.Integer, primary_key=True)
    category_id = db.Column(db.Integer, db.ForeignKey("job_categories.id"), nullable=False)
    total_count = db.Column(db.Integer, default=0)
    last_updated_count = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<CategoryStatistic {self.category_id}>"
from app import db
class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(50), default="user")

    cvs = db.relationship("CV", backref="user", lazy=True)
    logs = db.relationship("UserActivityLog", backref="user", lazy=True)
    classifications = db.relationship("ClassificationLog", backref="user", lazy=True)
    is_active = db.Column(db.Boolean, default=True)


    def __repr__(self):
        return f"<User {self.email}>"
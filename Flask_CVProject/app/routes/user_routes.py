from flask import Blueprint, request, jsonify
from app.extensions import db
from app.models.user import User
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import create_access_token

user_bp = Blueprint('user_bp', __name__)

@user_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    if not data or not data.get('email') or not data.get('password'):
        return jsonify({"message": "Thiếu thông tin đăng ký"}), 400

    if User.query.filter_by(email=data['email']).first():
        return jsonify({"message": "Email đã tồn tại"}), 400

    hashed_pw = generate_password_hash(data['password'])
    user = User(email=data['email'], password_hash=hashed_pw)
    db.session.add(user)
    db.session.commit()
    return jsonify({"message": "Đăng ký thành công"}), 201


@user_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    user = User.query.filter_by(email=data.get('email')).first()

    if user and check_password_hash(user.password_hash, data.get('password')):
        token = create_access_token(identity=str(user.id))
        return jsonify({"access_token": token, "user_id": user.id}), 200
    return jsonify({"message": "Sai email hoặc mật khẩu"}), 401

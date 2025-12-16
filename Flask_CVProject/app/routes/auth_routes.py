from flask import Blueprint, request, jsonify, render_template
from app.extensions import db
from app.models.user import User
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from datetime import timedelta

auth_bp = Blueprint("auth", __name__)

def get_user_id_from_jwt():
    user_id = get_jwt_identity()
    if isinstance(user_id, str) and user_id.isdigit():
        return int(user_id)
    return user_id

@auth_bp.route("/login", methods=["GET"])
def login_page():
    return render_template("login.html")

@auth_bp.route("/register", methods=["GET"])
def register_page():
    return render_template("register.html")

@auth_bp.route("/profile", methods=["GET"])
def profile_page():
    return render_template("profile.html")

@auth_bp.route("/api/register", methods=["POST"])
def register():
    try:
        data = request.get_json()
        email = data.get("email")
        password = data.get("password")
        full_name = data.get("full_name")
        role = data.get("role", "candidate")

        if not email or not password:
            return jsonify({"error": "Missing email or password"}), 400

        if role not in ["candidate", "recruiter"]:
            return jsonify({"error": "Invalid role. Must be 'candidate' or 'recruiter'"}), 400
        
        if role == "admin":
            return jsonify({"error": "Cannot register as admin"}), 403

        if User.query.filter_by(email=email).first():
            return jsonify({"error": "Email already exists"}), 400

        new_user = User(
            email=email,
            password_hash=generate_password_hash(password),
            full_name=full_name,
            role=role
        )
        db.session.add(new_user)
        db.session.commit()
        return jsonify({"message": "User registered successfully"}), 201
    
    except Exception as e:
        db.session.rollback()
        print(f"Error in register: {str(e)}")
        return jsonify({"error": f"Database error: {str(e)}"}), 500


@auth_bp.route("/api/login", methods=["POST"])
def login():
    data = request.get_json()
    email = data.get("email")
    password = data.get("password")

    user = User.query.filter_by(email=email).first()

    if not user or not check_password_hash(user.password_hash, password):
        return jsonify({"error": "Invalid credentials"}), 401

    access_token = create_access_token(identity=str(user.id), expires_delta=timedelta(hours=2))
    return jsonify({
        "message": "Login successful",
        "access_token": access_token,
        "user": {
            "id": user.id,
            "email": user.email,
            "role": user.role,
            "full_name": user.full_name
        }
    }), 200

@auth_bp.route("/api/me", methods=["GET"])
@jwt_required()
def me():
    user_id = get_user_id_from_jwt()
    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404
    return jsonify({
        "id": user.id,
        "email": user.email,
        "full_name": user.full_name,
        "role": user.role,
        "is_active": user.is_active,
        "created_at": user.created_at.isoformat() if user.created_at else None,
        "updated_at": user.updated_at.isoformat() if user.updated_at else None
    })

@auth_bp.route("/api/me", methods=["PUT"])
@jwt_required()
def update_me():
    user_id = get_user_id_from_jwt()
    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404
    data = request.get_json() or {}
    full_name = data.get("full_name")
    new_password = data.get("new_password")
    current_password = data.get("current_password")

    if full_name is not None:
        user.full_name = full_name.strip()

    if new_password:
        if not current_password or not check_password_hash(user.password_hash, current_password):
            return jsonify({"error": "Current password is incorrect"}), 400
        if len(new_password) < 6:
            return jsonify({"error": "Password must be at least 6 characters"}), 400
        user.password_hash = generate_password_hash(new_password)

    db.session.commit()
    return jsonify({"message": "Profile updated successfully", "full_name": user.full_name})

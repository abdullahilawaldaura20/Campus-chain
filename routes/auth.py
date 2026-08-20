from flask import Blueprint, request, jsonify, session
from extensions import db
from models import User
from flask import current_app

auth_bp = Blueprint("auth", __name__, url_prefix="/api")


def login_required(view_func):
    """Simple session-based auth guard used across all protected routes."""
    from functools import wraps

    @wraps(view_func)
    def wrapped(*args, **kwargs):
        if "user_id" not in session:
            return jsonify({"error": "Login required"}), 401
        return view_func(*args, **kwargs)
    return wrapped


def admin_required(view_func):
    from functools import wraps

    @wraps(view_func)
    def wrapped(*args, **kwargs):
        if "user_id" not in session:
            return jsonify({"error": "Login required"}), 401
        user = User.query.get(session["user_id"])
        if not user or user.role != "admin":
            return jsonify({"error": "Admin access required"}), 403
        return view_func(*args, **kwargs)
    return wrapped


@auth_bp.route("/register", methods=["POST"])
def register():
    data = request.get_json(force=True) or {}
    name = data.get("name", "").strip()
    email = data.get("school_email", "").strip().lower()
    student_id = data.get("student_id", "").strip()
    password = data.get("password", "")

    if not all([name, email, student_id, password]):
        return jsonify({"error": "All fields are required"}), 400

    allowed_domain = current_app.config.get("ALLOWED_EMAIL_DOMAIN")
    if allowed_domain and not email.endswith(allowed_domain):
        return jsonify({"error": f"Email must end with {allowed_domain}"}), 400

    if User.query.filter_by(school_email=email).first():
        return jsonify({"error": "An account with this email already exists"}), 409
    if User.query.filter_by(student_id=student_id).first():
        return jsonify({"error": "An account with this student ID already exists"}), 409

    user = User(name=name, school_email=email, student_id=student_id)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()

    session["user_id"] = user.id
    return jsonify(user.to_dict(include_private=True)), 201


@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json(force=True) or {}
    email = data.get("school_email", "").strip().lower()
    password = data.get("password", "")

    user = User.query.filter_by(school_email=email).first()
    if not user or not user.check_password(password):
        return jsonify({"error": "Invalid email or password"}), 401
    if user.status == "suspended":
        return jsonify({"error": "This account has been suspended"}), 403

    session["user_id"] = user.id
    return jsonify(user.to_dict(include_private=True)), 200


@auth_bp.route("/logout", methods=["POST"])
def logout():
    session.pop("user_id", None)
    return jsonify({"message": "Logged out"}), 200


@auth_bp.route("/me", methods=["GET"])
@login_required
def me():
    user = User.query.get(session["user_id"])
    return jsonify(user.to_dict(include_private=True)), 200

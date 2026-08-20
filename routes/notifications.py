from flask import Blueprint, jsonify, session
from extensions import db
from models import Notification
from routes.auth import login_required

notifications_bp = Blueprint("notifications", __name__, url_prefix="/api/notifications")


@notifications_bp.route("", methods=["GET"])
@login_required
def list_notifications():
    notes = Notification.query.filter_by(user_id=session["user_id"]) \
        .order_by(Notification.created_at.desc()).limit(50).all()
    return jsonify([n.to_dict() for n in notes]), 200


@notifications_bp.route("/unread-count", methods=["GET"])
@login_required
def unread_count():
    count = Notification.query.filter_by(user_id=session["user_id"], read_flag=False).count()
    return jsonify({"unread_count": count}), 200


@notifications_bp.route("/<int:notification_id>/read", methods=["POST"])
@login_required
def mark_read(notification_id):
    note = Notification.query.get_or_404(notification_id)
    if note.user_id != session["user_id"]:
        return jsonify({"error": "Not your notification"}), 403
    note.read_flag = True
    db.session.commit()
    return jsonify(note.to_dict()), 200


@notifications_bp.route("/read-all", methods=["POST"])
@login_required
def mark_all_read():
    Notification.query.filter_by(user_id=session["user_id"], read_flag=False) \
        .update({"read_flag": True})
    db.session.commit()
    return jsonify({"message": "All notifications marked read"}), 200

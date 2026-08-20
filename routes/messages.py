from flask import Blueprint, request, jsonify, session
from sqlalchemy import or_, and_
from extensions import db
from models import Message, User
from routes.auth import login_required
from notifications import notify

messages_bp = Blueprint("messages", __name__, url_prefix="/api")


@messages_bp.route("/messages", methods=["POST"])
@login_required
def send_message():
    data = request.get_json(force=True) or {}
    receiver_id = data.get("receiver_id")
    content = data.get("content", "").strip()

    if not receiver_id or not content:
        return jsonify({"error": "receiver_id and content are required"}), 400
    if not User.query.get(receiver_id):
        return jsonify({"error": "Receiver not found"}), 404

    message = Message(
        sender_id=session["user_id"],
        receiver_id=receiver_id,
        product_id=data.get("product_id"),
        content=content,
    )
    db.session.add(message)
    db.session.commit()

    notify(receiver_id, "message", f"New message from user #{session['user_id']}.", link_id=message.id)

    return jsonify(message.to_dict()), 201


@messages_bp.route("/messages/<int:other_user_id>", methods=["GET"])
@login_required
def get_conversation(other_user_id):
    """Full message thread between the current user and another user."""
    me = session["user_id"]
    thread = Message.query.filter(
        or_(
            and_(Message.sender_id == me, Message.receiver_id == other_user_id),
            and_(Message.sender_id == other_user_id, Message.receiver_id == me),
        )
    ).order_by(Message.sent_at.asc()).all()

    # Mark messages sent to me as read
    for m in thread:
        if m.receiver_id == me and not m.read_flag:
            m.read_flag = True
    db.session.commit()

    return jsonify([m.to_dict() for m in thread]), 200


@messages_bp.route("/messages/inbox", methods=["GET"])
@login_required
def inbox():
    """One row per conversation partner, most recent message first."""
    me = session["user_id"]
    all_msgs = Message.query.filter(
        or_(Message.sender_id == me, Message.receiver_id == me)
    ).order_by(Message.sent_at.desc()).all()

    seen = set()
    conversations = []
    for m in all_msgs:
        partner_id = m.receiver_id if m.sender_id == me else m.sender_id
        if partner_id in seen:
            continue
        seen.add(partner_id)
        conversations.append({
            "partner_id": partner_id,
            "last_message": m.content,
            "sent_at": m.sent_at.isoformat(),
            "unread": (m.receiver_id == me and not m.read_flag),
        })
    return jsonify(conversations), 200

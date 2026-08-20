from flask import Blueprint, request, jsonify
from datetime import datetime, timedelta
from extensions import db
from models import User, Product, Transaction, BlockchainBlock
from routes.auth import admin_required
from blockchain import validate_chain

admin_bp = Blueprint("admin", __name__, url_prefix="/api/admin")


@admin_bp.route("/stats", methods=["GET"])
@admin_required
def stats():
    return jsonify({
        "total_users": User.query.count(),
        "active_listings": Product.query.filter_by(status="available").count(),
        "completed_transactions": Transaction.query.filter_by(status="completed").count(),
        "total_blocks": BlockchainBlock.query.count(),
    }), 200


@admin_bp.route("/users", methods=["GET"])
@admin_required
def list_users():
    users = User.query.order_by(User.created_at.desc()).all()
    return jsonify([u.to_dict(include_private=True) for u in users]), 200


@admin_bp.route("/users/<int:user_id>/suspend", methods=["POST"])
@admin_required
def suspend_user(user_id):
    user = User.query.get_or_404(user_id)
    user.status = "suspended"
    db.session.commit()
    return jsonify(user.to_dict(include_private=True)), 200


@admin_bp.route("/users/<int:user_id>/reinstate", methods=["POST"])
@admin_required
def reinstate_user(user_id):
    user = User.query.get_or_404(user_id)
    user.status = "active"
    db.session.commit()
    return jsonify(user.to_dict(include_private=True)), 200


@admin_bp.route("/products/<int:product_id>", methods=["DELETE"])
@admin_required
def remove_listing(product_id):
    product = Product.query.get_or_404(product_id)
    product.status = "removed"
    db.session.commit()
    return jsonify({"message": "Listing removed"}), 200


@admin_bp.route("/stats/daily-transactions", methods=["GET"])
@admin_required
def daily_transaction_stats():
    """
    Completed-transaction counts per day for the last 14 days —
    feeds a simple line/bar chart on the admin dashboard.
    """
    days = 14
    since = datetime.utcnow() - timedelta(days=days)
    rows = Transaction.query.filter(
        Transaction.status == "completed",
        Transaction.created_at >= since,
    ).all()

    counts = {(since + timedelta(days=i)).date().isoformat(): 0 for i in range(days + 1)}
    for tx in rows:
        key = tx.created_at.date().isoformat()
        if key in counts:
            counts[key] += 1

    series = [{"date": d, "count": c} for d, c in sorted(counts.items())]
    return jsonify(series), 200


@admin_bp.route("/chain/validate", methods=["GET"])
@admin_required
def check_chain():
    return jsonify(validate_chain()), 200


@admin_bp.route("/transactions", methods=["GET"])
@admin_required
def list_transactions():
    txs = Transaction.query.order_by(Transaction.created_at.desc()).all()
    return jsonify([t.to_dict() for t in txs]), 200

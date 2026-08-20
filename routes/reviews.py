from flask import Blueprint, request, jsonify, session
from extensions import db
from models import Review, Transaction
from routes.auth import login_required
from notifications import notify

reviews_bp = Blueprint("reviews", __name__, url_prefix="/api")


@reviews_bp.route("/reviews", methods=["POST"])
@login_required
def submit_review():
    data = request.get_json(force=True) or {}
    transaction_id = data.get("transaction_id")
    rating = data.get("rating")
    comment = data.get("comment", "")

    if not transaction_id or rating is None:
        return jsonify({"error": "transaction_id and rating are required"}), 400
    if not (1 <= int(rating) <= 5):
        return jsonify({"error": "rating must be between 1 and 5"}), 400

    transaction = Transaction.query.get_or_404(transaction_id)
    if transaction.buyer_id != session["user_id"]:
        return jsonify({"error": "Only the buyer can review this transaction"}), 403
    if transaction.status != "completed":
        return jsonify({"error": "You can only review completed transactions"}), 409
    if Review.query.filter_by(transaction_id=transaction_id, reviewer_id=session["user_id"]).first():
        return jsonify({"error": "You've already reviewed this transaction"}), 409

    review = Review(
        transaction_id=transaction_id,
        reviewer_id=session["user_id"],
        seller_id=transaction.seller_id,
        rating=int(rating),
        comment=comment,
    )
    db.session.add(review)
    db.session.commit()

    notify(transaction.seller_id, "review", f"You received a {rating}-star review.", link_id=review.id)

    return jsonify(review.to_dict()), 201


@reviews_bp.route("/users/<int:seller_id>/reviews", methods=["GET"])
def get_seller_reviews(seller_id):
    reviews = Review.query.filter_by(seller_id=seller_id).order_by(Review.created_at.desc()).all()
    return jsonify([r.to_dict() for r in reviews]), 200

from flask import Blueprint, request, jsonify, session
from sqlalchemy import or_
import secrets
import io
import base64
import qrcode
from extensions import db
from models import Product, Transaction, User
from routes.auth import login_required
from blockchain import add_block
from notifications import notify

products_bp = Blueprint("products", __name__, url_prefix="/api")


@products_bp.route("/products", methods=["GET"])
def list_products():
    """
    Search & filter marketplace listings.
    Query params: q, category, min_price, max_price, sort (newest|price_asc|price_desc)
    """
    query = Product.query.filter(Product.status != "removed")

    q = request.args.get("q", "").strip()
    if q:
        like = f"%{q}%"
        query = query.filter(or_(Product.title.ilike(like), Product.description.ilike(like)))

    category = request.args.get("category")
    if category and category.lower() != "all":
        query = query.filter(Product.category == category)

    seller_id = request.args.get("seller_id", type=int)
    if seller_id is not None:
        query = query.filter(Product.seller_id == seller_id)

    min_price = request.args.get("min_price", type=float)
    if min_price is not None:
        query = query.filter(Product.price >= min_price)

    max_price = request.args.get("max_price", type=float)
    if max_price is not None:
        query = query.filter(Product.price <= max_price)

    sort = request.args.get("sort", "newest")
    if sort == "price_asc":
        query = query.order_by(Product.price.asc())
    elif sort == "price_desc":
        query = query.order_by(Product.price.desc())
    else:
        query = query.order_by(Product.created_at.desc())

    products = query.all()
    return jsonify([p.to_dict() for p in products]), 200


@products_bp.route("/products/<int:product_id>", methods=["GET"])
def get_product(product_id):
    product = Product.query.get_or_404(product_id)
    return jsonify(product.to_dict()), 200


@products_bp.route("/products", methods=["POST"])
@login_required
def create_product():
    data = request.get_json(force=True) or {}
    title = data.get("title", "").strip()
    price = data.get("price")
    category = data.get("category", "").strip()

    if not title or price is None or not category:
        return jsonify({"error": "title, price, and category are required"}), 400

    product = Product(
        seller_id=session["user_id"],
        title=title,
        description=data.get("description", ""),
        price=price,
        category=category,
        condition=data.get("condition"),
        image_url=data.get("image_url"),
    )
    db.session.add(product)
    db.session.commit()
    return jsonify(product.to_dict()), 201


@products_bp.route("/products/<int:product_id>", methods=["PUT"])
@login_required
def update_product(product_id):
    product = Product.query.get_or_404(product_id)
    if product.seller_id != session["user_id"]:
        return jsonify({"error": "You can only edit your own listings"}), 403

    data = request.get_json(force=True) or {}
    for field in ["title", "description", "price", "category", "condition", "image_url", "status"]:
        if field in data:
            setattr(product, field, data[field])
    db.session.commit()
    return jsonify(product.to_dict()), 200


@products_bp.route("/products/<int:product_id>", methods=["DELETE"])
@login_required
def delete_product(product_id):
    product = Product.query.get_or_404(product_id)
    if product.seller_id != session["user_id"]:
        return jsonify({"error": "You can only delete your own listings"}), 403
    db.session.delete(product)
    db.session.commit()
    return jsonify({"message": "Listing deleted"}), 200


@products_bp.route("/me/transactions", methods=["GET"])
@login_required
def my_transactions():
    """Every transaction where the current user is buyer or seller."""
    me = session["user_id"]
    txs = Transaction.query.filter(
        or_(Transaction.buyer_id == me, Transaction.seller_id == me)
    ).order_by(Transaction.created_at.desc()).all()
    return jsonify([t.to_dict() for t in txs]), 200


# ---------------- Buy / Sell transaction flow ----------------

@products_bp.route("/products/<int:product_id>/buy-request", methods=["POST"])
@login_required
def request_purchase(product_id):
    product = Product.query.get_or_404(product_id)
    if product.status != "available":
        return jsonify({"error": "This item is no longer available"}), 409
    if product.seller_id == session["user_id"]:
        return jsonify({"error": "You can't buy your own listing"}), 400

    transaction = Transaction(
        product_id=product.id,
        seller_id=product.seller_id,
        buyer_id=session["user_id"],
        amount=product.price,
        status="requested",
    )
    product.status = "pending"
    db.session.add(transaction)
    db.session.commit()

    notify(product.seller_id, "offer", f"New buy request for '{product.title}'.", link_id=transaction.id)

    return jsonify(transaction.to_dict()), 201


@products_bp.route("/transactions/<int:transaction_id>/respond", methods=["POST"])
@login_required
def respond_to_request(transaction_id):
    """Seller accepts or rejects a pending buy request."""
    transaction = Transaction.query.get_or_404(transaction_id)
    if transaction.seller_id != session["user_id"]:
        return jsonify({"error": "Only the seller can respond to this request"}), 403

    decision = (request.get_json(force=True) or {}).get("decision")
    if decision not in ("accept", "reject"):
        return jsonify({"error": "decision must be 'accept' or 'reject'"}), 400

    if decision == "reject":
        transaction.status = "rejected"
        transaction.product.status = "available"
        db.session.commit()
        notify(transaction.buyer_id, "offer", f"Your request for '{transaction.product.title}' was declined.", link_id=transaction.id)
    else:
        transaction.status = "accepted"
        # Unique token used for QR-based in-person handoff verification.
        transaction.qr_code_token = secrets.token_hex(16)
        db.session.commit()
        notify(transaction.buyer_id, "offer", f"Your request for '{transaction.product.title}' was accepted.", link_id=transaction.id)

    return jsonify(transaction.to_dict()), 200


@products_bp.route("/transactions/<int:transaction_id>/complete", methods=["POST"])
@login_required
def complete_transaction(transaction_id):
    """
    Buyer and/or seller confirms the handoff happened.
    This is the hook point for Phase 4: once status flips to 'completed',
    a blockchain block should be appended here (see blockchain.py).
    """
    transaction = Transaction.query.get_or_404(transaction_id)
    if session["user_id"] not in (transaction.buyer_id, transaction.seller_id):
        return jsonify({"error": "Not part of this transaction"}), 403
    if transaction.status != "accepted":
        return jsonify({"error": "Transaction must be accepted before it can be completed"}), 409

    transaction.status = "completed"
    transaction.product.status = "sold"
    db.session.commit()

    # Seal the completed trade into the hash chain. add_block() sets
    # transaction.block_id and commits itself.
    add_block(transaction)

    notify(transaction.buyer_id, "sale", f"Purchase of '{transaction.product.title}' confirmed and sealed on-chain.", link_id=transaction.id)
    notify(transaction.seller_id, "sale", f"Sale of '{transaction.product.title}' confirmed and sealed on-chain.", link_id=transaction.id)

    return jsonify(transaction.to_dict()), 200


# ---------------- QR code verification (Phase 6) ----------------

@products_bp.route("/transactions/<int:transaction_id>/qr", methods=["GET"])
@login_required
def get_transaction_qr(transaction_id):
    """
    Returns a QR code (base64 PNG) encoding the transaction's verification
    token. Either party displays this on their phone; the other scans it
    in person to confirm the handoff via /transactions/verify-qr.
    """
    transaction = Transaction.query.get_or_404(transaction_id)
    if session["user_id"] not in (transaction.buyer_id, transaction.seller_id):
        return jsonify({"error": "Not part of this transaction"}), 403
    if transaction.status != "accepted":
        return jsonify({"error": "QR code is only available once the request is accepted"}), 409
    if not transaction.qr_code_token:
        return jsonify({"error": "No QR token generated for this transaction"}), 409

    img = qrcode.make(transaction.qr_code_token)
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    encoded = base64.b64encode(buffer.getvalue()).decode("utf-8")

    return jsonify({
        "transaction_id": transaction.id,
        "qr_code_token": transaction.qr_code_token,
        "qr_image_base64": f"data:image/png;base64,{encoded}",
    }), 200


@products_bp.route("/transactions/verify-qr", methods=["POST"])
@login_required
def verify_qr():
    """
    The other party scans/enters the token shown on the QR code. A
    successful scan is treated as physical proof of handoff and
    completes the transaction in one step (equivalent to both sides
    manually confirming via /transactions/<id>/complete).
    """
    token = (request.get_json(force=True) or {}).get("token", "").strip()
    if not token:
        return jsonify({"error": "token is required"}), 400

    transaction = Transaction.query.filter_by(qr_code_token=token).first()
    if not transaction:
        return jsonify({"error": "Invalid or expired QR code"}), 404
    if session["user_id"] not in (transaction.buyer_id, transaction.seller_id):
        return jsonify({"error": "Not part of this transaction"}), 403
    if transaction.status != "accepted":
        return jsonify({"error": "This transaction is not awaiting handoff confirmation"}), 409

    transaction.status = "completed"
    transaction.product.status = "sold"
    db.session.commit()

    add_block(transaction)

    notify(transaction.buyer_id, "sale", f"Purchase of '{transaction.product.title}' verified via QR and sealed on-chain.", link_id=transaction.id)
    notify(transaction.seller_id, "sale", f"Sale of '{transaction.product.title}' verified via QR and sealed on-chain.", link_id=transaction.id)

    return jsonify(transaction.to_dict()), 200

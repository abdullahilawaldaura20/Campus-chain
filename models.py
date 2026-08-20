from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from extensions import db


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    school_email = db.Column(db.String(150), unique=True, nullable=False, index=True)
    student_id = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default="student")  # student | admin
    phone = db.Column(db.String(30), nullable=True)
    profile_image = db.Column(db.String(255), nullable=True)
    status = db.Column(db.String(20), nullable=False, default="active")  # active | suspended
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    products = db.relationship("Product", backref="seller", lazy=True)

    def set_password(self, raw_password):
        self.password_hash = generate_password_hash(raw_password)

    def check_password(self, raw_password):
        return check_password_hash(self.password_hash, raw_password)

    @property
    def rating_avg(self):
        reviews = Review.query.filter_by(seller_id=self.id).all()
        if not reviews:
            return None
        return round(sum(r.rating for r in reviews) / len(reviews), 1)

    def to_dict(self, include_private=False):
        data = {
            "id": self.id,
            "name": self.name,
            "role": self.role,
            "status": self.status,
            "rating_avg": self.rating_avg,
            "created_at": self.created_at.isoformat(),
        }
        # Private fields (email, phone, student_id) only included for the
        # account owner or an admin — never sent to other students.
        if include_private:
            data.update({
                "school_email": self.school_email,
                "student_id": self.student_id,
                "phone": self.phone,
            })
        return data


class Product(db.Model):
    __tablename__ = "products"

    id = db.Column(db.Integer, primary_key=True)
    seller_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    title = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, nullable=True)
    price = db.Column(db.Numeric(10, 2), nullable=False)
    category = db.Column(db.String(50), nullable=False)
    condition = db.Column(db.String(30), nullable=True)
    image_url = db.Column(db.String(255), nullable=True)
    status = db.Column(db.String(20), nullable=False, default="available")  # available | pending | sold
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "seller_id": self.seller_id,
            "seller_name": self.seller.name if self.seller else None,
            "title": self.title,
            "description": self.description,
            "price": float(self.price),
            "category": self.category,
            "condition": self.condition,
            "image_url": self.image_url,
            "status": self.status,
            "created_at": self.created_at.isoformat(),
        }


class Transaction(db.Model):
    __tablename__ = "transactions"

    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"), nullable=False)
    seller_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    buyer_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    status = db.Column(db.String(20), nullable=False, default="requested")
    # requested -> accepted -> completed  (or -> rejected / cancelled)
    qr_code_token = db.Column(db.String(64), nullable=True)
    block_id = db.Column(db.Integer, db.ForeignKey("blockchain_blocks.id"), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    product = db.relationship("Product")

    def to_dict(self):
        return {
            "id": self.id,
            "product_id": self.product_id,
            "product_title": self.product.title if self.product else None,
            "seller_id": self.seller_id,
            "buyer_id": self.buyer_id,
            "amount": float(self.amount),
            "status": self.status,
            "qr_code_token": self.qr_code_token,
            "block_id": self.block_id,
            "created_at": self.created_at.isoformat(),
        }


class Review(db.Model):
    __tablename__ = "reviews"

    id = db.Column(db.Integer, primary_key=True)
    transaction_id = db.Column(db.Integer, db.ForeignKey("transactions.id"), nullable=False)
    reviewer_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    seller_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    rating = db.Column(db.Integer, nullable=False)  # 1-5
    comment = db.Column(db.String(500), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "transaction_id": self.transaction_id,
            "reviewer_id": self.reviewer_id,
            "seller_id": self.seller_id,
            "rating": self.rating,
            "comment": self.comment,
            "created_at": self.created_at.isoformat(),
        }


class Message(db.Model):
    __tablename__ = "messages"

    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    receiver_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"), nullable=True)
    content = db.Column(db.String(1000), nullable=False)
    sent_at = db.Column(db.DateTime, default=datetime.utcnow)
    read_flag = db.Column(db.Boolean, default=False)

    def to_dict(self):
        return {
            "id": self.id,
            "sender_id": self.sender_id,
            "receiver_id": self.receiver_id,
            "product_id": self.product_id,
            "content": self.content,
            "sent_at": self.sent_at.isoformat(),
            "read_flag": self.read_flag,
        }


class Notification(db.Model):
    __tablename__ = "notifications"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    type = db.Column(db.String(30), nullable=False)  # message | offer | sale | system
    content = db.Column(db.String(255), nullable=False)
    link_id = db.Column(db.Integer, nullable=True)  # related product_id / transaction_id, context-dependent on type
    read_flag = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "type": self.type,
            "content": self.content,
            "link_id": self.link_id,
            "read_flag": self.read_flag,
            "created_at": self.created_at.isoformat(),
        }


class BlockchainBlock(db.Model):
    """
    Minimal model so Transaction.block_id has somewhere to point.
    Full hashing logic is implemented in Phase 4 (blockchain.py) —
    this table just holds the block rows.
    """
    __tablename__ = "blockchain_blocks"

    id = db.Column(db.Integer, primary_key=True)
    transaction_id = db.Column(db.Integer, db.ForeignKey("transactions.id"), nullable=False)
    seller_id = db.Column(db.Integer, nullable=False)
    buyer_id = db.Column(db.Integer, nullable=False)
    product_id = db.Column(db.Integer, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    previous_hash = db.Column(db.String(64), nullable=False)
    current_hash = db.Column(db.String(64), nullable=False)

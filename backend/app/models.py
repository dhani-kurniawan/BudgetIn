from datetime import datetime
from app import db


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    username = db.Column(db.String(50), unique=True, nullable=True)
    phone = db.Column(db.String(30), nullable=True)
    profile_photo = db.Column(db.String(255), nullable=True)  # nama file di folder uploads/profile
    last_login = db.Column(db.DateTime, nullable=True)  # disimpan UTC
    email_verified = db.Column(db.Boolean, default=False)
    password_changed_at = db.Column(db.DateTime, nullable=True)  # token login yang terbit sebelum ini dianggap tidak berlaku
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    transactions = db.relationship("Transaction", backref="user", cascade="all, delete-orphan")
    targets = db.relationship("Target", backref="user", cascade="all, delete-orphan")


class Category(db.Model):
    __tablename__ = "categories"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    name = db.Column(db.String(100), nullable=False)
    type = db.Column(db.Enum("income", "expense", name="category_type"), nullable=False)
    is_default = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Transaction(db.Model):
    __tablename__ = "transactions"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey("categories.id"), nullable=False)
    # Sumber dana: kategori PEMASUKAN (mis. Gaji/Bonus) yang membiayai pengeluaran ini.
    # Hanya diisi untuk type = expense.
    source_id = db.Column(db.Integer, db.ForeignKey("categories.id"), nullable=True)
    type = db.Column(db.Enum("income", "expense", name="transaction_type"), nullable=False)
    amount = db.Column(db.Numeric(15, 2), nullable=False)
    currency_code = db.Column(db.String(3), nullable=False, default="IDR")
    exchange_rate = db.Column(db.Numeric(15, 6), nullable=False, default=1)
    amount_idr = db.Column(db.Numeric(15, 2), nullable=False)
    transaction_date = db.Column(db.Date, nullable=False)
    note = db.Column(db.String(255))
    receipt_image = db.Column(db.String(255), nullable=True)  # nama file foto bon di uploads/receipts/<user_id>/
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    category = db.relationship("Category", foreign_keys=[category_id])
    source = db.relationship("Category", foreign_keys=[source_id])


class Target(db.Model):
    __tablename__ = "targets"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    type = db.Column(db.Enum("expense_limit", "savings", name="target_type"), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    target_amount = db.Column(db.Numeric(15, 2), nullable=False)
    period_start = db.Column(db.Date, nullable=False)
    period_end = db.Column(db.Date, nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey("categories.id"), nullable=True)
    note = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    category = db.relationship("Category")


class AuthToken(db.Model):
    """Token sekali pakai untuk verifikasi email dan reset password. Yang disimpan hanya hash-nya."""

    __tablename__ = "auth_tokens"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    purpose = db.Column(db.String(20), nullable=False)  # "verify_email" | "reset_password"
    token_hash = db.Column(db.String(64), nullable=False, unique=True)
    expires_at = db.Column(db.DateTime, nullable=False)
    used_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

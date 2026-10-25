import os
import uuid
from datetime import date as date_cls

import requests
from flask import Blueprint, request, jsonify, send_from_directory
from flask_jwt_extended import jwt_required
from sqlalchemy import func, or_, and_
from app import db
from app.models import Transaction, Category
from app.utils import (
    current_user_id, retention_cutoff, parse_date, date_arg, finite_number, MAX_AMOUNT,
    purge_old_transactions, read_image_upload, receipt_dir, delete_receipt_file, json_body,
)

transactions_bp = Blueprint("transactions", __name__)


def rupiah(value) -> str:
    return "Rp " + f"{int(round(value)):,}".replace(",", ".")


def source_balance(user_id, source_id, exclude_tx_id=None) -> float:
    """Saldo sumber dana = total pemasukan kategori itu - total pengeluaran yang memakai sumber itu."""
    def total(*conds):
        q = db.session.query(func.coalesce(func.sum(Transaction.amount_idr), 0)).filter(
            Transaction.user_id == user_id, *conds
        )
        if exclude_tx_id:
            q = q.filter(Transaction.id != exclude_tx_id)
        return float(q.scalar())

    income = total(Transaction.type == "income", Transaction.category_id == source_id)
    expense = total(Transaction.type == "expense", Transaction.source_id == source_id)
    return round(income - expense, 2)


def _visible_category(user_id, category_id, type_):
    return Category.query.filter(
        Category.id == category_id,
        Category.type == type_,
        (Category.is_default == True) | (Category.user_id == user_id),  # noqa: E712
    ).first()


def _purge_old(user_id):
    """Retensi maksimal 3 tahun: hapus transaksi (dan foto bonnya) yang lebih lama dari batas."""
    purge_old_transactions(user_id)


@transactions_bp.route("", methods=["GET"])
@jwt_required()
def list_transactions():
    user_id = current_user_id()
    _purge_old(user_id)
    query = Transaction.query.filter_by(user_id=user_id)

    # Filter opsional lewat query string: ?category_id=&type=&start=&end=&limit=
    category_id = request.args.get("category_id", type=int)
    type_ = request.args.get("type")
    start, err1 = date_arg("start")
    end, err2 = date_arg("end")
    limit = request.args.get("limit", type=int)
    source_id = request.args.get("source_id", type=int)
    if err1 or err2:
        return jsonify({"error": err1 or err2}), 400
    if type_ and type_ not in ("income", "expense"):
        return jsonify({"error": "type harus income atau expense"}), 400

    if category_id:
        query = query.filter_by(category_id=category_id)
    if type_:
        query = query.filter_by(type=type_)
    if source_id:  # pemasukan kategori itu + pengeluaran yang dibiayai sumber itu
        query = query.filter(
            or_(
                and_(Transaction.type == "income", Transaction.category_id == source_id),
                and_(Transaction.type == "expense", Transaction.source_id == source_id),
            )
        )
    if start:
        query = query.filter(Transaction.transaction_date >= start)
    if end:
        query = query.filter(Transaction.transaction_date <= end)

    query = query.order_by(Transaction.transaction_date.desc(), Transaction.id.desc())
    if limit:
        query = query.limit(min(limit, 500))
    return jsonify([_serialize(t) for t in query.all()]), 200


def _validate(data, partial=False):
    """Mengembalikan pesan error (str) atau None."""
    if "type" in data and data["type"] not in ("income", "expense"):
        return "type harus income atau expense"
    if "amount" in data and finite_number(data["amount"]) is None:
        return "Jumlah uang harus berupa angka lebih dari 0 dan tidak terlalu besar"
    if "exchange_rate" in data and finite_number(data["exchange_rate"], maximum=999_999_999) is None:
        return "Kurs harus berupa angka lebih dari 0"
    if "transaction_date" in data:
        try:
            d = parse_date(data["transaction_date"])
        except (TypeError, ValueError):
            return "Format tanggal harus YYYY-MM-DD"
        if d < retention_cutoff():
            return "Tanggal transaksi melebihi batas retensi 3 tahun"
    if "currency_code" in data:
        code = str(data["currency_code"])
        if len(code) != 3 or not code.isascii() or not code.isalpha():
            return "Kode mata uang harus 3 huruf"
    return None


def _check_total(amount_idr):
    """Total dalam Rupiah harus muat di kolom DECIMAL(15,2)."""
    if amount_idr > MAX_AMOUNT:
        return "Total dalam Rupiah terlalu besar"
    return None


@transactions_bp.route("", methods=["POST"])
@jwt_required()
def create_transaction():
    user_id = current_user_id()
    data = json_body()

    required = ["category_id", "type", "amount", "transaction_date"]
    if not all(data.get(f) for f in required):
        return jsonify({"error": f"Field wajib: {', '.join(required)}"}), 400
    err = _validate(data)
    if err:
        return jsonify({"error": err}), 400

    category = _visible_category(user_id, data["category_id"], data["type"])
    if not category:
        return jsonify({"error": "Kategori tidak ditemukan atau tidak sesuai jenis transaksi"}), 400

    currency_code = str(data.get("currency_code", "IDR")).upper()
    exchange_rate = 1.0 if currency_code == "IDR" else float(data.get("exchange_rate", 1))
    amount = float(data["amount"])
    amount_idr = round(amount * exchange_rate, 2)
    err = _check_total(amount_idr)
    if err:
        return jsonify({"error": err}), 400

    source_id = None
    if data["type"] == "expense":
        err, source_id = _check_source(user_id, data.get("source_id"), amount_idr)
        if err:
            return jsonify({"error": err}), 400

    transaction = Transaction(
        user_id=user_id,
        category_id=category.id,
        source_id=source_id,
        type=data["type"],
        amount=amount,
        currency_code=currency_code,
        exchange_rate=exchange_rate,
        amount_idr=amount_idr,
        transaction_date=parse_date(data["transaction_date"]),
        note=(data.get("note") or "").strip()[:255] or None,
    )
    db.session.add(transaction)
    db.session.commit()

    return jsonify(_serialize(transaction)), 201


def _check_source(user_id, source_id, amount_idr, exclude_tx_id=None):
    """Validasi sumber dana pengeluaran. Return (error, source_id)."""
    if not source_id:
        return "Sumber dana wajib dipilih untuk pengeluaran", None
    source = _visible_category(user_id, source_id, "income")
    if not source:
        return "Sumber dana harus berupa kategori pemasukan", None
    available = source_balance(user_id, source.id, exclude_tx_id)
    if amount_idr > available + 0.005:
        return f"Saldo sumber dana {source.name} tidak cukup (sisa {rupiah(max(available, 0))})", None
    return None, source.id


@transactions_bp.route("/<int:transaction_id>", methods=["PUT"])
@jwt_required()
def update_transaction(transaction_id):
    user_id = current_user_id()
    transaction = Transaction.query.filter_by(id=transaction_id, user_id=user_id).first()
    if not transaction:
        return jsonify({"error": "Transaksi tidak ditemukan"}), 404

    data = json_body()
    err = _validate(data, partial=True)
    if err:
        return jsonify({"error": err}), 400

    # Nilai baru (gabungan data lama + perubahan), dihitung dulu sebelum menyimpan apa pun
    new_type = data.get("type", transaction.type)
    try:
        new_category_id = int(data.get("category_id", transaction.category_id))
    except (TypeError, ValueError):
        return jsonify({"error": "category_id tidak valid"}), 400
    new_currency = str(data.get("currency_code", transaction.currency_code)).upper()
    new_amount = float(data.get("amount", transaction.amount))
    new_rate = 1.0 if new_currency == "IDR" else float(data.get("exchange_rate", transaction.exchange_rate))
    new_amount_idr = round(new_amount * new_rate, 2)
    err = _check_total(new_amount_idr)
    if err:
        return jsonify({"error": err}), 400

    category = _visible_category(user_id, new_category_id, new_type)
    if not category:
        return jsonify({"error": "Kategori tidak ditemukan atau tidak sesuai jenis transaksi"}), 400

    new_source_id = None
    if new_type == "expense":
        err, new_source_id = _check_source(
            user_id, data.get("source_id", transaction.source_id), new_amount_idr, exclude_tx_id=transaction.id
        )
        if err:
            return jsonify({"error": err}), 400

    # Kalau ini pemasukan lama, pastikan perubahan tidak membuat saldo sumber dananya minus
    if transaction.type == "income":
        old_cat = transaction.category_id
        still_same = new_type == "income" and new_category_id == old_cat
        remaining = source_balance(user_id, old_cat, exclude_tx_id=transaction.id) + (new_amount_idr if still_same else 0)
        if remaining < -0.005:
            return jsonify({"error": "Tidak bisa diubah: dana dari pemasukan ini sudah dipakai pengeluaran"}), 400

    transaction.type = new_type
    transaction.category_id = new_category_id
    transaction.source_id = new_source_id
    transaction.currency_code = new_currency
    transaction.amount = new_amount
    transaction.exchange_rate = new_rate
    transaction.amount_idr = new_amount_idr
    if "transaction_date" in data:
        transaction.transaction_date = parse_date(data["transaction_date"])
    if "note" in data:
        transaction.note = (data["note"] or "").strip()[:255] or None

    db.session.commit()
    return jsonify(_serialize(transaction)), 200


@transactions_bp.route("/<int:transaction_id>", methods=["DELETE"])
@jwt_required()
def delete_transaction(transaction_id):
    user_id = current_user_id()
    transaction = Transaction.query.filter_by(id=transaction_id, user_id=user_id).first()
    if not transaction:
        return jsonify({"error": "Transaksi tidak ditemukan"}), 404

    if transaction.type == "income" and source_balance(user_id, transaction.category_id, transaction.id) < -0.005:
        return jsonify({"error": "Tidak bisa dihapus: dana dari pemasukan ini sudah dipakai pengeluaran"}), 400

    receipt = transaction.receipt_image
    db.session.delete(transaction)
    db.session.commit()
    delete_receipt_file(user_id, receipt)
    return jsonify({"message": "Transaksi dihapus"}), 200


# ---------- Foto bon / struk (privat: hanya pemilik transaksi yang bisa melihat) ----------
def _own_transaction(transaction_id):
    return Transaction.query.filter_by(id=transaction_id, user_id=current_user_id()).first()


@transactions_bp.route("/<int:transaction_id>/receipt", methods=["POST"])
@jwt_required()
def upload_receipt(transaction_id):
    transaction = _own_transaction(transaction_id)
    if not transaction:
        return jsonify({"error": "Transaksi tidak ditemukan"}), 404
    file = request.files.get("receipt")
    if not file or not file.filename:
        return jsonify({"error": "File foto bon tidak ditemukan"}), 400

    data, ext, err = read_image_upload(file, 5 * 1024 * 1024)
    if err:
        return jsonify({"error": err}), 400

    filename = f"{uuid.uuid4().hex}.{ext}"
    with open(os.path.join(receipt_dir(transaction.user_id), filename), "wb") as f:
        f.write(data)
    delete_receipt_file(transaction.user_id, transaction.receipt_image)  # ganti foto lama
    transaction.receipt_image = filename
    db.session.commit()
    return jsonify(_serialize(transaction)), 200


@transactions_bp.route("/<int:transaction_id>/receipt", methods=["GET"])
@jwt_required()
def get_receipt(transaction_id):
    transaction = _own_transaction(transaction_id)
    if not transaction or not transaction.receipt_image:
        return jsonify({"error": "Foto bon tidak ditemukan"}), 404
    resp = send_from_directory(receipt_dir(transaction.user_id), os.path.basename(transaction.receipt_image))
    resp.headers["Cache-Control"] = "private, max-age=300"
    return resp


@transactions_bp.route("/<int:transaction_id>/receipt", methods=["DELETE"])
@jwt_required()
def delete_receipt(transaction_id):
    transaction = _own_transaction(transaction_id)
    if not transaction:
        return jsonify({"error": "Transaksi tidak ditemukan"}), 404
    delete_receipt_file(transaction.user_id, transaction.receipt_image)
    transaction.receipt_image = None
    db.session.commit()
    return jsonify(_serialize(transaction)), 200


@transactions_bp.route("/rate", methods=["GET"])
@jwt_required()
def get_rate():
    """Ambil kurs ke IDR dari Frankfurter (gratis). ?from=USD&date=YYYY-MM-DD (date opsional)"""
    from_ccy = (request.args.get("from") or "").upper()
    if len(from_ccy) != 3 or not from_ccy.isascii() or not from_ccy.isalpha():
        return jsonify({"error": "Parameter from (kode mata uang) wajib"}), 400
    if from_ccy == "IDR":
        return jsonify({"from": "IDR", "to": "IDR", "rate": 1}), 200

    rate_date, err = date_arg("date")
    if err:
        return jsonify({"error": err}), 400
    # Tanggal masa depan / kosong -> kurs terbaru; tanggal lampau -> kurs pada tanggal itu
    path = rate_date if rate_date and parse_date(rate_date) < date_cls.today() else "latest"
    try:
        r = requests.get(
            f"https://api.frankfurter.app/{path}",
            params={"from": from_ccy, "to": "IDR"},
            timeout=6,
        )
        r.raise_for_status()
        body = r.json()
        return jsonify({"from": from_ccy, "to": "IDR", "rate": body["rates"]["IDR"], "date": body.get("date")}), 200
    except Exception:
        return jsonify({"error": "Gagal mengambil kurs otomatis, isi manual saja"}), 502


def _serialize(t: Transaction):
    return {
        "id": t.id,
        "category_id": t.category_id,
        "category_name": t.category.name if t.category else None,
        "source_id": t.source_id,
        "source_name": t.source.name if t.source else None,
        "has_receipt": bool(t.receipt_image),
        "type": t.type,
        "amount": float(t.amount),
        "currency_code": t.currency_code,
        "exchange_rate": float(t.exchange_rate),
        "amount_idr": float(t.amount_idr),
        "transaction_date": t.transaction_date.isoformat(),
        "note": t.note,
    }

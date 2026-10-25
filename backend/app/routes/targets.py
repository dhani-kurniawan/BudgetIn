from datetime import date
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from sqlalchemy import func
from app import db
from app.models import Target, Transaction, Category
from app.utils import current_user_id, parse_date, json_body, finite_number

targets_bp = Blueprint("targets", __name__)


@targets_bp.route("", methods=["GET"])
@jwt_required()
def list_targets():
    user_id = current_user_id()
    targets = Target.query.filter_by(user_id=user_id).order_by(Target.period_end.asc()).all()
    return jsonify([_serialize_with_evaluation(t) for t in targets]), 200


def _parse_payload(data, user_id):
    """Validasi payload target. Return (cleaned, error)."""
    required = ["type", "name", "target_amount", "period_start", "period_end"]
    if not all(data.get(f) for f in required):
        return None, f"Field wajib: {', '.join(required)}"
    if data["type"] not in ("expense_limit", "savings"):
        return None, "type harus expense_limit atau savings"
    amount = finite_number(data["target_amount"])
    if amount is None:
        return None, "Nominal target harus berupa angka lebih dari 0 dan tidak terlalu besar"
    try:
        start = parse_date(data["period_start"])
        end = parse_date(data["period_end"])
    except (TypeError, ValueError):
        return None, "Format tanggal harus YYYY-MM-DD"
    if end < start:
        return None, "Tanggal selesai tidak boleh sebelum tanggal mulai"

    category_id = data.get("category_id") or None
    if data["type"] == "savings":
        category_id = None  # tabungan dihitung dari seluruh pemasukan - pengeluaran
    if category_id:
        cat = Category.query.filter(
            Category.id == category_id,
            (Category.is_default == True) | (Category.user_id == user_id),  # noqa: E712
        ).first()
        if not cat or cat.type != "expense":
            return None, "Kategori target harus kategori pengeluaran milik kamu"

    return {
        "type": data["type"],
        "name": str(data["name"]).strip()[:100],
        "target_amount": amount,
        "period_start": start,
        "period_end": end,
        "category_id": category_id,
        "note": (data.get("note") or "").strip()[:255] or None,
    }, None


@targets_bp.route("", methods=["POST"])
@jwt_required()
def create_target():
    user_id = current_user_id()
    cleaned, err = _parse_payload(json_body(), user_id)
    if err:
        return jsonify({"error": err}), 400

    target = Target(user_id=user_id, **cleaned)
    db.session.add(target)
    db.session.commit()
    return jsonify(_serialize_with_evaluation(target)), 201


@targets_bp.route("/<int:target_id>", methods=["PUT"])
@jwt_required()
def update_target(target_id):
    user_id = current_user_id()
    target = Target.query.filter_by(id=target_id, user_id=user_id).first()
    if not target:
        return jsonify({"error": "Target tidak ditemukan"}), 404

    cleaned, err = _parse_payload(json_body(), user_id)
    if err:
        return jsonify({"error": err}), 400
    for k, v in cleaned.items():
        setattr(target, k, v)
    db.session.commit()
    return jsonify(_serialize_with_evaluation(target)), 200


@targets_bp.route("/<int:target_id>", methods=["DELETE"])
@jwt_required()
def delete_target(target_id):
    user_id = current_user_id()
    target = Target.query.filter_by(id=target_id, user_id=user_id).first()
    if not target:
        return jsonify({"error": "Target tidak ditemukan"}), 404
    db.session.delete(target)
    db.session.commit()
    return jsonify({"message": "Target dihapus"}), 200


def _sum(user_id, type_, target, category_id=None):
    q = db.session.query(func.coalesce(func.sum(Transaction.amount_idr), 0)).filter(
        Transaction.user_id == user_id,
        Transaction.type == type_,
        Transaction.transaction_date >= target.period_start,
        Transaction.transaction_date <= target.period_end,
    )
    if category_id:
        q = q.filter(Transaction.category_id == category_id)
    return float(q.scalar())


def _serialize_with_evaluation(target: Target):
    """
    Evaluasi target:
    - expense_limit: jumlahkan transaksi 'expense' dalam periode (dan kategori bila diisi),
      bandingkan dengan target_amount.
    - savings: jumlahkan (income - expense) dalam periode, bandingkan dengan target_amount.
    Status: "aman" | "mendekati_batas" | "terlampaui" | "tercapai" | "belum_tercapai"
    """
    user_id = target.user_id
    amount = float(target.target_amount)

    if target.type == "expense_limit":
        current_value = _sum(user_id, "expense", target, target.category_id)
        progress = current_value / amount if amount else 0
        if progress >= 1:
            status = "terlampaui"
        elif progress >= 0.8:
            status = "mendekati_batas"
        else:
            status = "aman"
    else:  # savings
        current_value = _sum(user_id, "income", target) - _sum(user_id, "expense", target)
        progress = max(current_value, 0) / amount if amount else 0
        status = "tercapai" if progress >= 1 else "belum_tercapai"

    today = date.today()
    days_left = (target.period_end - today).days
    return {
        "id": target.id,
        "type": target.type,
        "name": target.name,
        "target_amount": amount,
        "period_start": target.period_start.isoformat(),
        "period_end": target.period_end.isoformat(),
        "category_id": target.category_id,
        "category_name": target.category.name if target.category else None,
        "note": target.note,
        "current_value": current_value,
        "progress_percent": round(progress * 100, 1),
        "status": status,
        "days_left": days_left,
        "is_active": target.period_start <= today <= target.period_end,
        "is_finished": days_left < 0,
    }

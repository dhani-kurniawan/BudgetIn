from collections import defaultdict
from datetime import date, timedelta
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from sqlalchemy import func
from app import db
from app.models import Transaction, Category
from app.utils import current_user_id, retention_cutoff, date_arg

dashboard_bp = Blueprint("dashboard", __name__)

MONTHS_ID = ["Jan", "Feb", "Mar", "Apr", "Mei", "Jun", "Jul", "Agu", "Sep", "Okt", "Nov", "Des"]


def _scope(q, type_, source_id):
    """Batasi query ke satu sumber dana: pemasukan = kategori itu, pengeluaran = yang memakai sumber itu."""
    if not source_id:
        return q
    if type_ == "income":
        return q.filter(Transaction.category_id == source_id)
    return q.filter(Transaction.source_id == source_id)


@dashboard_bp.route("/summary", methods=["GET"])
@jwt_required()
def summary():
    user_id = current_user_id()
    start, err1 = date_arg("start")  # opsional, format YYYY-MM-DD
    end, err2 = date_arg("end")
    if err1 or err2:
        return jsonify({"error": err1 or err2}), 400
    source_id = request.args.get("source_id", type=int)

    def base(type_):
        q = db.session.query(func.coalesce(func.sum(Transaction.amount_idr), 0)).filter(
            Transaction.user_id == user_id, Transaction.type == type_
        )
        if start:
            q = q.filter(Transaction.transaction_date >= start)
        if end:
            q = q.filter(Transaction.transaction_date <= end)
        return _scope(q, type_, source_id)

    total_income = float(base("income").scalar())
    total_expense = float(base("expense").scalar())

    # Pengeluaran per kategori, untuk grafik (ikut filter tanggal)
    cat_q = (
        db.session.query(Category.name, func.sum(Transaction.amount_idr))
        .join(Transaction, Transaction.category_id == Category.id)
        .filter(Transaction.user_id == user_id, Transaction.type == "expense")
    )
    if start:
        cat_q = cat_q.filter(Transaction.transaction_date >= start)
    if end:
        cat_q = cat_q.filter(Transaction.transaction_date <= end)
    cat_q = _scope(cat_q, "expense", source_id)
    rows = cat_q.group_by(Category.name).order_by(func.sum(Transaction.amount_idr).desc()).all()
    by_category = [{"category": name, "total": float(total)} for name, total in rows]

    return jsonify({
        "total_income": total_income,
        "total_expense": total_expense,
        "balance": total_income - total_expense,
        "expense_by_category": by_category,
    }), 200


def _week_start(d: date) -> date:
    return d - timedelta(days=d.weekday())  # Senin


def _buckets(period: str, today: date):
    """Return (list of (key, label), start_date, key_fn)."""
    if period == "day":
        days = [today - timedelta(days=i) for i in range(29, -1, -1)]
        return [(d.isoformat(), d.strftime("%d/%m")) for d in days], days[0], lambda d: d.isoformat()
    if period == "week":
        first = _week_start(today) - timedelta(weeks=11)
        weeks = [first + timedelta(weeks=i) for i in range(12)]
        return (
            [(w.isoformat(), w.strftime("%d/%m")) for w in weeks],
            first,
            lambda d: _week_start(d).isoformat(),
        )
    if period == "month":
        y, m = today.year, today.month
        months = []
        for _ in range(12):
            months.append((y, m))
            m -= 1
            if m == 0:
                m, y = 12, y - 1
        months.reverse()
        return (
            [(f"{y}-{m:02d}", f"{MONTHS_ID[m - 1]} {str(y)[2:]}") for y, m in months],
            date(months[0][0], months[0][1], 1),
            lambda d: f"{d.year}-{d.month:02d}",
        )
    # year: 3 tahun terakhir (sesuai retensi data)
    years = [today.year - 2, today.year - 1, today.year]
    return [(str(y), str(y)) for y in years], date(years[0], 1, 1), lambda d: str(d.year)


@dashboard_bp.route("/trend", methods=["GET"])
@jwt_required()
def trend():
    """Grafik pemasukan vs pengeluaran. ?period=day|week|month|year"""
    user_id = current_user_id()
    period = request.args.get("period", "month")
    source_id = request.args.get("source_id", type=int)
    if period not in ("day", "week", "month", "year"):
        return jsonify({"error": "period harus day, week, month, atau year"}), 400

    today = date.today()
    buckets, start, key_fn = _buckets(period, today)
    start = max(start, retention_cutoff())

    rows = (
        db.session.query(
            Transaction.transaction_date, Transaction.type, Transaction.amount_idr,
            Transaction.category_id, Transaction.source_id,
        )
        .filter(Transaction.user_id == user_id, Transaction.transaction_date >= start)
        .all()
    )
    income, expense = defaultdict(float), defaultdict(float)
    for d, type_, amt, cat_id, src_id in rows:
        if source_id and (cat_id if type_ == "income" else src_id) != source_id:
            continue
        (income if type_ == "income" else expense)[key_fn(d)] += float(amt)

    return jsonify({
        "period": period,
        "labels": [label for _, label in buckets],
        "income": [round(income[k], 2) for k, _ in buckets],
        "expense": [round(expense[k], 2) for k, _ in buckets],
    }), 200


@dashboard_bp.route("/sources", methods=["GET"])
@jwt_required()
def sources():
    """Saldo per sumber dana (kategori pemasukan): masuk, terpakai, sisa."""
    user_id = current_user_id()

    income_rows = dict(
        db.session.query(Transaction.category_id, func.sum(Transaction.amount_idr))
        .filter(Transaction.user_id == user_id, Transaction.type == "income")
        .group_by(Transaction.category_id)
        .all()
    )
    expense_rows = dict(
        db.session.query(Transaction.source_id, func.sum(Transaction.amount_idr))
        .filter(Transaction.user_id == user_id, Transaction.type == "expense", Transaction.source_id.isnot(None))
        .group_by(Transaction.source_id)
        .all()
    )
    unassigned = db.session.query(func.coalesce(func.sum(Transaction.amount_idr), 0)).filter(
        Transaction.user_id == user_id, Transaction.type == "expense", Transaction.source_id.is_(None)
    ).scalar()

    categories = Category.query.filter(
        Category.type == "income", (Category.is_default == True) | (Category.user_id == user_id)  # noqa: E712
    ).order_by(Category.id).all()

    result = []
    for c in categories:
        inc = float(income_rows.get(c.id, 0))
        exp = float(expense_rows.get(c.id, 0))
        result.append({
            "id": c.id,
            "name": c.name,
            "income": inc,
            "expense": exp,
            "balance": round(inc - exp, 2),
            "used_percent": round(exp / inc * 100, 1) if inc else 0,
        })
    return jsonify({"sources": result, "unassigned_expense": float(unassigned)}), 200

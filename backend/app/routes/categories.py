from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from app.utils import current_user_id, json_body
from app import db
from app.models import Category

categories_bp = Blueprint("categories", __name__)


@categories_bp.route("", methods=["GET"])
@jwt_required()
def list_categories():
    user_id = current_user_id()
    # Kategori bawaan (is_default) + kategori buatan user yang login
    categories = Category.query.filter(
        (Category.is_default == True) | (Category.user_id == user_id)  # noqa: E712
    ).all()

    return jsonify([_serialize(c) for c in categories]), 200


@categories_bp.route("", methods=["POST"])
@jwt_required()
def create_category():
    user_id = current_user_id()
    data = json_body()
    name = str(data.get("name") or "").strip()
    type_ = data.get("type")  # "income" atau "expense"

    if not name or type_ not in ("income", "expense"):
        return jsonify({"error": "name dan type (income/expense) wajib diisi"}), 400
    if len(name) > 50:
        return jsonify({"error": "Nama kategori maksimal 50 karakter"}), 400

    exists = Category.query.filter(
        db.func.lower(Category.name) == name.lower(),
        Category.type == type_,
        (Category.is_default == True) | (Category.user_id == user_id),  # noqa: E712
    ).first()
    if exists:
        return jsonify({"error": "Kategori dengan nama itu sudah ada"}), 409

    category = Category(user_id=user_id, name=name, type=type_, is_default=False)
    db.session.add(category)
    db.session.commit()

    return jsonify(_serialize(category)), 201


def _serialize(category: Category):
    return {
        "id": category.id,
        "name": category.name,
        "type": category.type,
        "is_default": category.is_default,
    }

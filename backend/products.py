import sqlite3

from flask import Blueprint, jsonify, request, session

from backend.auth import require_auth
from backend.database import get_db


products_bp = Blueprint("products", __name__, url_prefix="/api")


@products_bp.get("/products")
@require_auth
def list_products():
    rows = get_db().execute(
        "SELECT id, name, description, created_at FROM products WHERE user_id = ? ORDER BY name",
        (session["user_id"],),
    ).fetchall()
    return jsonify([dict(row) for row in rows])


@products_bp.post("/products")
@require_auth
def create_product():
    data = request.get_json(silent=True) or {}
    name = str(data.get("name", "")).strip()
    description = str(data.get("description", "")).strip()
    if not name:
        return jsonify({"error": "Product name is required"}), 400
    db = get_db()
    cursor = db.execute(
        "INSERT INTO products (user_id, name, description) VALUES (?, ?, ?)",
        (session["user_id"], name, description),
    )
    db.commit()
    return jsonify({"id": cursor.lastrowid, "name": name, "description": description}), 201


@products_bp.delete("/products/<int:product_id>")
@require_auth
def delete_product(product_id):
    db = get_db()
    try:
        cursor = db.execute(
            "DELETE FROM products WHERE id = ? AND user_id = ?",
            (product_id, session["user_id"]),
        )
        db.commit()
    except sqlite3.IntegrityError:
        return jsonify({"error": "This product has plans or subscriptions and cannot be deleted"}), 409
    if cursor.rowcount == 0:
        return jsonify({"error": "Product not found"}), 404
    return jsonify({"message": "Product deleted"})


@products_bp.get("/plans")
@require_auth
def list_plans():
    rows = get_db().execute(
        """SELECT plans.id, plans.product_id, plans.name, plans.price,
                  plans.billing_interval, products.name AS product_name
           FROM plans JOIN products ON products.id = plans.product_id
           WHERE products.user_id = ? ORDER BY products.name, plans.price""",
        (session["user_id"],),
    ).fetchall()
    return jsonify([dict(row) for row in rows])


@products_bp.post("/plans")
@require_auth
def create_plan():
    data = request.get_json(silent=True) or {}
    name = str(data.get("name", "")).strip()
    interval = str(data.get("billing_interval", "")).strip().lower()
    try:
        product_id = int(data.get("product_id"))
        price = float(data.get("price"))
    except (TypeError, ValueError):
        return jsonify({"error": "A valid product and price are required"}), 400
    if not name or price < 0 or interval not in {"month", "year"}:
        return jsonify({"error": "Provide a plan name, non-negative price, and month or year interval"}), 400
    db = get_db()
    product = db.execute(
        "SELECT id FROM products WHERE id = ? AND user_id = ?",
        (product_id, session["user_id"]),
    ).fetchone()
    if product is None:
        return jsonify({"error": "Product not found"}), 404
    cursor = db.execute(
        "INSERT INTO plans (product_id, name, price, billing_interval) VALUES (?, ?, ?, ?)",
        (product_id, name, price, interval),
    )
    db.commit()
    return jsonify({"id": cursor.lastrowid, "product_id": product_id, "name": name,
                    "price": price, "billing_interval": interval}), 201


@products_bp.delete("/plans/<int:plan_id>")
@require_auth
def delete_plan(plan_id):
    db = get_db()
    try:
        cursor = db.execute(
            """DELETE FROM plans WHERE id = ? AND product_id IN
               (SELECT id FROM products WHERE user_id = ?)""",
            (plan_id, session["user_id"]),
        )
        db.commit()
    except sqlite3.IntegrityError:
        return jsonify({"error": "This plan has subscriptions and cannot be deleted"}), 409
    if cursor.rowcount == 0:
        return jsonify({"error": "Plan not found"}), 404
    return jsonify({"message": "Plan deleted"})

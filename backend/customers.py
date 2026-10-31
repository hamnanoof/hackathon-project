import sqlite3

from flask import Blueprint, jsonify, request, session

from backend.auth import require_auth
from backend.database import get_db


customers_bp = Blueprint("customers", __name__, url_prefix="/api/customers")


@customers_bp.get("")
@require_auth
def list_customers():
    rows = get_db().execute(
        "SELECT id, name, email, phone, address, created_at FROM customers WHERE user_id = ? ORDER BY name",
        (session["user_id"],),
    ).fetchall()
    return jsonify([dict(row) for row in rows])


@customers_bp.post("")
@require_auth
def create_customer():
    data = request.get_json(silent=True) or {}
    name = str(data.get("name", "")).strip()
    email = str(data.get("email", "")).strip().lower()
    phone = str(data.get("phone", "")).strip()
    address = str(data.get("address", "")).strip()
    if not name or not email:
        return jsonify({"error": "Name and email are required"}), 400
    db = get_db()
    try:
        cursor = db.execute(
            "INSERT INTO customers (user_id, name, email, phone, address) VALUES (?, ?, ?, ?, ?)",
            (session["user_id"], name, email, phone or None, address or None),
        )
        db.commit()
    except sqlite3.IntegrityError as error:
        if "UNIQUE constraint failed" in str(error):
            return jsonify({"error": "A customer with this email already exists"}), 409
        raise
    return jsonify({"id": cursor.lastrowid, "name": name, "email": email, "phone": phone, "address": address}), 201


@customers_bp.patch("/<int:customer_id>")
@require_auth
def update_customer(customer_id):
    data = request.get_json(silent=True) or {}
    name = str(data.get("name", "")).strip()
    email = str(data.get("email", "")).strip().lower()
    phone = str(data.get("phone", "")).strip()
    address = str(data.get("address", "")).strip()
    if not name or not email:
        return jsonify({"error": "Name and email are required"}), 400
    db = get_db()
    try:
        cursor = db.execute(
            """UPDATE customers
               SET name = ?, email = ?, phone = ?, address = ?
               WHERE id = ? AND user_id = ?""",
            (name, email, phone or None, address or None, customer_id, session["user_id"]),
        )
        db.commit()
    except sqlite3.IntegrityError as error:
        if "UNIQUE constraint failed" in str(error):
            return jsonify({"error": "A customer with this email already exists"}), 409
        raise
    if cursor.rowcount == 0:
        return jsonify({"error": "Customer not found"}), 404
    return jsonify({"id": customer_id, "name": name, "email": email, "phone": phone, "address": address})


@customers_bp.delete("/<int:customer_id>")
@require_auth
def delete_customer(customer_id):
    db = get_db()
    try:
        cursor = db.execute(
            "DELETE FROM customers WHERE id = ? AND user_id = ?",
            (customer_id, session["user_id"]),
        )
        db.commit()
    except sqlite3.IntegrityError:
        return jsonify({"error": "This customer has subscriptions and cannot be deleted"}), 409
    if cursor.rowcount == 0:
        return jsonify({"error": "Customer not found"}), 404
    return jsonify({"message": "Customer deleted"})

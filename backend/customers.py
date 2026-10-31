
import sqlite3

from flask import Blueprint, jsonify, request, session

from werkzeug.security import generate_password_hash

from backend.auth import require_role
from backend.database import get_db


customers_bp = Blueprint("customers", __name__, url_prefix="/api/customers")


# View customers belonging to the logged-in business
@customers_bp.get("")
@require_role("admin", "staff")
def list_customers():

    rows = get_db().execute(
        """SELECT id, name, email, phone, address, account_id, created_at
           FROM customers
           WHERE user_id = ?
           ORDER BY name""",
        (session["user_id"],),
    ).fetchall()

    return jsonify([dict(row) for row in rows])


# Create a customer and their login account
@customers_bp.post("")
@require_role("admin", "staff")
def create_customer():

    data = request.get_json(silent=True) or {}

    name = str(data.get("name", "")).strip()
    email = str(data.get("email", "")).strip().lower()
    password = str(data.get("password", ""))
    phone = str(data.get("phone", "")).strip()
    address = str(data.get("address", "")).strip()

    if not name or not email or len(password) < 8:
        return jsonify({
            "error": "Name, email, and a password of at least 8 characters are required"
        }), 400

    db = get_db()

    # Check whether this email already has a login account
    existing_user = db.execute(
        "SELECT id FROM users WHERE email = ?",
        (email,),
    ).fetchone()

    if existing_user:
        return jsonify({
            "error": "An account with this email already exists"
        }), 409

    try:
        # Create customer login account
        user_cursor = db.execute(
            """INSERT INTO users (name, email, password_hash, role)
               VALUES (?, ?, ?, 'customer')""",
            (name, email, generate_password_hash(password)),
        )

        account_id = user_cursor.lastrowid

        # Create customer record linked to the login account
        customer_cursor = db.execute(
            """INSERT INTO customers
               (user_id, account_id, name, email, phone, address)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (
                session["user_id"],
                account_id,
                name,
                email,
                phone or None,
                address or None,
            ),
        )

        db.commit()

    except sqlite3.IntegrityError:
        db.rollback()
        return jsonify({
            "error": "Could not create customer. Check whether this email already exists."
        }), 409

    return jsonify({
        "id": customer_cursor.lastrowid,
        "account_id": account_id,
        "name": name,
        "email": email,
        "phone": phone,
        "address": address,
        "message": "Customer and login account created successfully"
    }), 201


# Update customer details
@customers_bp.patch("/<int:customer_id>")
@require_role("admin", "staff")
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
        customer = db.execute(
            """SELECT account_id FROM customers
               WHERE id = ? AND user_id = ?""",
            (customer_id, session["user_id"]),
        ).fetchone()

        if customer is None:
            return jsonify({"error": "Customer not found"}), 404

        db.execute(
            """UPDATE customers
               SET name = ?, email = ?, phone = ?, address = ?
               WHERE id = ? AND user_id = ?""",
            (
                name, email, phone or None, address or None,
                customer_id, session["user_id"]
            ),
        )

        # Keep the customer's login details in sync
        if customer["account_id"] is not None:
            db.execute(
                """UPDATE users
                   SET name = ?, email = ?
                   WHERE id = ? AND role = 'customer'""",
                (name, email, customer["account_id"]),
            )

        db.commit()

    except sqlite3.IntegrityError:
        db.rollback()
        return jsonify({
            "error": "A customer or login account with this email already exists"
        }), 409

    return jsonify({
        "id": customer_id,
        "name": name,
        "email": email,
        "phone": phone,
        "address": address,
        "message": "Customer updated successfully"
    })


# Delete a customer record
@customers_bp.delete("/<int:customer_id>")
@require_role("admin", "staff")
def delete_customer(customer_id):

    db = get_db()

    try:
        cursor = db.execute(
            """DELETE FROM customers
               WHERE id = ? AND user_id = ?""",
            (customer_id, session["user_id"]),
        )

        db.commit()

    except sqlite3.IntegrityError:
        db.rollback()
        return jsonify({
            "error": "This customer has subscriptions and cannot be deleted"
        }), 409

    if cursor.rowcount == 0:
        return jsonify({"error": "Customer not found"}), 404

    return jsonify({
        "message": "Customer record deleted"
    })

from functools import wraps
import sqlite3

from flask import Blueprint, jsonify, request, session
from werkzeug.security import check_password_hash, generate_password_hash

from backend.database import get_db


auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")


def require_auth(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if "user_id" not in session:
            return jsonify({"error": "Authentication required"}), 401
        return view(*args, **kwargs)

    return wrapped


@auth_bp.post("/register")
def register():
    data = request.get_json(silent=True) or {}
    name = str(data.get("name", "")).strip()
    email = str(data.get("email", "")).strip().lower()
    password = str(data.get("password", ""))
    if not name or not email or len(password) < 8:
        return jsonify({"error": "Name, email, and a password of at least 8 characters are required"}), 400

    db = get_db()
    try:
        cursor = db.execute(
            "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
            (name, email, generate_password_hash(password)),
        )
        db.commit()
    except sqlite3.IntegrityError as error:
        if "UNIQUE constraint failed" in str(error):
            return jsonify({"error": "An account with this email already exists"}), 409
        raise
    session["user_id"] = cursor.lastrowid
    return jsonify({"id": cursor.lastrowid, "name": name, "email": email}), 201


@auth_bp.post("/login")
def login():
    data = request.get_json(silent=True) or {}
    email = str(data.get("email", "")).strip().lower()
    password = str(data.get("password", ""))
    user = get_db().execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
    if user is None or not check_password_hash(user["password_hash"], password):
        return jsonify({"error": "Invalid email or password"}), 401
    session.clear()
    session["user_id"] = user["id"]
    return jsonify({"id": user["id"], "name": user["name"], "email": user["email"]})


@auth_bp.post("/logout")
def logout():
    session.clear()
    return jsonify({"message": "Logged out"})


@auth_bp.get("/me")
@require_auth
def me():
    user = get_db().execute(
        "SELECT id, name, email FROM users WHERE id = ?", (session["user_id"],)
    ).fetchone()
    if user is None:
        session.clear()
        return jsonify({"error": "Account not found"}), 401
    return jsonify(dict(user))

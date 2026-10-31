
from functools import wraps
import sqlite3
import re

from flask import Blueprint, jsonify, request, session
from werkzeug.security import check_password_hash, generate_password_hash

from backend.database import get_db
from backend.errors import ApiError


auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")


# Check whether the user is logged in
def require_auth(view):
    @wraps(view)
    def wrapped(*args, **kwargs):

        if "user_id" not in session:
            raise ApiError("Authentication required", 401)

        return view(*args, **kwargs)

    return wrapped


# Check user role and permissions
def require_role(*allowed_roles):
    def decorator(view):

        @wraps(view)
        @require_auth
        def wrapped(*args, **kwargs):

            user = get_db().execute(
                "SELECT role FROM users WHERE id = ?",
                (session["user_id"],)
            ).fetchone()

            if user is None:
                session.clear()
                raise ApiError("Account not found", 401)

            if user["role"] not in allowed_roles:
                raise ApiError("Permission denied", 403)

            return view(*args, **kwargs)

        return wrapped

    return decorator


# User registration
@auth_bp.post("/register")
def register():

    data = request.get_json(silent=True) or {}

    name = str(data.get("name", "")).strip()
    email = str(data.get("email", "")).strip().lower()
    password = str(data.get("password", ""))

    # Password strength validation
    if len(password) < 8:
        raise ApiError("Password must be at least 8 characters long", 400)
    if not re.search(r'[A-Z]', password):
        raise ApiError("Password must contain at least one uppercase letter", 400)
    if not re.search(r'[a-z]', password):
        raise ApiError("Password must contain at least one lowercase letter", 400)
    if not re.search(r'\d', password):
        raise ApiError("Password must contain at least one digit", 400)
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        raise ApiError("Password must contain at least one special character", 400)

    if not name or not email:
        raise ApiError("Name and email are required", 400)

    db = get_db()

    # Check if this is the first user
    user_count = db.execute("SELECT COUNT(*) as count FROM users").fetchone()["count"]
    role = "admin" if user_count == 0 else "customer"

    try:
        cursor = db.execute(
            """INSERT INTO users
               (name, email, password_hash, role)
               VALUES (?, ?, ?, ?)""",
            (name, email, generate_password_hash(password), role)
        )

        db.commit()

    except sqlite3.IntegrityError:
        raise ApiError("An account with this email already exists", 409)

    session.clear()
    session["user_id"] = cursor.lastrowid

    return jsonify({
        "id": cursor.lastrowid,
        "name": name,
        "email": email,
        "role": role
    }), 201


# User login
@auth_bp.post("/login")
def login():

    data = request.get_json(silent=True) or {}

    email = str(data.get("email", "")).strip().lower()
    password = str(data.get("password", ""))

    user = get_db().execute(
        "SELECT * FROM users WHERE email = ?",
        (email,)
    ).fetchone()

    if user is None or not check_password_hash(
        user["password_hash"], password
    ):
        raise ApiError("Invalid email or password", 401)

    session.clear()
    session["user_id"] = user["id"]

    return jsonify({
        "id": user["id"],
        "name": user["name"],
        "email": user["email"],
        "role": user["role"]
    })


# User logout
@auth_bp.post("/logout")
def logout():

    session.clear()

    return jsonify({
        "message": "Logged out"
    })


# Get currently logged-in user details
@auth_bp.get("/me")
@require_auth
def me():

    user = get_db().execute(
        """SELECT id, name, email, role
           FROM users
           WHERE id = ?""",
        (session["user_id"],)
    ).fetchone()

    if user is None:
        session.clear()
        raise ApiError("Account not found", 401)

    return jsonify(dict(user))

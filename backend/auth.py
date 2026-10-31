
from functools import wraps

from flask import Blueprint, jsonify, request, session
from werkzeug.security import check_password_hash

from backend.database import get_db


auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")


# Check whether the user is logged in
def require_auth(view):
    @wraps(view)
    def wrapped(*args, **kwargs):

        if "user_id" not in session:
            return jsonify({"error": "Authentication required"}), 401

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
                return jsonify({"error": "Account not found"}), 401

            if user["role"] not in allowed_roles:
                return jsonify({"error": "Permission denied"}), 403

            return view(*args, **kwargs)

        return wrapped

    return decorator


# Public registration is disabled.
# Admin/staff create customer accounts instead.
@auth_bp.post("/register")
def register():

    return jsonify({
        "error": "Registration is disabled. Contact your administrator."
    }), 403


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
        return jsonify({
            "error": "Invalid email or password"
        }), 401

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

        return jsonify({
            "error": "Account not found"
        }), 401

    return jsonify(dict(user))


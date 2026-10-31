from functools import wraps
from flask import session, jsonify
from backend.errors import ApiError


def require_role(*allowed_roles):
    def decorator(view):
        @wraps(view)
        def wrapped(*args, **kwargs):
            if "user_id" not in session:
                raise ApiError("Authentication required", 401)
            db = __import__('backend.database', fromlist=['get_db']).get_db()
            user = db.execute(
                "SELECT role FROM users WHERE id = ?",
                (session["user_id"],)
            ).fetchone()
            if user is None or user["role"] not in allowed_roles:
                raise ApiError("Insufficient permissions", 403)
            return view(*args, **kwargs)
        return wrapped
    return decorator


def paginate(query, params, page=1, page_size=20):
    from backend.database import get_db
    db = get_db()

    offset = (page - 1) * page_size

    # Get total count
    count_query = f"SELECT COUNT(*) as total FROM ({query}) as subq"
    total = db.execute(count_query, params).fetchone()["total"]

    # Get paginated items
    paginated_query = f"{query} LIMIT ? OFFSET ?"
    items = db.execute(paginated_query, params + [page_size, offset]).fetchall()

    pages = (total + page_size - 1) // page_size if total > 0 else 1

    return {
        "items": [dict(row) for row in items],
        "total": total,
        "page": page,
        "page_size": page_size,
        "pages": pages
    }

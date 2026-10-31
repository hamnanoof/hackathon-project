from flask import Flask, jsonify, send_from_directory

from backend import config
from backend.auth import auth_bp
from backend.customers import customers_bp
from backend.database import init_db
from backend.invoices import invoices_bp
from backend.payments import payments_bp
from backend.products import products_bp
from backend.subscriptions import subscriptions_bp


def create_app():
    app = Flask(__name__, static_folder=None)
    app.config.from_object(config)
    app.config["BASE_DIR"] = str(config.BASE_DIR)
    app.config["DATABASE_PATH"] = str(config.DATABASE_PATH)
    app.config["SESSION_COOKIE_HTTPONLY"] = True
    app.config["SESSION_COOKIE_SAMESITE"] = "Lax"

    init_db(app)
    app.register_blueprint(auth_bp)
    app.register_blueprint(customers_bp)
    app.register_blueprint(products_bp)
    app.register_blueprint(subscriptions_bp)
    app.register_blueprint(invoices_bp)
    app.register_blueprint(payments_bp)

    @app.get("/api/dashboard")
    def dashboard():
        from flask import session

        if "user_id" not in session:
            return jsonify({"error": "Authentication required"}), 401
        from backend.database import get_db

        db = get_db()
        user_id = session["user_id"]
        counts = db.execute(
            """SELECT
                (SELECT COUNT(*) FROM products WHERE user_id = ?) AS products,
                (SELECT COUNT(*) FROM customers WHERE user_id = ?) AS customers,
                (SELECT COUNT(*) FROM subscriptions WHERE user_id = ? AND status = 'active') AS active_subscriptions,
                (SELECT COUNT(*) FROM invoices WHERE user_id = ? AND status = 'pending') AS pending_invoices,
                (SELECT COALESCE(SUM(amount), 0) FROM payments WHERE user_id = ? AND status = 'completed') AS collected
            """,
            (user_id, user_id, user_id, user_id, user_id),
        ).fetchone()
        return jsonify(dict(counts))

    @app.get("/")
    def index():
        return send_from_directory(config.FRONTEND_DIR, "index.html")

    @app.get("/<path:filename>")
    def frontend_file(filename):
        return send_from_directory(config.FRONTEND_DIR, filename)

    return app


app = create_app()


if __name__ == "__main__":
    app.run(debug=True)


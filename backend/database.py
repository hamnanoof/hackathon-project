import sqlite3
from pathlib import Path

from flask import current_app, g


def get_db():
    if "db" not in g:
        db_path = Path(current_app.config["DATABASE_PATH"])
        db_path.parent.mkdir(parents=True, exist_ok=True)
        g.db = sqlite3.connect(db_path)
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db


def close_db(_error=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db(app):
    app.teardown_appcontext(close_db)
    with app.app_context():
        db = get_db()
        schema_path = Path(app.config["BASE_DIR"]) / "database" / "schema.sql"
        db.executescript(schema_path.read_text(encoding="utf-8"))
        db.commit()
        migrate_db(db)


def migrate_db(db):
    # Create the customer table for existing databases.
    db.execute("""
        CREATE TABLE IF NOT EXISTS customers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            phone TEXT,
            address TEXT,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id, email)
        )
    """)

    # Check whether subscriptions already have customer_id.
    columns = [
        row["name"]
        for row in db.execute("PRAGMA table_info(subscriptions)").fetchall()
    ]

    if "customer_id" not in columns:
        db.execute("""
            ALTER TABLE subscriptions
            ADD COLUMN customer_id INTEGER REFERENCES customers(id)
        """)

    db.execute("""
        CREATE INDEX IF NOT EXISTS idx_customers_user
        ON customers(user_id)
    """)

    db.execute("""
        CREATE INDEX IF NOT EXISTS idx_subscriptions_customer
        ON subscriptions(customer_id)
    """)

    db.commit()

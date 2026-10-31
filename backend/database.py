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

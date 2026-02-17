from flask import Flask
import os
import psycopg2
import sqlalchemy

# ✅ ADD THIS LINE
DATABASE_URL = os.environ.get("DATABASE_URL")

def create_app():
    base_dir = os.path.abspath(os.path.dirname(__file__))
    template_dir = os.path.join(base_dir, "..", "templates")
    static_dir = os.path.join(base_dir, "..", "static")

    app = Flask(
        __name__,
        template_folder=template_dir,
        static_folder=static_dir
    )

    from .routes import main
    app.register_blueprint(main)

    return app


def init_db():
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS anime (
        id SERIAL PRIMARY KEY,
        name TEXT,
        genres TEXT
    )
    """)

    conn.commit()
    cur.close()
    conn.close()


init_db()

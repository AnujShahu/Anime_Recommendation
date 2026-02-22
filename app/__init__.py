from flask import Flask
from flask_caching import Cache
from flask_login import LoginManager
import os
import logging

cache = Cache()
login_manager = LoginManager()

def create_app():
    base_dir = os.path.abspath(os.path.dirname(__file__))

    template_dir = os.path.join(base_dir, "..", "templates")
    static_dir = os.path.join(base_dir, "..", "static")

    app = Flask(
        __name__,
        template_folder=template_dir,
        static_folder=static_dir
    )

    # ================= SECRET KEY =================
    app.config["SECRET_KEY"] = "super-secret-key-change-this"

    # ================= CACHE CONFIG =================
    app.config["CACHE_TYPE"] = "simple"
    app.config["CACHE_DEFAULT_TIMEOUT"] = 300
    cache.init_app(app)

    # ================= LOGIN MANAGER =================
    login_manager.init_app(app)
    login_manager.login_view = "auth.login"

    # ================= LOGGING =================
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s"
    )

    # ================= INIT USER DATABASE =================
    # This will create user_info.db automatically if it doesn't exist
    from .user_service import init_user_db
    init_user_db()

    # ================= REGISTER BLUEPRINTS =================
    from .routes import main
    from .auth import auth

    app.register_blueprint(main)
    app.register_blueprint(auth)

    return app
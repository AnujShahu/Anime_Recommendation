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

    # 🔐 SECRET KEY (NEW)
    app.config["SECRET_KEY"] = "super-secret-key-change-this"

    # 🔥 Cache Configuration (UNCHANGED)
    app.config["CACHE_TYPE"] = "simple"
    app.config["CACHE_DEFAULT_TIMEOUT"] = 300
    cache.init_app(app)

    # 🔐 Login Manager Init (NEW)
    login_manager.init_app(app)
    login_manager.login_view = "auth.login"

    # 🔥 Logging Configuration (UNCHANGED)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s"
    )

    from .routes import main
    from .auth import auth   # NEW

    app.register_blueprint(main)
    app.register_blueprint(auth)  # NEW

    return app
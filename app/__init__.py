from flask import Flask
from flask_caching import Cache
import os
import logging

cache = Cache()

def create_app():
    base_dir = os.path.abspath(os.path.dirname(__file__))

    template_dir = os.path.join(base_dir, "..", "templates")
    static_dir = os.path.join(base_dir, "..", "static")

    app = Flask(
        __name__,
        template_folder=template_dir,
        static_folder=static_dir
    )

    # 🔥 Cache Configuration
    app.config["CACHE_TYPE"] = "simple"
    app.config["CACHE_DEFAULT_TIMEOUT"] = 300
    cache.init_app(app)

    # 🔥 Logging Configuration
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s"
    )

    from .routes import main
    app.register_blueprint(main)

    return app

from flask import Flask, send_from_directory
from flask_cors import CORS
from config import Config
from extensions import db
from routes import register_blueprints
from blockchain import init_genesis_block_if_needed


def create_app():
    app = Flask(__name__, static_folder="static", static_url_path="")
    app.config.from_object(Config)
    CORS(app, supports_credentials=True)

    db.init_app(app)
    register_blueprints(app)

    with app.app_context():
        db.create_all()  # for local dev; use real migrations (Flask-Migrate) in production
        init_genesis_block_if_needed()

    @app.route("/api/health")
    def health():
        return {"status": "ok"}

    @app.route("/")
    def index():
        return send_from_directory(app.static_folder, "index.html")

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True, port=5000)

"""
backend/app.py
Flask application entry point.

Chạy từ repository root: python -m backend.app
Server: http://localhost:8080
"""

from flask import Flask
from flask_cors import CORS
from backend.api.game_controller import game_bp


def create_app() -> Flask:
    app = Flask(__name__)

    # Cho phép frontend (localhost:3000) gọi API
    CORS(app, origins=["http://localhost:3000"])

    # Đăng ký blueprint
    app.register_blueprint(game_bp)

    # Health check
    @app.route("/health")
    def health():
        return {"status": "ok", "service": "chess-ai-backend"}

    return app


if __name__ == "__main__":
    app = create_app()
    print("Chess AI Backend running at http://localhost:8080")
    app.run(host="0.0.0.0", port=8080, debug=True)

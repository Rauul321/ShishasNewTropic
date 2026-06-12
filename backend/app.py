from flask import Flask
from flask_cors import CORS

from routes.auth import auth_bp
from routes.bonos import bonos_bp
from routes.scan import scan_bp


def create_app():
    app = Flask(__name__)
    CORS(app)

    app.register_blueprint(auth_bp)
    app.register_blueprint(bonos_bp)
    app.register_blueprint(scan_bp)

    return app


app = create_app()


if __name__ == "__main__":
    app.run(debug=True, port=5000)
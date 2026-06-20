import os

from flask import Flask, jsonify
from flask_cors import CORS

from routes.auth import auth_bp
from routes.bonos import bonos_bp
from routes.scan import scan_bp


def create_app():
    app = Flask(__name__)
    CORS(app)

    @app.get("/health")
    def health_check():
        return {"status": "ok"}, 200

    app.register_blueprint(auth_bp)
    app.register_blueprint(bonos_bp)
    app.register_blueprint(scan_bp)

    return app


app = create_app()

@app.route('/ping', methods=['GET'])
def ping():
    # Devolvemos un JSON vacío (o un texto) y el código de estado 200
    return jsonify({"status": "OK"}), 200


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=int(os.getenv("PORT", 5000)))
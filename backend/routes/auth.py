from flask import Blueprint, jsonify, request

from core.auth import ADMIN_PASSWORD, generate_token


auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/login", methods=["POST", "OPTIONS"])
def login():
    if request.method == "OPTIONS":
        return "", 200

    data = request.json or {}
    password = data.get("password")

    if not password:
        return jsonify({"error": "Se requiere contraseña"}), 400

    if password == ADMIN_PASSWORD:
        token = generate_token("admin", role="admin")
        return jsonify({"token": token})

    return jsonify({"error": "Contraseña incorrecta"}), 401

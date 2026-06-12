import os
from functools import wraps

from dotenv import load_dotenv
from flask import jsonify, request
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer


load_dotenv()

SECRET_KEY = os.getenv("JWT_SECRET", "super-secret-key-change-me-39824u923")
serializer = URLSafeTimedSerializer(SECRET_KEY)
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")


def generate_token(username, role="staff"):
    return serializer.dumps({"username": username, "role": role})


def verify_token(token):
    try:
        return serializer.loads(token, max_age=604800)
    except (SignatureExpired, BadSignature):
        return None


def requires_auth(_func=None, *, allowed_roles=None):
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if request.method == "OPTIONS":
                return f(*args, **kwargs)

            auth_header = request.headers.get("Authorization")
            if not auth_header or not auth_header.startswith("Bearer "):
                return jsonify({"error": "No autorizado. Token faltante."}), 401

            token = auth_header.split(" ")[1]
            user_data = verify_token(token)
            if not user_data:
                return jsonify({"error": "No autorizado. Token inválido o expirado."}), 401

            if allowed_roles and user_data.get("role") not in allowed_roles:
                return jsonify({"error": "No autorizado. Rol insuficiente."}), 403

            return f(*args, **kwargs)

        return decorated

    if _func is not None:
        return decorator(_func)

    return decorator

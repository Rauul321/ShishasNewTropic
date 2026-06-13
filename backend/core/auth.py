import os
from functools import wraps
from pathlib import Path

from dotenv import load_dotenv
from flask import jsonify, request
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer


BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

SECRET_KEY = os.getenv("JWT_SECRET")
serializer = URLSafeTimedSerializer(SECRET_KEY)
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD")
SCAN_TOKEN_MAX_AGE = int(os.getenv("SCAN_TOKEN_MAX_AGE", "604800"))


def generate_token(username, role="staff"):
    return serializer.dumps({"username": username, "role": role})


def verify_token(token):
    try:
        return serializer.loads(token, max_age=604800)
    except (SignatureExpired, BadSignature):
        return None


def generate_scan_token(bono_id):
    return serializer.dumps({"bono_id": bono_id, "scope": "scan"})


def verify_scan_token(token, bono_id):
    if not token:
        return False

    try:
        payload = serializer.loads(token, max_age=SCAN_TOKEN_MAX_AGE)
    except (SignatureExpired, BadSignature):
        return False

    return payload.get("scope") == "scan" and payload.get("bono_id") == bono_id


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

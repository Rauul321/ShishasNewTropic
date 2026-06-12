from datetime import datetime

from flask import Blueprint, jsonify, request, send_file

from core.auth import requires_auth
from services.pdf_service import generate_pdf
from services.supabase_service import create_bono_db, get_all_bonos, get_bono, supabase


bonos_bp = Blueprint("bonos", __name__)


@bonos_bp.route("/crear_bono", methods=["POST", "OPTIONS"])
@requires_auth(allowed_roles=["admin"])
def crear_bono():
    if request.method == "OPTIONS":
        return "", 200

    if supabase is None:
        return jsonify({"error": "Supabase no está configurado en el servidor"}), 500

    data = request.json or {}
    cliente = data.get("cliente", "").strip()
    telefono = data.get("telefono", "").strip()
    usos = int(data.get("usos", 1))
    base_url = data.get("base_url", "https://shishasnewtropic.onrender.com")

    if not cliente or usos < 1:
        return jsonify({"error": "Datos inválidos"}), 400

    import uuid

    bono_id = str(uuid.uuid4())[:12].upper()
    fecha_dt = datetime.now()
    fecha_iso = fecha_dt.isoformat()
    fecha_str = fecha_dt.strftime("%d/%m/%Y %H:%M")

    success = create_bono_db(bono_id, cliente, telefono, usos, fecha_iso)
    if not success:
        return jsonify({"error": "Error al registrar el bono en base de datos"}), 500

    pdf_path = generate_pdf(bono_id, cliente, telefono, usos, usos, fecha_str, base_url)
    filename = f"bono_{cliente.replace(' ', '_')}_{bono_id}.pdf"

    return send_file(pdf_path, as_attachment=True, download_name=filename, mimetype="application/pdf")


@bonos_bp.route("/bonos", methods=["GET", "OPTIONS"])
@requires_auth(allowed_roles=["admin"])
def listar_bonos():
    if request.method == "OPTIONS":
        return "", 200

    bonos = get_all_bonos()
    return jsonify(bonos)


@bonos_bp.route("/bono/<bono_id>/pdf", methods=["POST", "OPTIONS"])
@requires_auth(allowed_roles=["admin"])
def reprint_pdf(bono_id):
    if request.method == "OPTIONS":
        return "", 200

    b = get_bono(bono_id)
    if not b:
        return jsonify({"error": "No encontrado"}), 404

    base_url = (request.json or {}).get("base_url", "https://shishasnewtropic.onrender.com")
    pdf_path = generate_pdf(
        bono_id,
        b["cliente"],
        b.get("telefono", ""),
        b["usos_totales"],
        b["usos_restantes"],
        b["fecha_compra"],
        base_url,
    )

    return send_file(pdf_path, as_attachment=True, download_name=f"bono_{bono_id}.pdf", mimetype="application/pdf")

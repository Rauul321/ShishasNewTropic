from datetime import datetime

from flask import Blueprint

from core.auth import requires_auth
from services.supabase_service import get_bono, update_bono_usages, supabase


scan_bp = Blueprint("scan", __name__)


@scan_bp.route("/scan/<bono_id>", methods=["GET", "OPTIONS"])
@requires_auth(allowed_roles=["admin", "staff"])
def scan_bono(bono_id):
    if supabase is None:
        return "<h1>Supabase no está configurado en el servidor.</h1>", 500

    bono = get_bono(bono_id)
    if not bono:
        return _scan_page(None, bono_id, "not_found")

    if bono["usos_restantes"] <= 0:
        return _scan_page(bono, bono_id, "agotado")

    nuevos_usos = bono["usos_restantes"] - 1
    historial = bono.get("historial") or []
    historial.append(datetime.now().strftime("%d/%m/%Y %H:%M:%S"))

    success = update_bono_usages(bono_id, nuevos_usos, historial)
    if not success:
        return "<h1>Error al canjear el bono en la base de datos.</h1>", 500

    bono["usos_restantes"] = nuevos_usos
    bono["historial"] = historial

    return _scan_page(bono, bono_id, "ok")


def _scan_page(bono, bono_id, status):
    status_title = ""
    status_desc = ""
    status_class = ""
    icon = ""
    extra_html = ""

    if status == "not_found":
        status_title = "Bono no encontrado"
        status_desc = f"El código del bono <strong>{bono_id}</strong> no existe en el sistema de New Tropic."
        status_class = "error"
        icon = "✕"
    elif status == "agotado":
        status_title = "Bono agotado"
        status_desc = f"El bono de <strong>{bono['cliente']}</strong> ya no tiene usos disponibles."
        status_class = "warning"
        icon = "⚠"
        extra_html = f"""
        <div class="info-row">
            <span>Cliente:</span>
            <strong>{bono['cliente']}</strong>
        </div>
        <div class="info-row">
            <span>Usos Totales:</span>
            <strong>{bono['usos_totales']}</strong>
        </div>
        """
    else:
        status_title = "Uso canjeado con éxito"
        status_desc = f"Se ha registrado el uso de una cachimba correctamente."
        status_class = "success"
        icon = "✓"
        extra_html = f"""
        <div class="info-row">
            <span>Cliente:</span>
            <strong>{bono['cliente']}</strong>
        </div>
        <div class="info-row">
            <span>Usos restantes:</span>
            <strong class="highlight">{bono['usos_restantes']} de {bono['usos_totales']}</strong>
        </div>
        """

    html = f"""
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Canje de Bono · New Tropic</title>
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
        <style>
            :root {{
                --bg: #080808;
                --card-bg: #111111;
                --border: rgba(255, 255, 255, 0.08);
                --text-main: #ffffff;
                --text-dim: #999999;

                --color-success: #ffffff;
                --color-warning: #707070;
                --color-error: #555555;
            }}
            * {{
                margin: 0; padding: 0; box-sizing: border-box;
            }}
            body {{
                background: var(--bg);
                color: var(--text-main);
                font-family: 'Inter', sans-serif;
                display: flex;
                align-items: center;
                justify-content: center;
                min-height: 100vh;
                padding: 24px;
                overflow-x: hidden;
            }}
            body::before {{
                content: '';
                position: fixed; inset: 0; z-index: 0; pointer-events: none;
                opacity: .02;
                background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noise'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noise)'/%3E%3C/svg%3E");
                background-repeat: repeat;
                background-size: 128px;
            }}
            .card {{
                background: var(--card-bg);
                border: 1px solid var(--border);
                border-radius: 12px;
                padding: 40px 32px;
                width: 100%;
                max-width: 420px;
                text-align: center;
                box-shadow: 0 20px 40px rgba(0,0,0,0.5);
                position: relative;
                z-index: 1;
            }}
            .logo {{
                font-size: 12px;
                letter-spacing: 4px;
                text-transform: uppercase;
                color: var(--text-dim);
                margin-bottom: 32px;
                font-weight: 600;
            }}
            .icon-wrapper {{
                width: 72px;
                height: 72px;
                border-radius: 50%;
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 32px;
                margin: 0 auto 24px;
                border: 1px solid var(--border);
            }}
            .icon-wrapper.success {{
                background: var(--text-main);
                color: var(--bg);
                box-shadow: 0 0 20px rgba(255,255,255,0.1);
            }}
            .icon-wrapper.warning {{
                background: #1a1a1a;
                color: #ffcc00;
                border-color: rgba(255, 204, 0, 0.2);
            }}
            .icon-wrapper.error {{
                background: #1a1a1a;
                color: #ff3333;
                border-color: rgba(255, 51, 51, 0.2);
            }}
            h1 {{
                font-size: 20px;
                font-weight: 600;
                margin-bottom: 12px;
                letter-spacing: -0.3px;
            }}
            .desc {{
                color: var(--text-dim);
                font-size: 14px;
                line-height: 1.5;
                margin-bottom: 32px;
            }}
            .info-box {{
                border-top: 1px solid var(--border);
                padding-top: 24px;
                text-align: left;
            }}
            .info-row {{
                display: flex;
                justify-content: space-between;
                font-size: 14px;
                margin-bottom: 12px;
            }}
            .info-row:last-child {{
                margin-bottom: 0;
            }}
            .info-row span {{
                color: var(--text-dim);
            }}
            .info-row strong {{
                color: var(--text-main);
                font-weight: 500;
            }}
            .info-row strong.highlight {{
                font-weight: 600;
            }}
            .footer {{
                margin-top: 40px;
                font-size: 10px;
                color: var(--text-dim);
                letter-spacing: 1px;
                text-transform: uppercase;
            }}
        </style>
    </head>
    <body>
        <div class="card">
            <div class="logo">NEW TROPIC</div>
            <div class="icon-wrapper {status_class}">{icon}</div>
            <h1>{status_title}</h1>
            <p class="desc">{status_desc}</p>

            {f'<div class="info-box">{extra_html}</div>' if extra_html else ''}

            <div class="footer">
                Bono ID: {bono_id}
            </div>
        </div>
    </body>
    </html>
    """
    return html

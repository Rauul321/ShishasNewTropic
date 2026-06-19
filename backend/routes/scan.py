from datetime import datetime

from flask import Blueprint, jsonify, render_template_string, request

from core.auth import verify_scan_token, verify_token
from services.supabase_service import get_bono, update_bono_usages, supabase


scan_bp = Blueprint("scan", __name__)


@scan_bp.route("/scan/<bono_id>", methods=["GET", "POST", "OPTIONS"])
def scan_bono(bono_id):
    if request.method == "OPTIONS":
        return "", 200

    if supabase is None:
        return "<h1>Supabase no está configurado en el servidor.</h1>", 500

    if request.method == "GET":
        return _scan_page(bono_id)

    scan_token = request.args.get("token")
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return jsonify({"error": "No autorizado. Debes iniciar sesión una vez en este dispositivo."}), 401

    user_data = verify_token(auth_header.split(" ", 1)[1])
    if not user_data or user_data.get("role") not in {"admin", "staff"}:
        return jsonify({"error": "No autorizado. Token inválido o expirado."}), 401

    if not verify_scan_token(scan_token, bono_id):
        return jsonify({"error": "Token del QR inválido o expirado."}), 401

    bono = get_bono(bono_id)
    if not bono:
        return jsonify({"error": "Bono no encontrado"}), 404

    if bono["usos_restantes"] <= 0:
        return jsonify({"error": "Bono agotado", "cliente": bono["cliente"], "usos_totales": bono["usos_totales"]}), 409

    nuevos_usos = bono["usos_restantes"] - 1
    historial = bono.get("historial") or []
    historial.append(datetime.now().strftime("%d/%m/%Y %H:%M:%S"))

    success = update_bono_usages(bono_id, nuevos_usos, historial)
    if not success:
        return jsonify({"error": "Error al canjear el bono en la base de datos."}), 500

    bono["usos_restantes"] = nuevos_usos
    bono["historial"] = historial

    return jsonify({
        "status": "ok",
        "bono_id": bono_id,
        "cliente": bono["cliente"],
        "usos_totales": bono["usos_totales"],
        "usos_restantes": bono["usos_restantes"],
    })


def _scan_page(bono_id):
        return render_template_string(
                """
                <!DOCTYPE html>
                <html lang="es">
                <head>
                    <meta charset="UTF-8">
                    <meta name="viewport" content="width=device-width, initial-scale=1.0">
                    <title>Canje de Bono · New Tropic</title>
                    <style>
                        :root {
                            --bg: #080808;
                            --card-bg: #111111;
                            --border: rgba(255, 255, 255, 0.08);
                            --text-main: #ffffff;
                            --text-dim: #999999;
                        }
                        * { box-sizing: border-box; }
                        body {
                            margin: 0;
                            min-height: 100vh;
                            display: grid;
                            place-items: center;
                            padding: 24px;
                            font-family: Inter, sans-serif;
                            background: var(--bg);
                            color: var(--text-main);
                        }
                        .card {
                            width: 100%;
                            max-width: 420px;
                            background: var(--card-bg);
                            border: 1px solid var(--border);
                            border-radius: 16px;
                            padding: 32px;
                            box-shadow: 0 20px 50px rgba(0, 0, 0, 0.45);
                        }
                        .eyebrow {
                            color: var(--text-dim);
                            text-transform: uppercase;
                            letter-spacing: 4px;
                            font-size: 11px;
                            margin-bottom: 20px;
                        }
                        h1 { margin: 0 0 12px; font-size: 22px; }
                        .desc { color: var(--text-dim); line-height: 1.5; margin-bottom: 24px; }
                        .field { margin-bottom: 14px; }
                        label { display:block; margin-bottom: 8px; color: var(--text-dim); font-size: 13px; }
                        input {
                            width: 100%;
                            padding: 14px 16px;
                            border-radius: 12px;
                            border: 1px solid var(--border);
                            background: #0f0f0f;
                            color: var(--text-main);
                            outline: none;
                        }
                        button {
                            width: 100%;
                            border: 0;
                            border-radius: 12px;
                            padding: 14px 16px;
                            margin-top: 10px;
                            background: #fff;
                            color: #000;
                            font-weight: 700;
                            cursor: pointer;
                        }
                        .muted { color: var(--text-dim); font-size: 12px; margin-top: 12px; }
                        .result { display:none; margin-top: 18px; padding-top: 18px; border-top: 1px solid var(--border); }
                        .result.ok { display:block; }
                        .result.error { display:block; }
                        .result-title { font-weight: 700; margin-bottom: 8px; }
                        .result-text { color: var(--text-dim); line-height: 1.5; }
                    </style>
                </head>
                <body>
                    <div class="card">
                        <div class="eyebrow">NEW TROPIC</div>
                        <h1>Canje de bono</h1>
                        <p class="desc">Debes autenticarte una vez por dispositivo. Después, el token se guarda en este navegador y no volverá a pedirlo.</p>

                        <div class="field" id="login-field">
                            <label for="password">Contraseña</label>
                            <input id="password" type="password" placeholder="••••••••" autocomplete="current-password">
                            <button id="login-btn" type="button">Autenticar y canjear</button>
                        </div>

                        <div class="muted" id="status-line">Bono ID: {{ bono_id }}</div>
                        <div class="result" id="result-box">
                            <div class="result-title" id="result-title"></div>
                            <div class="result-text" id="result-text"></div>
                        </div>
                    </div>

                    <script>
                        const STORAGE_KEY = 'scanAuthToken';
                        const scanToken = new URLSearchParams(window.location.search).get('token');
                        const loginField = document.getElementById('login-field');
                        const statusLine = document.getElementById('status-line');
                        const resultBox = document.getElementById('result-box');
                        const resultTitle = document.getElementById('result-title');
                        const resultText = document.getElementById('result-text');
                        const loginBtn = document.getElementById('login-btn');
                        const passwordInput = document.getElementById('password');

                        function setResult(title, text, kind) {
                            resultBox.className = 'result ' + kind;
                            resultTitle.textContent = title;
                            resultText.textContent = text;
                        }

                        async function redeem() {
                            const authToken = localStorage.getItem(STORAGE_KEY);
                            if (!authToken) {
                                loginField.style.display = 'block';
                                return;
                            }

                            if (!scanToken) {
                                setResult('Código QR inválido', 'Falta el token del bono en la URL.', 'error');
                                return;
                            }

                            statusLine.textContent = 'Validando acceso...';

                            const response = await fetch(window.location.pathname + window.location.search, {
                                method: 'POST',
                                headers: {
                                    'Content-Type': 'application/json',
                                    'Authorization': 'Bearer ' + authToken,
                                },
                                body: JSON.stringify({}),
                            });

                            const data = await response.json().catch(() => ({}));

                            if (response.status === 401) {
                                localStorage.removeItem(STORAGE_KEY);
                                loginField.style.display = 'block';
                                statusLine.textContent = data.error || 'Sesión caducada. Vuelve a autenticarte.';
                                return;
                            }

                            if (!response.ok) {
                                setResult('No se pudo canjear', data.error || 'Error inesperado.', 'error');
                                return;
                            }

                            loginField.style.display = 'none';
                            setResult(
                                'Uso canjeado con éxito',
                                data.cliente + ' · ' + data.usos_restantes + ' de ' + data.usos_totales + ' usos restantes',
                                'ok'
                            );
                            statusLine.textContent = 'Bono ID: {{ bono_id }}';
                        }

                        async function loginAndRedeem() {
                            const password = passwordInput.value.trim();
                            if (!password) {
                                statusLine.textContent = 'Introduce la contraseña.';
                                return;
                            }

                            loginBtn.disabled = true;
                            loginBtn.textContent = 'Autenticando...';

                            try {
                                const response = await fetch('/login', {
                                    method: 'POST',
                                    headers: { 'Content-Type': 'application/json' },
                                    body: JSON.stringify({ password }),
                                });

                                const data = await response.json().catch(() => ({}));

                                if (!response.ok) {
                                    statusLine.textContent = data.error || 'Contraseña incorrecta.';
                                    return;
                                }

                                localStorage.setItem(STORAGE_KEY, data.token);
                                passwordInput.value = '';
                                await redeem();
                            } catch (error) {
                                statusLine.textContent = 'No se pudo conectar con el servidor.';
                            } finally {
                                loginBtn.disabled = false;
                                loginBtn.textContent = 'Autenticar y canjear';
                            }
                        }

                        loginBtn.addEventListener('click', loginAndRedeem);
                        passwordInput.addEventListener('keydown', (event) => {
                            if (event.key === 'Enter') loginAndRedeem();
                        });

                        redeem();
                    </script>
                </body>
                </html>
                """,
                bono_id=bono_id,
        )

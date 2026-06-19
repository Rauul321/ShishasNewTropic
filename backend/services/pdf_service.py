from datetime import datetime
from io import BytesIO
import os
import tempfile
from urllib.parse import urlencode, urlparse
from urllib.request import urlopen

import qrcode
from PIL import Image as PILImage
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

from core.auth import generate_scan_token
from core.config import BARLOW_BOLD_PATH, BARLOW_REGULAR_PATH, ORIGINAL_IMAGE_SOURCE, ORIGINAL_IMAGE_PATH


pdfmetrics.registerFont(TTFont("Barlow", BARLOW_REGULAR_PATH))
pdfmetrics.registerFont(TTFont("Barlow-Bold", BARLOW_BOLD_PATH))


def generate_qr_image(url):
    qr = qrcode.QRCode(
        version=1,
        box_size=10,
        border=4,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
    )
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="#111111", back_color="white")
    buf = BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf


_cached_background_path = None

def get_cached_background_path():
    global _cached_background_path
    if _cached_background_path is not None and os.path.exists(_cached_background_path):
        return _cached_background_path

    cached_jpg = os.path.join(tempfile.gettempdir(), "shishas_bg_resized_v1.jpg")
    
    if os.path.exists(cached_jpg):
        _cached_background_path = cached_jpg
        return _cached_background_path

    # 1. Try local filesystem
    if ORIGINAL_IMAGE_PATH and os.path.exists(ORIGINAL_IMAGE_PATH):
        try:
            img = PILImage.open(ORIGINAL_IMAGE_PATH)
            img.load()
            target_size = (1240, 1754)
            img_resized = img.convert("RGB").resize(target_size, PILImage.Resampling.LANCZOS)
            img_resized.save(cached_jpg, format="JPEG", quality=95)
            _cached_background_path = cached_jpg
            print("[+] Imagen de fondo cargada, redimensionada y guardada como JPEG en caché.")
            return _cached_background_path
        except Exception as e:
            print(f"[-] Error procesando imagen local: {e}")

    # 2. Fallback to network download
    try:
        parsed = urlparse(ORIGINAL_IMAGE_SOURCE)
        if parsed.scheme in {"http", "https"}:
            print(f"[!] Descargando imagen de fondo desde {ORIGINAL_IMAGE_SOURCE}...")
            with urlopen(ORIGINAL_IMAGE_SOURCE, timeout=10) as response:
                img = PILImage.open(BytesIO(response.read()))
                img.load()
                target_size = (1240, 1754)
                img_resized = img.convert("RGB").resize(target_size, PILImage.Resampling.LANCZOS)
                img_resized.save(cached_jpg, format="JPEG", quality=95)
                _cached_background_path = cached_jpg
                print("[+] Imagen de fondo descargada, redimensionada y guardada como JPEG en caché.")
                return _cached_background_path
    except Exception as e:
        print(f"[-] Error al cargar la imagen de fondo remota: {e}")

    return None


def generate_pdf(bono_id, cliente, telefono, usos_totales, usos_restantes, fecha_compra, base_url):
    scan_url = f"{base_url}/scan/{bono_id}?{urlencode({'token': generate_scan_token(bono_id)})}"
    qr_buf = generate_qr_image(scan_url)
    pdf_path = os.path.join(tempfile.gettempdir(), f"bono_{bono_id}.pdf")

    qr_tmp = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
    qr_tmp.write(qr_buf.read())
    qr_tmp.close()

    c = canvas.Canvas(pdf_path, pagesize=A4, pageCompression=1)
    w, h = A4

    bg_path = get_cached_background_path()

    if bg_path is not None:
        try:
            c.drawImage(bg_path, 0, 0, width=w, height=h)
        except Exception as e:
            print(f"Error al procesar la imagen de fondo: {e}")
            c.setFillColor(colors.HexColor("#080808"))
            c.rect(0, 0, w, h, fill=1, stroke=0)
    else:
        c.setFillColor(colors.HexColor("#080808"))
        c.rect(0, 0, w, h, fill=1, stroke=0)
        c.setFillColor(colors.white)
        c.setFont("Helvetica-Bold", 14)
        c.drawCentredString(w / 2, h / 2, "Imagen de fondo no cargada.")

    qr_size = 170
    qr_x = w / 2 - qr_size / 2
    qr_y = (h / 2 - qr_size / 2) - 40

    c.setFillColor(colors.white)
    c.roundRect(qr_x - 10, qr_y - 10, qr_size + 20, qr_size + 20, 8, fill=1, stroke=0)
    c.drawImage(qr_tmp.name, qr_x, qr_y, width=qr_size, height=qr_size)

    label_y = qr_y + qr_size + 30
    label_text = f"{cliente.upper()}"

    c.setFillColor(colors.white)
    c.setFont("Barlow-Bold", 24)
    c.drawCentredString(w / 2, label_y, label_text)

    info_y = label_y + 30
    c.setFillColor(colors.white)
    c.setFont("Barlow-Bold", 22)

    try:
        fecha_obj = datetime.strptime(fecha_compra, "%d/%m/%Y %H:%M")
        fecha_formateada = fecha_obj.strftime("%d/%m/%Y")
    except ValueError:
        fecha_formateada = fecha_compra

    c.drawCentredString(w / 2, info_y, f"{fecha_formateada} · VÁLIDO POR {usos_totales} CACHIMBAS")

    c.setFillColor(colors.HexColor("#555555"))
    c.setFont("Helvetica", 8)
    c.drawCentredString(w / 2, 20, f"ID BONO: {bono_id} · NEW TROPIC")

    c.save()

    try:
        os.unlink(qr_tmp.name)
    except Exception as e:
        print(f"Error al limpiar archivos temporales: {e}")

    return pdf_path

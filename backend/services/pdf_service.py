from datetime import datetime
from io import BytesIO
import os
import tempfile

import qrcode
from PIL import Image as PILImage
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

from core.config import BARLOW_BOLD_PATH, BARLOW_REGULAR_PATH, ORIGINAL_IMAGE_PATH


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


def generate_pdf(bono_id, cliente, telefono, usos_totales, usos_restantes, fecha_compra, base_url):
    scan_url = f"{base_url}/scan/{bono_id}"
    qr_buf = generate_qr_image(scan_url)
    pdf_path = os.path.join(tempfile.gettempdir(), f"bono_{bono_id}.pdf")

    qr_tmp = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
    qr_tmp.write(qr_buf.read())
    qr_tmp.close()

    c = canvas.Canvas(pdf_path, pagesize=A4, pageCompression=1)
    w, h = A4

    bg_tmp_path = None

    if os.path.exists(ORIGINAL_IMAGE_PATH):
        try:
            img_original = PILImage.open(ORIGINAL_IMAGE_PATH)
            target_size = (1240, 1754)
            img_resized = img_original.resize(target_size, PILImage.Resampling.LANCZOS)

            bg_tmp = tempfile.NamedTemporaryFile(suffix=".jpg", delete=False)
            img_resized.convert("RGB").save(bg_tmp.name, format="JPEG", quality=65, optimize=True)
            bg_tmp.close()
            bg_tmp_path = bg_tmp.name

            c.drawImage(bg_tmp_path, 0, 0, width=w, height=h)
        except Exception as e:
            print(f"Error al optimizar la imagen de fondo: {e}")
            c.drawImage(ORIGINAL_IMAGE_PATH, 0, 0, width=w, height=h)
    else:
        c.setFillColor(colors.HexColor("#080808"))
        c.rect(0, 0, w, h, fill=1, stroke=0)
        c.setFillColor(colors.white)
        c.setFont("Helvetica-Bold", 14)
        c.drawCentredString(w / 2, h / 2, f"Imagen '{ORIGINAL_IMAGE_PATH}' no encontrada.")

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
        if bg_tmp_path and os.path.exists(bg_tmp_path):
            os.unlink(bg_tmp_path)
    except Exception as e:
        print(f"Error al limpiar archivos temporales: {e}")

    return pdf_path

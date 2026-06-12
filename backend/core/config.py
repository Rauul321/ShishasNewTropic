from pathlib import Path

from dotenv import load_dotenv


load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent
ORIGINAL_IMAGE_SOURCE = "https://bhartzaotpohrezefeya.supabase.co/storage/v1/object/public/vouchers_img/image_0.png"
ORIGINAL_IMAGE_PATH = ORIGINAL_IMAGE_SOURCE
BARLOW_REGULAR_PATH = str(BASE_DIR / "Barlow-Regular.ttf")
BARLOW_BOLD_PATH = str(BASE_DIR / "Barlow-Bold.ttf")


import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()  # carrega .env se existir

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
TEMP_DIR = BASE_DIR / "temp"

DATA_DIR.mkdir(exist_ok=True)
TEMP_DIR.mkdir(exist_ok=True)

# DB config
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://nfse_user:senha123@localhost/nfse_db")

# Tesseract (se precisar ajustar)
TESSERACT_CMD = os.getenv("TESSERACT_CMD", "/usr/bin/tesseract")
TESSDATA_PREFIX = os.getenv("TESSDATA_PREFIX", "/usr/share/tesseract-ocr/4.00/tessdata")

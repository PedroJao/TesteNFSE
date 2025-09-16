import os
import uuid
from pathlib import Path
from fastapi import UploadFile
from ..config import TEMP_DIR

def save_upload_file(upload: UploadFile, dest_folder: str = None) -> str:
    """Salva UploadFile em disco em TEMP_DIR (nome único) e retorna caminho."""
    dest_folder = Path(dest_folder or TEMP_DIR)
    dest_folder.mkdir(parents=True, exist_ok=True)
    filename = os.path.basename(upload.filename)
    unique = f"{uuid.uuid4().hex}_{filename}"
    path = dest_folder / unique
    with path.open("wb") as f:
        f.write(upload.file.read())
    return str(path)

def remove_file(path: str) -> None:
    try:
        if path and os.path.exists(path):
            os.remove(path)
    except Exception:
        pass

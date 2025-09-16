import re
import os
import cv2
import numpy as np
import pytesseract
import fitz
from datetime import datetime
from typing import List, Tuple
from ..config import DATA_DIR, TESSERACT_CMD, TESSDATA_PREFIX
from .base import NFSeExtractor

# Configura tesseract
pytesseract.pytesseract.tesseract_cmd = TESSERACT_CMD
os.environ.setdefault("TESSDATA_PREFIX", TESSDATA_PREFIX)

# Crops padrão
DEFAULT_CROPS: List[Tuple[int, int, int, int]] = [
    (306, 372, 541, 936),    # data_emissao
    (83, 303, 1985, 2395),   # numero_nfse
    (511, 574, 825, 2396),   # prestador_nome
    (643, 702, 695, 1110),   # prestador_cnpj
    (699, 758, 775, 2396),   # prestador_endereco
    (904, 946, 517, 2392),   # tomador_nome
    (970, 1012, 328, 713),   # tomador_cnpj
    (1029, 1071, 411, 2392), # tomador_endereco
    (1224, 1857, 88, 2392),  # servicos_descricao
    (2445, 2500, 584, 909),  # valor_servicos
    (2925, 3029, 2027, 2381),# valor_iss
    (2932, 3022, 584, 907),  # valor_liquido
    (2514, 2584, 2019, 2393) # valor_deducoes
]

class FortalezaNFSeExtractor(NFSeExtractor):
    def __init__(self, template_filename: str = "brasao_fortaleza.png", crops: List[Tuple[int,int,int,int]] = None):
        self.template_path = os.path.join(DATA_DIR, template_filename)
        self.fixed_crops = crops or DEFAULT_CROPS

    def pdf_to_image(self, pdf_path: str, page_num: int = 0):
        """Renderiza a página como imagem numpy (BGR)."""
        doc = fitz.open(pdf_path)
        page = doc[page_num]
        pix = page.get_pixmap(dpi=300)
        arr = np.frombuffer(pix.samples, dtype=np.uint8)
        try:
            img = arr.reshape(pix.height, pix.width, pix.n)
        except Exception:
            # fallback in case of single-channel
            img = arr.reshape(pix.height, pix.width)
            img = cv2.cvtColor(img, cv2.COLOR_GRAY2RGB)
        img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
        doc.close()
        return img

    def extract_text_from_crop(self, img: np.ndarray, crop: Tuple[int,int,int,int]) -> str:
        y_start, y_end, x_start, x_end = crop
        # bounds safety
        y_start = max(0, int(y_start)); y_end = max(y_start+1, int(y_end))
        x_start = max(0, int(x_start)); x_end = max(x_start+1, int(x_end))
        crop_img = img[y_start:y_end, x_start:x_end]
        if crop_img.size == 0:
            return ""
        gray = cv2.cvtColor(crop_img, cv2.COLOR_BGR2GRAY)
        # adaptive threshold + morphology -> reduz ruído mantendo velocidade
        _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        kernel = np.ones((1,1), np.uint8)
        processed = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
        config = "--oem 3 --psm 6"
        try:
            text = pytesseract.image_to_string(processed, lang="por", config=config)
            return text.strip()
        except Exception:
            return ""

    def detect_brasao(self, img: np.ndarray, threshold: float = 0.6) -> bool:
        """Detecta o brasão usando matchTemplate multi-escala."""
        template = cv2.imread(self.template_path)
        if template is None:
            return False
        # sharpen template for robustness
        kernel = np.array([[-1,-1,-1],[-1,9,-1],[-1,-1,-1]])
        template = cv2.filter2D(template, -1, kernel)
        best_val = -1.0
        best_loc = None
        best_scale = 1.0
        h_t, w_t = template.shape[:2]
        scales = np.linspace(0.6, 1.4, 12)
        for scale in scales:
            t_h = int(h_t * scale); t_w = int(w_t * scale)
            if t_h >= img.shape[0] or t_w >= img.shape[1]:
                continue
            resized = cv2.resize(template, (t_w, t_h), interpolation=cv2.INTER_AREA if scale < 1 else cv2.INTER_CUBIC)
            try:
                res_channels = [cv2.matchTemplate(img[:,:,c], resized[:,:,c], cv2.TM_CCOEFF_NORMED) for c in range(3)]
                res = np.mean(res_channels, axis=0)
                _, max_val, _, max_loc = cv2.minMaxLoc(res)
            except Exception:
                continue
            if max_val > best_val:
                best_val = max_val
                best_loc = max_loc
                best_scale = scale
            if best_val >= threshold:
                break
        # opcional: salva debug match se encontrado
        if best_val >= threshold and best_loc:
            x, y = best_loc
            rh, rw = int(h_t*best_scale), int(w_t*best_scale)
            debug = img.copy()
            cv2.rectangle(debug, (x, y), (x+rw, y+rh), (0,255,0), 2)
            debug_path = os.path.join(DATA_DIR, "debug_match.png")
            cv2.imwrite(debug_path, debug)
            return True
        return False

    def parse_fields(self, textos: dict) -> dict:
        """Converte textos em estrutura de dados fidedigna."""
        dados = {
            "data_emissao": None,
            "numero_nfse": None,
            "prestador": {"nome": None, "cnpj": None, "endereco": None},
            "tomador": {"nome": None, "cpf_cnpj": None, "endereco": None},
            "servicos": [{"descricao": None, "quantidade": 1, "valor_unitario": 0.0, "valor_total": 0.0}],
            "valores": {"valor_servicos": 0.0, "valor_deducoes": 0.0, "valor_iss": 0.0, "valor_liquido": 0.0}
        }

        # data
        dm = re.search(r"(\d{2}/\d{2}/\d{4}(?: \d{2}:\d{2}:\d{2})?)", textos.get("data_emissao",""))
        if dm:
            try:
                if len(dm.group(1)) > 10:
                    dados["data_emissao"] = datetime.strptime(dm.group(1), "%d/%m/%Y %H:%M:%S").isoformat()
                else:
                    dados["data_emissao"] = datetime.strptime(dm.group(1), "%d/%m/%Y").isoformat()
            except Exception:
                dados["data_emissao"] = dm.group(1)

        # numero nfse
        nm = re.search(r"(\d+)", textos.get("numero_nfse",""))
        if nm:
            dados["numero_nfse"] = nm.group(1)

        dados["prestador"]["nome"] = (textos.get("prestador_nome") or "").strip() or None
        dados["prestador"]["cnpj"] = (textos.get("prestador_cnpj") or "").strip() or None
        dados["prestador"]["endereco"] = (textos.get("prestador_endereco") or "").strip() or None

        dados["tomador"]["nome"] = (textos.get("tomador_nome") or "").strip() or None
        dados["tomador"]["cpf_cnpj"] = (textos.get("tomador_cnpj") or "").strip() or None
        dados["tomador"]["endereco"] = (textos.get("tomador_endereco") or "").strip() or None

        dados["servicos"][0]["descricao"] = (textos.get("servicos_descricao") or "").strip() or None

        # valores (limpeza)
        for field in ["valor_servicos", "valor_iss", "valor_liquido", "valor_deducoes"]:
            raw = textos.get(field, "") or ""
            m = re.search(r"([\d\.,]+)", raw)
            if m:
                num = m.group(1).replace(".", "").replace(",", ".")
                try:
                    dados["valores"][field] = float(num)
                except Exception:
                    dados["valores"][field] = 0.0
            else:
                dados["valores"][field] = 0.0

        return dados

    def extract(self, file_path: str) -> dict:
        """Fluxo principal de extração para NFSe Fortaleza."""
        img = self.pdf_to_image(file_path)
        # detecta brasão se possível; se não detectado, ainda tenta extrair
        _ = self.detect_brasao(img)
        field_names = [
            "data_emissao", "numero_nfse", "prestador_nome", "prestador_cnpj", "prestador_endereco",
            "tomador_nome", "tomador_cnpj", "tomador_endereco", "servicos_descricao",
            "valor_servicos", "valor_iss", "valor_liquido", "valor_deducoes"
        ]
        textos = {}
        for name, crop in zip(field_names, self.fixed_crops):
            textos[name] = self.extract_text_from_crop(img, crop)
        dados = self.parse_fields(textos)
        # salva debug de crops (imagem com retângulos)
        debug_img = img.copy()
        for i, crop in enumerate(self.fixed_crops):
            y1,y2,x1,x2 = crop
            cv2.rectangle(debug_img, (x1,y1), (x2,y2), (0,255,0), 1)
            cv2.putText(debug_img, str(i), (x1, max(y1-6,0)), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0,255,0),1)
        debug_path = os.path.join(DATA_DIR, "debug_marked.png")
        cv2.imwrite(debug_path, debug_img)
        return dados
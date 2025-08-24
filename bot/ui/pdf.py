from __future__ import annotations

import os
import json
from pathlib import Path
from typing import Dict, Optional

from fpdf import FPDF


def _ensure_dir(path: str) -> None:
    Path(path).mkdir(parents=True, exist_ok=True)


def _setup_font(pdf: FPDF) -> None:
    # Try to register DejaVu for Unicode; fallback to core font
    try:
        font_path = Path("assets").joinpath("DejaVuSans.ttf")
        if font_path.exists():
            pdf.add_font("DejaVu", "", str(font_path), uni=True)
            pdf.set_font("DejaVu", size=12)
            return
    except Exception:
        pass
    pdf.set_font("helvetica", size=12)


def save_text_pdf(user_id: int, title: str, body_text: str, *, base_dir: str = "data/reports") -> str:
    out_dir = os.path.join(base_dir, str(user_id))
    _ensure_dir(out_dir)
    pdf_path = os.path.join(out_dir, "last.pdf")

    pdf = FPDF(format="A4")
    pdf.add_page()
    _setup_font(pdf)

    # Title
    pdf.set_text_color(0, 0, 0)
    pdf.set_font_size(16)
    pdf.multi_cell(0, 10, txt=title)
    pdf.ln(2)

    # Body
    pdf.set_font_size(12)
    # Avoid long unbroken lines
    for line in body_text.splitlines():
        pdf.multi_cell(0, 8, txt=line)

    pdf.output(pdf_path)
    return pdf_path


def save_last_json(user_id: int, payload: Dict, *, base_dir: str = "data/reports") -> str:
    out_dir = os.path.join(base_dir, str(user_id))
    _ensure_dir(out_dir)
    json_path = os.path.join(out_dir, "last.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    return json_path





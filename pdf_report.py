from pathlib import Path
from typing import Dict, Any
from fpdf import FPDF


async def build_pdf(user_profile: Dict[str, Any], rec: Dict[str, Any], out_path: str) -> str:
	p = Path(out_path)
	p.parent.mkdir(parents=True, exist_ok=True)
	pdf = FPDF()
	pdf.add_page()
	pdf.add_font('Arial', '', '', uni=False)
	pdf.set_font('Arial', size=12)
	pdf.multi_cell(0, 8, txt="Персональный план ухода")
	pdf.ln(4)

	pdf.set_font('Arial', size=10)
	pdf.multi_cell(0, 6, txt=f"Тип кожи: {user_profile.get('skin_type','')}\nПроблемы: {', '.join(user_profile.get('concerns', []))}")
	pdf.ln(4)

	def section(title: str):
		pdf.set_font('Arial', size=12)
		pdf.multi_cell(0, 7, txt=title)
		pdf.set_font('Arial', size=10)

	section('AM')
	for pid in rec.get('routines', {}).get('am', []):
		prod = next((p for p in rec.get('products', []) if p['id'] == pid), None)
		if prod:
			pdf.multi_cell(0, 6, txt=f"- {prod['name']} ({prod['brand']}) — {prod.get('usage','')}")

	section('PM')
	for pid in rec.get('routines', {}).get('pm', []):
		prod = next((p for p in rec.get('products', []) if p['id'] == pid), None)
		if prod:
			pdf.multi_cell(0, 6, txt=f"- {prod['name']} ({prod['brand']}) — {prod.get('usage','')}")

	section('Weekly')
	for pid in rec.get('routines', {}).get('weekly', []):
		prod = next((p for p in rec.get('products', []) if p['id'] == pid), None)
		if prod:
			pdf.multi_cell(0, 6, txt=f"- {prod['name']} ({prod['brand']}) — {prod.get('usage','')}")

	pdf.output(str(p))
	return str(p)


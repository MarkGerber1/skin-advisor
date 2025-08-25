"""
PDF Report Generation Module
Handles saving reports as JSON and PDF files for users
"""
from __future__ import annotations

import os
import json
from typing import Dict, Any, Optional


def save_last_json(uid: int, snapshot: Dict[str, Any]) -> str:
    """Save user's latest report data as JSON"""
    try:
        # Create user reports directory
        user_dir = os.path.join("data", "reports", str(uid))
        os.makedirs(user_dir, exist_ok=True)
        
        # Save JSON snapshot
        json_path = os.path.join(user_dir, "last.json")
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(snapshot, f, ensure_ascii=False, indent=2)
        
        print(f"✅ Saved JSON report for user {uid}: {json_path}")
        return json_path
        
    except Exception as e:
        print(f"❌ Error saving JSON report for user {uid}: {e}")
        return ""


def save_text_pdf(uid: int, title: str, body_text: str) -> str:
    """Save report as PDF (with text fallback if fpdf2 unavailable)"""
    try:
        # Create user reports directory
        user_dir = os.path.join("data", "reports", str(uid))
        os.makedirs(user_dir, exist_ok=True)
        
        pdf_path = os.path.join(user_dir, "last.pdf")
        
        # Try to create PDF using fpdf2
        try:
            from fpdf import FPDF
            
            pdf = FPDF(unit="mm", format="A4")
            pdf.add_page()
            
            # Try to add Unicode font for Russian text
            try:
                font_path = "assets/fonts/DejaVuSans.ttf"
                if os.path.exists(font_path):
                    pdf.add_font("DejaVu", "", font_path, uni=True)
                    pdf.set_font("DejaVu", size=12)
                else:
                    raise Exception("DejaVu font not found")
            except Exception:
                # Fallback to Arial
                pdf.set_font("Arial", size=12)
            
            # Add title
            pdf.set_font_size(16)
            pdf.multi_cell(0, 8, title)
            pdf.ln(5)
            
            # Add body text
            pdf.set_font_size(12)
            
            # Split text into paragraphs and handle encoding
            paragraphs = body_text.split('\n\n')
            for paragraph in paragraphs:
                if paragraph.strip():
                    try:
                        # Clean text for PDF
                        clean_text = paragraph.strip()
                        # Remove markdown formatting
                        clean_text = clean_text.replace('**', '').replace('*', '')
                        pdf.multi_cell(0, 6, clean_text)
                        pdf.ln(2)
                    except Exception as e:
                        print(f"Warning: Skipping paragraph due to encoding: {e}")
                        continue
            
            # Save PDF
            pdf.output(pdf_path)
            print(f"✅ Saved PDF report for user {uid}: {pdf_path}")
            return pdf_path
            
        except ImportError:
            print("⚠️ fpdf2 not available, creating text fallback...")
            # Fallback: save as .txt file but with .pdf extension
            with open(pdf_path, "w", encoding="utf-8") as f:
                f.write(f"{title}\n")
                f.write("=" * len(title) + "\n\n")
                f.write(body_text)
            
            print(f"✅ Saved text fallback for user {uid}: {pdf_path}")
            return pdf_path
            
    except Exception as e:
        print(f"❌ Error saving PDF report for user {uid}: {e}")
        return ""


def get_last_report_path(uid: int) -> Optional[str]:
    """Get path to user's last PDF report if it exists"""
    try:
        pdf_path = os.path.join("data", "reports", str(uid), "last.pdf")
        if os.path.exists(pdf_path):
            return pdf_path
        return None
    except Exception:
        return None


def get_last_json_path(uid: int) -> Optional[str]:
    """Get path to user's last JSON report if it exists"""
    try:
        json_path = os.path.join("data", "reports", str(uid), "last.json")
        if os.path.exists(json_path):
            return json_path
        return None
    except Exception:
        return None


def load_last_report_json(uid: int) -> Optional[Dict[str, Any]]:
    """Load user's last report data from JSON"""
    try:
        json_path = get_last_json_path(uid)
        if json_path:
            with open(json_path, "r", encoding="utf-8") as f:
                return json.load(f)
        return None
    except Exception as e:
        print(f"❌ Error loading JSON report for user {uid}: {e}")
        return None

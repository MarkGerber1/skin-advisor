# -*- coding: utf-8 -*-
"""
Visual Cards Generator
Генератор визуальных карточек результатов тестов
"""

import os
from typing import Dict, List, Any, Optional
from pathlib import Path


class VisualCardGenerator:
    """Генератор визуальных карточек"""

    def __init__(self):
        self.output_dir = Path("output/cards")
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate_makeup_card(
        self, profile: Dict[str, Any], recommendations: List[Dict[str, Any]]
    ) -> Optional[str]:
        """Генерировать визуальную карточку для макияжа"""
        try:
            html_content = self._create_makeup_card_html(profile, recommendations)
            filename = f"makeup_card_{profile.get('user_id', 'unknown')}.html"
            filepath = self.output_dir / filename

            with open(filepath, "w", encoding="utf-8") as f:
                f.write(html_content)

            return str(filepath)
        except Exception as e:
            print(f"Error generating makeup card: {e}")
            return None

    def generate_skincare_card(
        self, profile: Dict[str, Any], recommendations: List[Dict[str, Any]]
    ) -> Optional[str]:
        """Генерировать визуальную карточку для ухода за кожей"""
        try:
            html_content = self._create_skincare_card_html(profile, recommendations)
            filename = f"skincare_card_{profile.get('user_id', 'unknown')}.html"
            filepath = self.output_dir / filename

            with open(filepath, "w", encoding="utf-8") as f:
                f.write(html_content)

            return str(filepath)
        except Exception as e:
            print(f"Error generating skincare card: {e}")
            return None

    def _create_makeup_card_html(
        self, profile: Dict[str, Any], recommendations: List[Dict[str, Any]]
    ) -> str:
        """Создать HTML карточку для макияжа"""
        user_id = profile.get("user_id", "unknown")
        season = profile.get("season", "unknown")
        undertone = profile.get("undertone", "unknown")

        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Ваш цветотип</title>
            <style>
                body {{ font-family: Arial; background: linear-gradient(45deg, #667eea, #764ba2); margin: 0; padding: 20px; min-height: 100vh; display: flex; align-items: center; justify-content: center; }}
                .card {{ background: white; border-radius: 20px; padding: 30px; max-width: 500px; box-shadow: 0 20px 40px rgba(0,0,0,0.1); text-align: center; }}
                .season {{ font-size: 24px; font-weight: bold; color: #667eea; margin: 20px 0; }}
            </style>
        </head>
        <body>
            <div class="card">
                <h1>Ваш цветотип</h1>
                <div class="season">{season.title()} тип ({undertone.title()} подтон)</div>
                <p>Рекомендуемые продукты:</p>
                <ul>
        """

        for rec in recommendations[:3]:
            html += f"<li>{rec.get('brand', '')} {rec.get('name', '')}</li>"

        html += """
                </ul>
            </div>
        </body>
        </html>
        """

        return html

    def _create_skincare_card_html(
        self, profile: Dict[str, Any], recommendations: List[Dict[str, Any]]
    ) -> str:
        """Создать HTML карточку для ухода за кожей"""
        skin_type = profile.get("skin_type", "unknown")
        concerns = profile.get("concerns", [])

        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Портрет кожи</title>
            <style>
                body {{ font-family: Arial; background: linear-gradient(45deg, #f093fb, #f5576c); margin: 0; padding: 20px; min-height: 100vh; display: flex; align-items: center; justify-content: center; }}
                .card {{ background: white; border-radius: 20px; padding: 30px; max-width: 500px; box-shadow: 0 20px 40px rgba(0,0,0,0.1); text-align: center; }}
                .skin-type {{ font-size: 24px; font-weight: bold; color: #f5576c; margin: 20px 0; }}
            </style>
        </head>
        <body>
            <div class="card">
                <h1>Портрет кожи</h1>
                <div class="skin-type">{skin_type.title()} кожа</div>
                <p>Рекомендуемые продукты:</p>
                <ul>
        """

        for rec in recommendations[:3]:
            html += f"<li>{rec.get('brand', '')} {rec.get('name', '')}</li>"

        html += """
                </ul>
            </div>
        </body>
        </html>
        """

        return html


def generate_visual_cards(
    profile: Dict[str, Any], recommendations: List[Dict[str, Any]]
) -> List[str]:
    """Генерировать визуальные карточки"""
    generator = VisualCardGenerator()
    results = []

    if "season" in profile and "undertone" in profile:
        card_path = generator.generate_makeup_card(profile, recommendations)
        if card_path:
            results.append(card_path)
    elif "skin_type" in profile:
        card_path = generator.generate_skincare_card(profile, recommendations)
        if card_path:
            results.append(card_path)

    return results

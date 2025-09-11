#!/usr/bin/env python3
"""
Тест генерации визуальных карточек
"""
import sys
import os

# Добавляем пути
sys.path.insert(0, os.getcwd())

print("🎨 Testing Visual Card Generation")
print("=" * 50)

# Проверка зависимостей
try:
    from PIL import Image, ImageDraw, ImageFont

    print("✅ Pillow: Available")
except ImportError as e:
    print(f"❌ Pillow: Not available - {e}")

try:
    import cairosvg

    print("✅ CairoSVG: Available")
except ImportError as e:
    print(f"❌ CairoSVG: Not available - {e}")

# Тест создания карточки
try:
    from report.cards import VisualCardGenerator, CardConfig
    from engine.models import UserProfile, Season, Undertone

    print("\n🎯 Testing card generation...")

    # Создаем тестовый профиль
    test_profile = UserProfile(
        user_id=12345, season=Season.SPRING, undertone=Undertone.WARM, age=25
    )

    test_result = {
        "skin_type": "Комбинированная",
        "concerns": ["шелушение", "расширенные поры"],
        "sensitivity": "нормальная",
    }

    # Генерируем карточку
    generator = VisualCardGenerator()
    result = generator.generate_makeup_card(test_profile, {})

    print(f"✅ Makeup card generated:")
    print(f"   SVG: {result.get('svg', 'N/A')}")
    print(f"   PNG: {result.get('png', 'N/A')}")

    # Проверяем файлы
    if result.get("svg") and os.path.exists(result["svg"]):
        print("   ✅ SVG file created")
    else:
        print("   ❌ SVG file not created")

    if result.get("png") and os.path.exists(result["png"]):
        print("   ✅ PNG file created")
    else:
        print("   ❌ PNG file not created (CairoSVG may not be available)")

    print("\n🎉 Visual card generation test completed!")

except Exception as e:
    print(f"❌ Error during card generation: {e}")
    import traceback

    traceback.print_exc()

print("\n📋 Recommendations:")
print("- Install Pillow: pip install Pillow")
print("- Install CairoSVG: pip install CairoSVG")
print("- For production: ensure both libraries are available")

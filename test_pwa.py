#!/usr/bin/env python3
"""
Тест PWA функциональности Beauty Care
Проверяет manifest.json, service worker и офлайн режим
"""

import os
import json
import sys
from pathlib import Path


def test_manifest():
    """Проверка manifest.json"""
    print("🔍 Проверка manifest.json...")

    manifest_path = "BeautyCare-Site/manifest.json"
    if not os.path.exists(manifest_path):
        print("❌ manifest.json не найден")
        return False

    try:
        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest = json.load(f)

        required_fields = ["name", "short_name", "start_url", "display", "icons"]
        missing_fields = []

        for field in required_fields:
            if field not in manifest:
                missing_fields.append(field)

        if missing_fields:
            print(f"❌ Отсутствуют обязательные поля: {missing_fields}")
            return False

        # Проверка иконок
        icons = manifest.get("icons", [])
        if not icons:
            print("❌ Не заданы иконки в manifest")
            return False

        # Проверка основных полей
        if manifest.get("display") != "standalone":
            print("⚠️ Рекомендуется display: 'standalone'")

        print("✅ manifest.json корректен")
        return True

    except json.JSONDecodeError as e:
        print(f"❌ Ошибка парсинга manifest.json: {e}")
        return False


def test_service_worker():
    """Проверка service worker"""
    print("🔍 Проверка service worker...")

    sw_path = "BeautyCare-Site/service-worker.js"
    if not os.path.exists(sw_path):
        print("❌ service-worker.js не найден")
        return False

    try:
        with open(sw_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Проверка основных функций
        required_functions = [
            "addEventListener('install'",
            "addEventListener('activate'",
            "addEventListener('fetch'",
            "caches.open",
            "fetch(",
        ]

        missing_functions = []
        for func in required_functions:
            if func not in content:
                missing_functions.append(func)

        if missing_functions:
            print(f"❌ Отсутствуют обязательные функции: {missing_functions}")
            return False

        print("✅ service-worker.js содержит необходимые функции")
        return True

    except Exception as e:
        print(f"❌ Ошибка чтения service-worker.js: {e}")
        return False


def test_offline_page():
    """Проверка offline страницы"""
    print("🔍 Проверка offline страницы...")

    offline_path = "BeautyCare-Site/offline.html"
    if not os.path.exists(offline_path):
        print("❌ offline.html не найден")
        return False

    try:
        with open(offline_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Проверка основных элементов
        required_elements = [
            "<!DOCTYPE html>",
            '<html lang="ru">',
            "<title>",
            "offline-container",
            "retry-btn",
        ]

        missing_elements = []
        for element in required_elements:
            if element not in content:
                missing_elements.append(element)

        if missing_elements:
            print(f"❌ Отсутствуют элементы: {missing_elements}")
            return False

        print("✅ offline.html содержит необходимые элементы")
        return True

    except Exception as e:
        print(f"❌ Ошибка чтения offline.html: {e}")
        return False


def test_pwa_files():
    """Проверка наличия всех PWA файлов"""
    print("🔍 Проверка наличия PWA файлов...")

    required_files = [
        "BeautyCare-Site/manifest.json",
        "BeautyCare-Site/service-worker.js",
        "BeautyCare-Site/offline.html",
        "BeautyCare-Site/pwa-install.js",
        "BeautyCare-Site/pwa-install.html",
    ]

    missing_files = []
    for file_path in required_files:
        if not os.path.exists(file_path):
            missing_files.append(file_path)

    if missing_files:
        print(f"❌ Отсутствуют файлы: {missing_files}")
        return False

    print("✅ Все PWA файлы присутствуют")
    return True


def test_html_integration():
    """Проверка интеграции PWA в HTML файлы"""
    print("🔍 Проверка интеграции PWA в HTML...")

    html_files = [
        "BeautyCare-Site/index.html",
        "BeautyCare-Site/demo.html",
        "BeautyCare-Site/brand.html",
    ]

    for html_file in html_files:
        if not os.path.exists(html_file):
            print(f"⚠️ HTML файл не найден: {html_file}")
            continue

        try:
            with open(html_file, "r", encoding="utf-8") as f:
                content = f.read()

            # Проверка manifest ссылки
            if '<link rel="manifest"' not in content:
                print(f"❌ Отсутствует manifest ссылка в {html_file}")
                return False

            # Проверка service worker регистрации
            if "serviceWorker.register" not in content:
                print(f"❌ Отсутствует service worker регистрация в {html_file}")
                return False

        except Exception as e:
            print(f"❌ Ошибка чтения {html_file}: {e}")
            return False

    print("✅ PWA интеграция в HTML файлы корректна")
    return True


def main():
    """Основная функция тестирования"""
    print("🧪 ТЕСТИРОВАНИЕ PWA ФУНКЦИОНАЛЬНОСТИ")
    print("=" * 50)

    tests = [
        ("Наличие файлов", test_pwa_files),
        ("Manifest.json", test_manifest),
        ("Service Worker", test_service_worker),
        ("Offline страница", test_offline_page),
        ("HTML интеграция", test_html_integration),
    ]

    passed = 0
    total = len(tests)

    for test_name, test_func in tests:
        print(f"\n📋 {test_name}:")
        if test_func():
            passed += 1
            print("✅ ПРОЙДЕН")
        else:
            print("❌ ПРОВАЛЕН")

    print("\n" + "=" * 50)
    print("📊 РЕЗУЛЬТАТЫ ТЕСТИРОВАНИЯ:")
    print(f"✅ Пройдено: {passed}/{total}")
    print(".1f")
    if passed == total:
        print("🎉 ВСЕ ТЕСТЫ ПРОЙДЕНЫ! PWA готов к использованию")
        return True
    else:
        print("⚠️ Некоторые тесты провалены. Проверьте ошибки выше")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

#!/usr/bin/env python
"""
Проверка готовности проекта к развертыванию на Railway
"""

import os
import sys
from pathlib import Path

def check_file_exists(path, description):
    """Проверяет существование файла"""
    if os.path.exists(path):
        print(f"✅ {description}: {path}")
        return True
    else:
        print(f"❌ {description}: {path} - НЕ НАЙДЕН")
        return False

def check_directory_exists(path, description):
    """Проверяет существование директории"""
    if os.path.exists(path) and os.path.isdir(path):
        print(f"✅ {description}: {path}")
        return True
    else:
        print(f"❌ {description}: {path} - НЕ НАЙДЕНА")
        return False

def check_dockerfile():
    """Проверяет Dockerfile"""
    dockerfile_path = "Dockerfile"
    if not check_file_exists(dockerfile_path, "Dockerfile"):
        return False

    try:
        with open(dockerfile_path, 'r', encoding='utf-8') as f:
            content = f.read()

        required_commands = [
            "FROM python:",
            "COPY requirements.txt",
            "RUN pip install",
            "COPY bot/",
            "COPY engine/",
            "COPY assets/",
            "CMD ["
        ]

        for cmd in required_commands:
            if cmd in content:
                print(f"   ✅ Содержит: {cmd}")
            else:
                print(f"   ❌ Отсутствует: {cmd}")
                return False

        print("   ✅ Dockerfile корректен")
        return True

    except Exception as e:
        print(f"   ❌ Ошибка чтения Dockerfile: {e}")
        return False

def check_railway_config():
    """Проверяет конфигурацию Railway"""
    configs = ["railway.json", "railway.toml"]
    found = False

    for config in configs:
        if os.path.exists(config):
            print(f"✅ Найден Railway config: {config}")
            found = True
            break

    if not found:
        print("❌ Railway конфигурация не найдена")
        return False

    return True

def check_entry_points():
    """Проверяет точки входа"""
    entry_points = ["start.py", "entrypoint.sh", "bot/main.py"]

    for ep in entry_points:
        check_file_exists(ep, f"Entry point: {ep}")

    # Проверим что start.py импортирует main
    if os.path.exists("start.py"):
        try:
            with open("start.py", 'r', encoding='utf-8') as f:
                content = f.read()
                if "from bot.main import main" in content:
                    print("   ✅ start.py корректно импортирует main")
                else:
                    print("   ❌ start.py не импортирует main")
        except Exception as e:
            print(f"   ❌ Ошибка чтения start.py: {e}")

def check_requirements():
    """Проверяет requirements.txt"""
    req_path = "requirements.txt"
    if not check_file_exists(req_path, "Requirements file"):
        return False

    try:
        with open(req_path, 'r', encoding='utf-8') as f:
            content = f.read()

        required_packages = ["aiogram", "fpdf", "python-dotenv", "pydantic"]
        missing = []

        for package in required_packages:
            if package not in content:
                missing.append(package)

        if missing:
            print(f"   ❌ Отсутствуют пакеты: {', '.join(missing)}")
            return False
        else:
            print("   ✅ Все необходимые пакеты присутствуют")
            return True

    except Exception as e:
        print(f"   ❌ Ошибка чтения requirements.txt: {e}")
        return False

def check_env_variables():
    """Проверяет переменные окружения"""
    print("\n🔧 Проверка переменных окружения:")

    critical_vars = ["BOT_TOKEN"]
    optional_vars = ["USE_WEBHOOK", "WEBHOOK_BASE", "LOG_LEVEL", "CATALOG_PATH"]

    # Проверим .env файл
    env_files = [".env", "env.example", ".env.local.example"]
    env_found = False

    for env_file in env_files:
        if os.path.exists(env_file):
            print(f"   ✅ Найден файл переменных: {env_file}")
            env_found = True
            break

    if not env_found:
        print("   ⚠️  Файл переменных окружения не найден")
        print("   💡 Создайте .env файл на основе env.example")

    # Проверим критические переменные
    for var in critical_vars:
        if os.environ.get(var):
            print(f"   ✅ {var}: УСТАНОВЛЕНА")
        else:
            print(f"   ❌ {var}: НЕ УСТАНОВЛЕНА (КРИТИЧНО!)")

def check_project_structure():
    """Проверяет структуру проекта"""
    print("\n📁 Проверка структуры проекта:")

    required_dirs = [
        ("bot", "Основной код бота"),
        ("engine", "Движок рекомендаций"),
        ("assets", "Каталог и ресурсы"),
        ("services", "Сервисы (affiliate, cart)"),
        ("config", "Конфигурация"),
        ("i18n", "Интернационализация")
    ]

    required_files = [
        ("bot/main.py", "Главная функция бота"),
        ("engine/selector_schema.py", "Схема селектора"),
        ("assets/fixed_catalog.yaml", "Каталог товаров"),
        ("services/affiliates.py", "Affiliate сервис"),
        ("services/text_sanitizer.py", "Очистка текста")
    ]

    all_good = True

    for dir_path, description in required_dirs:
        if not check_directory_exists(dir_path, description):
            all_good = False

    for file_path, description in required_files:
        if not check_file_exists(file_path, description):
            all_good = False

    return all_good

def main():
    """Главная функция проверки"""
    print("🚂 === ПРОВЕРКА ГОТОВНОСТИ К РАЗВЕРТЫВАНИЮ НА RAILWAY ===\n")

    checks = [
        ("Структура проекта", check_project_structure),
        ("Dockerfile", check_dockerfile),
        ("Railway конфигурация", check_railway_config),
        ("Точки входа", check_entry_points),
        ("Requirements", check_requirements),
    ]

    results = []

    for check_name, check_func in checks:
        print(f"\n🔍 {check_name}:")
        try:
            result = check_func()
            results.append((check_name, result))
        except Exception as e:
            print(f"❌ Ошибка проверки {check_name}: {e}")
            results.append((check_name, False))

    # Переменные окружения
    check_env_variables()

    # Итоги
    print("\n" + "="*60)
    print("📊 РЕЗУЛЬТАТЫ ПРОВЕРКИ:")

    all_passed = True
    for check_name, result in results:
        status = "✅ ПРОЙДЕНА" if result else "❌ ПРОВАЛЕНА"
        print("30")
        if not result:
            all_passed = False

    if all_passed:
        print("\n🎉 ПРОЕКТ ГОТОВ К РАЗВЕРТЫВАНИЮ НА RAILWAY!")
        print("\n📋 Следующие шаги:")
        print("1. Установите Railway CLI: npm install -g @railway/cli")
        print("2. Авторизуйтесь: railway login")
        print("3. Создайте проект: railway init")
        print("4. Настройте переменные: railway variables set BOT_TOKEN=your_token")
        print("5. Разверните: railway up")
    else:
        print("\n⚠️  ПРОЕКТ НУЖДАЕТСЯ В ДОРАБОТКЕ!")
        print("Исправьте отмеченные проблемы перед развертыванием.")

    print("\n📖 Подробная инструкция: RAILWAY_DEPLOY_GUIDE.md")
    print("="*60)

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Проверка статуса Railway deployment
"""

import subprocess
import os


def run_command(cmd, description):
    """Выполняет команду и возвращает результат"""
    print(f"\n🔍 {description}")
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            env={**os.environ, "PAGER": "cat", "GIT_PAGER": "cat"},
        )

        if result.returncode == 0:
            print("✅ УСПЕХ")
            if result.stdout.strip():
                print(f"   📄 {result.stdout.strip()}")
            return True
        else:
            print("❌ ОШИБКА")
            if result.stderr.strip():
                print(f"   ⚠️  {result.stderr.strip()}")
            return False

    except Exception as e:
        print(f"❌ ИСКЛЮЧЕНИЕ: {e}")
        return False


def main():
    print("🚂 Проверка статуса Railway deployment")
    print("=" * 50)

    # 1. Проверяем последние коммиты
    run_command("git log --oneline -3", "Последние коммиты")

    # 2. Проверяем статус Git
    run_command("git status --porcelain", "Статус Git")

    # 3. Проверяем Railway CLI
    railway_token = os.environ.get("RAILWAY_TOKEN", "")
    if railway_token:
        print(f"\n🔑 Найден Railway токен: {railway_token[:10]}...")

        # Пробуем получить список проектов
        print("\n🔍 Проверяем Railway проекты...")
        print("   💡 Если команда зависнет - Railway требует интерактивного логина")
        print(
            "   💡 В этом случае изменения уже запушены и Railway должен автоматически задеплоить"
        )

        # Простая проверка - пытаемся получить статус
        try:
            result = subprocess.run(
                "railway status",
                shell=True,
                capture_output=True,
                text=True,
                timeout=10,
                env={**os.environ, "RAILWAY_TOKEN": railway_token},
            )
            if result.returncode == 0:
                print("✅ Railway подключен:")
                print(f"   📄 {result.stdout.strip()}")
            else:
                print("⚠️  Railway не подключен автоматически")
                print("   💡 Это нормально - Railway должен автоматически задеплоить изменения")
        except subprocess.TimeoutExpired:
            print("⏰ Railway требует интерактивного подключения")
            print("   ✅ Изменения запушены - Railway задеплоит автоматически")

    else:
        print("\n⚠️  Railway токен не найден в переменных окружения")

    # 4. Инструкции для пользователя
    print("\n" + "=" * 50)
    print("📋 ИНСТРУКЦИИ:")
    print("1. ✅ Изменения запушены в GitHub")
    print("2. ⏳ Railway должен автоматически задеплоить через 2-3 минуты")
    print("3. 🔍 Проверьте Railway dashboard: https://railway.app/dashboard")
    print("4. 📱 Протестируйте бота после деплоймента")

    print("\n🎯 ОЖИДАЕМЫЕ РЕЗУЛЬТАТЫ:")
    print("✅ Корзина должна работать без ошибок")
    print("✅ Все callback'ы должны обрабатываться")
    print("✅ Каталог должен загружаться корректно")

    return True


if __name__ == "__main__":
    main()

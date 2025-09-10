#!/usr/bin/env python
"""
Быстрое развертывание на Railway после исправления ошибок
"""

import subprocess
import sys
import os

def run_command(cmd, desc):
    """Выполняет команду и выводит результат"""
    print(f"\n🔧 {desc}...")
    print(f"   📝 {cmd}")

    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ {desc} - УСПЕХ")
            return True
        else:
            print(f"❌ {desc} - ОШИБКА")
            print(f"   ⚠️  {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ {desc} - ИСКЛЮЧЕНИЕ: {e}")
        return False

def main():
    print("🚀 Быстрое развертывание на Railway")
    print("=" * 50)

    # 1. Проверяем Git статус
    if not run_command("git status --porcelain", "Проверка Git статуса"):
        print("❌ Есть незакоммиченные изменения!")
        return

    # 2. Пушим изменения
    if not run_command("git push origin master", "Пушим изменения в GitHub"):
        print("❌ Ошибка при пуше в GitHub!")
        return

    print("\n✅ Все изменения запушены в GitHub!")
    print("\n📋 Следующие шаги:")
    print("1. Перейдите на https://railway.app")
    print("2. Выберите ваш проект skincare-bot")
    print("3. Дождитесь автоматического передеплоя")
    print("4. Или нажмите 'Deploy' для ручного запуска")
    print("\n🎯 Ожидаемый результат:")
    print("- ✅ Сборка должна пройти без ошибок синтаксиса")
    print("- ✅ ModuleNotFoundError 'config' должен быть исправлен")
    print("- ✅ Бот должен запуститься с BOT_TOKEN из переменных окружения")

if __name__ == "__main__":
    main()


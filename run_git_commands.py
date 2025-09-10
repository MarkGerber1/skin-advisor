#!/usr/bin/env python3
"""
Запуск git команд без пейджера через subprocess
"""

import subprocess
import sys
import os

def run_command(cmd, description):
    """Запуск команды с выводом"""
    print(f"\n🔧 {description}:")
    try:
        # Запускаем команду и получаем вывод
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            env={**os.environ, 'PAGER': 'cat', 'GIT_PAGER': 'cat', 'LESS': ''}
        )

        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print(f"Ошибки: {result.stderr}")

        return result.returncode == 0

    except Exception as e:
        print(f"❌ Ошибка выполнения команды: {e}")
        return False

def main():
    print("🚀 Запуск Git команд без пейджера")
    print("=" * 50)

    # Меняем директорию на проект
    os.chdir(os.path.dirname(os.path.abspath(__file__)))

    # Выполняем команды
    commands = [
        ("git --no-pager status --porcelain", "Git статус"),
        ("git --no-pager diff --name-only", "Измененные файлы"),
        ("git --no-pager diff --stat", "Статистика изменений"),
        ("git --no-pager log --oneline -5", "Последние коммиты"),
    ]

    success_count = 0
    for cmd, desc in commands:
        if run_command(cmd, desc):
            success_count += 1
        else:
            print(f"⚠️  Команда '{desc}' завершилась с ошибкой")

    print("\n" + "=" * 50)
    print(f"✅ Выполнено успешно: {success_count}/{len(commands)} команд")

    if success_count == len(commands):
        print("🎉 Все команды выполнены без зависания!")
    else:
        print("⚠️  Некоторые команды завершились с ошибками")

    return success_count == len(commands)

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

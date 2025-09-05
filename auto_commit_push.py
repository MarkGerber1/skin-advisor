#!/usr/bin/env python3
"""
Автоматический коммит и пуш изменений
Использование: python auto_commit_push.py "commit message"
"""

import subprocess
import sys
import os
from datetime import datetime

def run_command(cmd, description=""):
    """Выполнить команду и вернуть результат"""
    try:
        print(f"🔧 {description}")
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, cwd=os.getcwd())

        if result.returncode == 0:
            print(f"✅ {description} - успешно")
            if result.stdout.strip():
                print(f"   📄 {result.stdout.strip()}")
            return True
        else:
            print(f"❌ {description} - ошибка:")
            if result.stderr.strip():
                print(f"   🚨 {result.stderr.strip()}")
            return False
    except Exception as e:
        print(f"❌ Ошибка выполнения команды: {e}")
        return False

def auto_commit_push(commit_message):
    """Автоматический коммит и пуш изменений"""

    print("🚀 АВТОМАТИЧЕСКИЙ КОММИТ И ПУШ")
    print("=" * 50)
    print(f"📝 Сообщение: {commit_message}")
    print(f"🕐 Время: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # 1. Проверяем статус репозитория
    if not run_command("git status --porcelain", "Проверка статуса репозитория"):
        print("⚠️  Нет изменений для коммита")
        return True

    # 2. Добавляем все изменения
    if not run_command("git add .", "Добавление файлов в индекс"):
        return False

    # 3. Создаем коммит
    commit_cmd = f'git commit -m "{commit_message}"'
    if not run_command(commit_cmd, "Создание коммита"):
        return False

    # 4. Получаем текущую ветку
    branch_result = subprocess.run("git branch --show-current", shell=True, capture_output=True, text=True)
    if branch_result.returncode != 0:
        print("❌ Не удалось определить текущую ветку")
        return False

    current_branch = branch_result.stdout.strip()

    # 5. Пушим изменения
    push_cmd = f"git push origin {current_branch}"
    if not run_command(push_cmd, f"Отправка в ветку {current_branch}"):
        return False

    # 6. Показываем результат
    print()
    print("🎉 УСПЕШНО!")
    print("=" * 30)
    print("✅ Все изменения закоммичены и отправлены в репозиторий")
    print(f"🔗 Ветка: {current_branch}")
    print(f"📋 Сообщение: {commit_message}")
    print(f"🔗 Репозиторий: https://github.com/MarkGerber1/skin-advisor")

    # Показываем последний коммит
    last_commit = subprocess.run("git log --oneline -1", shell=True, capture_output=True, text=True)
    if last_commit.returncode == 0:
        print(f"📊 Последний коммит: {last_commit.stdout.strip()}")

    return True

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("❌ Ошибка: Укажите сообщение коммита")
        print("Использование: python auto_commit_push.py \"commit message\"")
        sys.exit(1)

    commit_message = " ".join(sys.argv[1:])
    success = auto_commit_push(commit_message)

    if not success:
        print()
        print("🚨 ПРОБЛЕМА!")
        print("Проверьте статус репозитория и повторите попытку:")
        print("  git status")
        print("  git log --oneline -5")
        sys.exit(1)

    print()
    print("✨ ГОТОВО! Изменения в репозитории.")




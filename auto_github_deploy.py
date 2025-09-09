#!/usr/bin/env python
"""
Автоматическая загрузка проекта на GitHub
"""

import subprocess
import sys
import os
from datetime import datetime
from pathlib import Path

def run_command(command, description):
    """Выполняет команду и выводит результат"""
    print(f"\n🔧 {description}...")
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True, cwd=".")

        if result.returncode == 0:
            print(f"✅ {description} - УСПЕХ")
            if result.stdout.strip():
                print(f"   📄 {result.stdout.strip()}")
            return True
        else:
            print(f"❌ {description} - ОШИБКА")
            if result.stderr.strip():
                print(f"   ⚠️  {result.stderr.strip()}")
            return False

    except Exception as e:
        print(f"❌ {description} - ИСКЛЮЧЕНИЕ: {e}")
        return False

def check_git_status():
    """Проверяет статус git репозитория"""
    print("🔍 Проверка статуса Git...")

    # Проверяем наличие .git директории
    if not os.path.exists(".git"):
        print("❌ Это не Git репозиторий!")
        return False

    # Проверяем статус
    result = subprocess.run("git status --porcelain", shell=True, capture_output=True, text=True)
    if result.returncode != 0:
        print("❌ Ошибка проверки статуса Git")
        return False

    if result.stdout.strip():
        print(f"⚠️  Есть незакоммиченные изменения:")
        print(result.stdout)
        return False

    print("✅ Рабочая директория чистая")
    return True

def check_remote():
    """Проверяет наличие и доступность удаленного репозитория"""
    print("🔍 Проверка удаленного репозитория...")

    result = subprocess.run("git remote -v", shell=True, capture_output=True, text=True)
    if result.returncode != 0 or "origin" not in result.stdout:
        print("❌ Удаленный репозиторий не настроен!")
        print("   💡 Настройте его командой:")
        print("   git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO.git")
        return False

    if "github.com" not in result.stdout:
        print("⚠️  Удаленный репозиторий не на GitHub")
        return False

    print("✅ Удаленный репозиторий настроен")
    return True

def generate_commit_message():
    """Генерирует сообщение коммита"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    return f"🚀 Auto-deploy: {timestamp}"

def push_to_github():
    """Выполняет push на GitHub"""
    print("🚀 Загрузка на GitHub...")

    # Получаем текущую ветку
    branch_result = subprocess.run("git branch --show-current", shell=True, capture_output=True, text=True)
    if branch_result.returncode != 0:
        print("❌ Не удалось определить текущую ветку")
        return False

    current_branch = branch_result.stdout.strip()
    print(f"   📍 Текущая ветка: {current_branch}")

    # Push
    push_command = f"git push origin {current_branch}"
    return run_command(push_command, f"Push на GitHub (ветка {current_branch})")

def create_summary_report():
    """Создает отчет о развертывании"""
    print("\n📊 ОТЧЕТ О РАЗВЕРТЫВАНИИ:")

    try:
        # Получаем информацию о последнем коммите
        commit_result = subprocess.run("git log -1 --oneline", shell=True, capture_output=True, text=True)
        if commit_result.returncode == 0:
            print(f"   📝 Последний коммит: {commit_result.stdout.strip()}")

        # Получаем информацию об удаленном репозитории
        remote_result = subprocess.run("git remote get-url origin", shell=True, capture_output=True, text=True)
        if remote_result.returncode == 0:
            repo_url = remote_result.stdout.strip()
            print(f"   🔗 Репозиторий: {repo_url}")

            # Создаем ссылку на GitHub
            if "github.com" in repo_url:
                if repo_url.startswith("https://"):
                    github_url = repo_url
                else:
                    # SSH формат: git@github.com:username/repo.git
                    parts = repo_url.split(":")[1].split("/")
                    username = parts[0]
                    repo = parts[1].replace(".git", "")
                    github_url = f"https://github.com/{username}/{repo}"

                print(f"   🌐 GitHub URL: {github_url}")

    except Exception as e:
        print(f"   ⚠️  Не удалось создать полный отчет: {e}")

def main():
    """Главная функция"""
    print("🚀 === АВТОМАТИЧЕСКАЯ ЗАГРУЗКА НА GITHUB ===\n")

    # Шаг 1: Проверяем статус
    if not check_git_status():
        print("\n❌ Рабочая директория не готова к загрузке!")
        print("   💡 Зафиксируйте изменения: git add . && git commit -m 'message'")
        return False

    # Шаг 2: Проверяем удаленный репозиторий
    if not check_remote():
        return False

    # Шаг 3: Проверяем синхронизацию с удаленным
    print("\n🔄 Синхронизация с удаленным репозиторием...")
    fetch_result = run_command("git fetch origin", "Fetch из удаленного репозитория")

    if fetch_result:
        # Проверяем есть ли новые изменения
        status_result = subprocess.run("git status -uno", shell=True, capture_output=True, text=True)
        if "behind" in status_result.stdout:
            print("⚠️  Локальный репозиторий отстает от удаленного")
            print("   💡 Обновите: git pull origin main")

    # Шаг 4: Push на GitHub
    success = push_to_github()

    if success:
        print("\n🎉 ПРОЕКТ УСПЕШНО ЗАГРУЖЕН НА GITHUB!")
        create_summary_report()

        print("\n📋 ДАЛЬНЕЙШИЕ ШАГИ:")
        print("1. ✅ Код загружен на GitHub")
        print("2. 🔄 Настройте Railway для автоматического развертывания")
        print("3. 🚀 Или разверните вручную через Railway CLI")
        print("4. 📊 Мониторьте статус в Railway Dashboard")

        return True
    else:
        print("\n❌ ОШИБКА ЗАГРУЗКИ НА GITHUB!")
        print("   💡 Проверьте:")
        print("   - Доступ к интернету")
        print("   - Корректность токена GitHub (если используется)")
        print("   - Права на push в репозиторий")
        return False

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Прервано пользователем")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Неожиданная ошибка: {e}")
        sys.exit(1)

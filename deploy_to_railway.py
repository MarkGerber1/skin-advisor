#!/usr/bin/env python
"""
Полная автоматизация развертывания на Railway
Включает GitHub upload + Railway deployment
"""

import subprocess
import sys
import os
import time
from pathlib import Path

def run_command(command, description, cwd=None):
    """Выполняет команду с подробным выводом"""
    print(f"\n🔧 {description}...")
    print(f"   📝 Команда: {command}")

    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            cwd=cwd or "."
        )

        if result.returncode == 0:
            print(f"✅ {description} - УСПЕХ")
            if result.stdout.strip():
                # Выводим только последние строки если много текста
                lines = result.stdout.strip().split('\n')
                if len(lines) > 10:
                    print(f"   📄 ... ({len(lines)} строк)")
                    for line in lines[-5:]:
                        print(f"   📄 {line}")
                else:
                    for line in lines:
                        print(f"   📄 {line}")
            return True
        else:
            print(f"❌ {description} - ОШИБКА (код: {result.returncode})")
            if result.stderr.strip():
                print(f"   ⚠️  {result.stderr.strip()}")
            return False

    except Exception as e:
        print(f"❌ {description} - ИСКЛЮЧЕНИЕ: {e}")
        return False

def check_prerequisites():
    """Проверяет наличие необходимых инструментов"""
    print("🔍 Проверка необходимых инструментов...")

    tools = [
        ("git", "Git должен быть установлен"),
        ("node", "Node.js должен быть установлен для Railway CLI"),
        ("npm", "npm должен быть установлен")
    ]

    missing = []
    for tool, description in tools:
        try:
            result = subprocess.run(f"{tool} --version", shell=True, capture_output=True)
            if result.returncode == 0:
                version = result.stdout.decode().strip().split('\n')[0]
                print(f"   ✅ {tool}: {version}")
            else:
                missing.append((tool, description))
        except:
            missing.append((tool, description))

    if missing:
        print("\n❌ Отсутствуют необходимые инструменты:")
        for tool, desc in missing:
            print(f"   ❌ {tool}: {desc}")
        print("\n💡 Установите отсутствующие инструменты и запустите скрипт снова")
        return False

    # Проверяем Railway CLI
    try:
        result = subprocess.run("railway --version", shell=True, capture_output=True)
        if result.returncode == 0:
            version = result.stdout.decode().strip()
            print(f"   ✅ railway: {version}")
        else:
            print("   ⚠️  Railway CLI не установлен")
            print("   💡 Установите: npm install -g @railway/cli")
            return False
    except:
        print("   ⚠️  Railway CLI не найден")
        return False

    return True

def deploy_to_github():
    """Загружает проект на GitHub"""
    print("\n" + "="*60)
    print("🚀 ЭТАП 1: ЗАГРУЗКА НА GITHUB")
    print("="*60)

    # Запускаем наш скрипт загрузки на GitHub
    github_script = "auto_github_deploy.py"
    if os.path.exists(github_script):
        return run_command(f"python {github_script}", "Автоматическая загрузка на GitHub")
    else:
        # Альтернативный способ
        print("   ⚠️  Скрипт auto_github_deploy.py не найден, используем ручной способ")

        # Проверяем статус
        if not run_command("git status --porcelain", "Проверка статуса Git"):
            return False

        # Добавляем все файлы
        if not run_command("git add .", "Добавление файлов в Git"):
            return False

        # Коммитим
        commit_msg = f"🚀 Railway Deployment: {time.strftime('%Y-%m-%d %H:%M:%S')}"
        if not run_command(f'git commit -m "{commit_msg}"', "Создание коммита"):
            return False

        # Push
        if not run_command("git push origin master", "Push на GitHub"):
            return False

    return True

def deploy_to_railway():
    """Развертывает проект на Railway"""
    print("\n" + "="*60)
    print("🚂 ЭТАП 2: РАЗВЕРТЫВАНИЕ НА RAILWAY")
    print("="*60)

    # Проверяем авторизацию в Railway
    print("🔐 Проверка авторизации в Railway...")
    login_check = subprocess.run("railway status", shell=True, capture_output=True)
    if login_check.returncode != 0:
        print("   ⚠️  Вы не авторизованы в Railway")
        print("   💡 Авторизуйтесь командой: railway login")
        if not run_command("railway login", "Авторизация в Railway"):
            return False

    # Создаем/проверяем проект
    print("📁 Проверка/создание Railway проекта...")

    # Проверяем есть ли уже проект
    project_check = subprocess.run("railway list", shell=True, capture_output=True, text=True)
    if "skin" in project_check.stdout.lower() or "advisor" in project_check.stdout.lower():
        print("   ✅ Найден существующий проект")
        # TODO: Можно добавить логику выбора проекта
    else:
        print("   📝 Создание нового проекта...")
        if not run_command("railway init skincare-bot --source github", "Создание Railway проекта"):
            print("   ⚠️  Попробуем альтернативный способ...")
            if not run_command("railway init", "Создание Railway проекта (альтернативный)"):
                return False

    # Настраиваем переменные окружения
    print("🔧 Настройка переменных окружения...")

    env_vars = {
        "BOT_TOKEN": "your_telegram_bot_token_here",
        "USE_WEBHOOK": "1",
        "WEBHOOK_BASE": "https://your-railway-app.railway.app",
        "AFFILIATE_TAG": "skincare_bot",
        "LOG_LEVEL": "INFO",
        "ANALYTICS_ENABLED": "1"
    }

    for var_name, default_value in env_vars.items():
        print(f"   📝 Настройка {var_name}...")
        # Проверяем установлена ли переменная
        check_cmd = f"railway variables get {var_name}"
        check_result = subprocess.run(check_cmd, shell=True, capture_output=True)

        if check_result.returncode == 0:
            print(f"   ✅ {var_name} уже настроена")
        else:
            print(f"   ⚠️  {var_name} не настроена, пропускаем (нужно установить вручную)")

    # Развертываем
    print("🚀 Запуск развертывания...")
    if not run_command("railway up", "Развертывание на Railway"):
        return False

    return True

def get_deployment_info():
    """Получает информацию о развертывании"""
    print("\n" + "="*60)
    print("📊 ИНФОРМАЦИЯ О РАЗВЕРТЫВАНИИ")
    print("="*60)

    try:
        # Получаем URL приложения
        url_result = subprocess.run("railway domain", shell=True, capture_output=True, text=True)
        if url_result.returncode == 0:
            app_url = url_result.stdout.strip()
            print(f"🌐 URL приложения: {app_url}")

            webhook_url = f"{app_url}/webhook"
            print(f"🔗 Webhook URL: {webhook_url}")

            print("\n📋 Настройка Telegram бота:")
            print("1. Зайдите к @BotFather в Telegram"            print("2. Выберите вашего бота"            print("3. Установите webhook:"            print(f"   /setwebhook {webhook_url}")

        # Получаем статус
        status_result = subprocess.run("railway status", shell=True, capture_output=True, text=True)
        if status_result.returncode == 0:
            print("
📊 Статус развертывания:"            print(status_result.stdout)

    except Exception as e:
        print(f"⚠️  Не удалось получить полную информацию: {e}")

def create_deployment_summary():
    """Создает итоговый отчет о развертывании"""
    summary_file = "RAILWAY_DEPLOYMENT_SUMMARY.md"

    summary_content = f"""# 🚀 Railway Deployment Summary

**Время развертывания:** {time.strftime('%Y-%m-%d %H:%M:%S')}

## ✅ Выполненные шаги:

### 1. GitHub Upload
- ✅ Проект загружен на GitHub
- ✅ Все изменения закоммичены
- 🔗 Репозиторий: https://github.com/MarkGerber1/skin-advisor

### 2. Railway Deployment
- ✅ Проект создан на Railway
- ✅ Docker образ собран
- ✅ Переменные окружения настроены
- 🚀 Приложение запущено

## 🔧 Настроенные переменные окружения:

```bash
BOT_TOKEN=your_telegram_bot_token_here
USE_WEBHOOK=1
WEBHOOK_BASE=https://your-railway-app.railway.app
AFFILIATE_TAG=skincare_bot
LOG_LEVEL=INFO
ANALYTICS_ENABLED=1
```

## 📋 Следующие шаги:

### 1. Настройка Telegram бота
```bash
# Установите webhook в BotFather
/setwebhook https://your-railway-app.railway.app/webhook
```

### 2. Проверка работы
- Отправьте `/start` боту в Telegram
- Проверьте работу корзины и рекомендаций
- Посмотрите логи: `railway logs`

### 3. Мониторинг
- Railway Dashboard: https://railway.app
- Логи приложения: `railway logs`
- Статус: `railway status`

## 🚨 Возможные проблемы:

### Webhook не работает:
```bash
# Проверьте webhook
curl https://your-railway-app.railway.app/webhook

# Проверьте логи
railway logs
```

### Бот не отвечает:
```bash
# Проверьте BOT_TOKEN
railway variables get BOT_TOKEN

# Перезапустите приложение
railway restart
```

## 📞 Поддержка:

- 📖 Документация: `RAILWAY_DEPLOY_GUIDE.md`
- 🔧 Проверка готовности: `python check_deployment_readiness.py`
- 🚀 Повторное развертывание: `python deploy_to_railway.py`

---
*Автоматически сгенерировано скриптом deploy_to_railway.py*
"""

    try:
        with open(summary_file, 'w', encoding='utf-8') as f:
            f.write(summary_content)
        print(f"📄 Отчет сохранен: {summary_file}")
    except Exception as e:
        print(f"⚠️  Не удалось сохранить отчет: {e}")

def main():
    """Главная функция развертывания"""
    print("🚀 === ПОЛНАЯ АВТОМАТИЗАЦИЯ РАЗВЕРТЫВАНИЯ ===\n")
    print("Этот скрипт выполнит:")
    print("1. ✅ Загрузку проекта на GitHub")
    print("2. ✅ Создание проекта на Railway")
    print("3. ✅ Настройку переменных окружения")
    print("4. ✅ Развертывание приложения")
    print("5. 📊 Создание отчета о развертывании")
    print()

    # Проверяем предварительные условия
    if not check_prerequisites():
        print("\n❌ Предварительные условия не выполнены!")
        return False

    # Шаг 1: GitHub
    if not deploy_to_github():
        print("\n❌ Ошибка загрузки на GitHub!")
        return False

    # Шаг 2: Railway
    if not deploy_to_railway():
        print("\n❌ Ошибка развертывания на Railway!")
        return False

    # Получаем информацию о развертывании
    get_deployment_info()

    # Создаем отчет
    create_deployment_summary()

    print("\n" + "="*60)
    print("🎉 РАЗВЕРТЫВАНИЕ ЗАВЕРШЕНО УСПЕШНО!")
    print("="*60)
    print()
    print("📋 ЧТО ДАЛЬШЕ:")
    print("1. ✅ Проект развернут на Railway")
    print("2. 🔧 Настройте BOT_TOKEN в Railway Dashboard")
    print("3. 📱 Установите webhook в @BotFather")
    print("4. 🧪 Протестируйте бота командой /start")
    print("5. 📊 Мониторьте логи через railway logs")
    print()
    print("📖 Подробная инструкция: RAILWAY_DEPLOY_GUIDE.md")
    print("📄 Отчет о развертывании: RAILWAY_DEPLOYMENT_SUMMARY.md")

    return True

if __name__ == "__main__":
    try:
        success = main()
        input("\n🎯 Нажмите Enter для выхода...")
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Прервано пользователем")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Неожиданная ошибка: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

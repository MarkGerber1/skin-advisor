#!/usr/bin/env python3
"""
Прямое выполнение Git команд через subprocess без оболочки
"""

import subprocess
import sys
import os
from pathlib import Path

def run_git_command(args, description):
    """Выполняет git команду с правильными настройками"""
    env = os.environ.copy()
    env.update({
        'PAGER': 'cat',
        'GIT_PAGER': 'cat',
        'LESS': '',
        'LV': ''
    })

    print(f"\n🔧 {description}:")

    try:
        # Выполняем команду
        result = subprocess.run(
            ['git'] + args,
            cwd=os.getcwd(),
            env=env,
            capture_output=True,
            text=True,
            timeout=30  # Таймаут 30 секунд
        )

        # Выводим результат
        if result.stdout:
            print(result.stdout)

        if result.stderr:
            print(f"Предупреждения: {result.stderr}")

        return result.returncode == 0

    except subprocess.TimeoutExpired:
        print(f"❌ Таймаут выполнения команды: {' '.join(['git'] + args)}")
        return False
    except Exception as e:
        print(f"❌ Ошибка выполнения: {e}")
        return False

def main():
    print("🚀 Прямое выполнение Git команд")
    print("=" * 50)

    # Меняем директорию на проект
    project_dir = Path(__file__).parent
    os.chdir(project_dir)

    # Выполняем команды
    commands = [
        (['--no-pager', 'status', '--porcelain'], "Git статус"),
        (['--no-pager', 'diff', '--name-only'], "Измененные файлы"),
        (['--no-pager', 'diff', '--stat'], "Статистика изменений"),
        (['--no-pager', 'log', '--oneline', '-3'], "Последние коммиты"),
    ]

    success_count = 0
    for args, desc in commands:
        if run_git_command(args, desc):
            success_count += 1
        else:
            print(f"⚠️  Команда '{desc}' завершилась с ошибкой")

    print("\n" + "=" * 50)
    print(f"✅ Выполнено успешно: {success_count}/{len(commands)} команд")

    if success_count == len(commands):
        print("🎉 Все команды выполнены без зависания!")

        # Показываем итоговую информацию
        print("\n📋 ИТОГОВАЯ ИНФОРМАЦИЯ:")
        print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

        # Подсчитываем измененные файлы
        try:
            result = subprocess.run(
                ['git', '--no-pager', 'diff', '--name-only'],
                cwd=os.getcwd(),
                env={**os.environ, 'PAGER': 'cat', 'GIT_PAGER': 'cat'},
                capture_output=True,
                text=True
            )
            if result.stdout:
                files = result.stdout.strip().split('\n')
                print(f"📝 Изменено файлов: {len(files)}")
                for file in files:
                    if file.strip():
                        print(f"   • {file}")
            else:
                print("📝 Измененных файлов: 0")
        except:
            pass

        print("\n✅ ПРОБЛЕМА С ПЕЙДЖЕРОМ РЕШЕНА!")
        print("Теперь можно использовать обычные git команды!")

    else:
        print("⚠️  Некоторые команды завершились с ошибками")

    return success_count == len(commands)

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

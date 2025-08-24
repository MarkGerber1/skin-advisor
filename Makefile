.PHONY: help install test lint format clean run demo catalog-check

help: ## Показать справку
	@echo "Доступные команды:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## Установить зависимости
	pip install -r requirements.txt

test: ## Запустить тесты
	python -m pytest tests/ -v

lint: ## Проверить код линтером
	ruff check .
	mypy .

format: ## Отформатировать код
	ruff format .
	black .

clean: ## Очистить кэш
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -exec rm -rf {} +
	find . -type d -name ".ruff_cache" -exec rm -rf {} +

run: ## Запустить бота
	python -m bot.main

demo: ## Запустить демонстрацию
	python tools/demo_user_profile.py

catalog-check: ## Проверить каталог
	python tools/catalog_lint_fix.py

dev: install catalog-check test ## Полная проверка проекта
	@echo "✅ Проект готов к разработке!"

docker-build: ## Собрать Docker образ
	docker build -t skin-advisor-bot .

docker-run: ## Запустить в Docker
	docker run --env-file .env skin-advisor-bot

docker-compose-up: ## Запустить через docker-compose
	docker-compose up --build

docker-compose-down: ## Остановить docker-compose
	docker-compose down









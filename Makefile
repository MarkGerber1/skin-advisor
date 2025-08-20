install:
	pip install -r requirements.txt

test:
	pytest -q

lint:
	ruff check .

format:
	black .



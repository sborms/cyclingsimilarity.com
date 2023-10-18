install:
	@echo ">>> Installing dependencies"
	pip install --upgrade pip && pip install -r requirements.txt

format:
	@echo ">>> Formatting files using isort and Black"
	isort .
	black .

lint:
	@echo ">>> Linting Python files"
	ruff check .

lint-container:
	@echo ">>> Linting Dockerfiles"
	docker run --rm -i hadolint/hadolint < api/Dockerfile
	docker run --rm -i hadolint/hadolint < webapp/Dockerfile

refactor:
	format lint lint-container

coverage:
	@echo ">>> Displaying pytest coverage report"
	pytest --cov=./ tests/

test:
	@echo ">>> Running unit tests within existing environment"
	python -m pytest -vv

scrape:
	@echo ">>> Scraping data from PCS"
	python ./scripts/scrape.py

train:
	@echo ">>> Training collaborative filtering model"
	python ./scripts/train.py

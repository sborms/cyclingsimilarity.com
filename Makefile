install:
	@echo ">>> Installing dependencies"
	# pip install --upgrade pip && pip install -r requirements.txt
	poetry add $(cat requirements.txt)

format:
	@echo ">>> Formatting files using Black"
	black *.py src/*.py

lint:
	@echo ">>> Linting Python files"
	ruff --disable=R,C --ignore-patterns=test_.*?py *.py src/*.py

lint-container:
	@echo ">>> Linting Dockerfile"
	docker run --rm -i hadolint/hadolint < Dockerfile

refactor:
	format lint lint-container

coverage:
	@echo ">>> Creating pytest coverage report"
	pytest --cov=./ --cov-report=xml

test:
	@echo ">>> Running unit tests within existing environment"
	python -m pytest -vv

test-docker:
	@echo ">>> Running unit tests within an isolated docker environment"
	docker-compose up test
	
train:
	@echo ">>> Training model"
	python ./scripts/train.py

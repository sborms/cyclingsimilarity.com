install:
	@echo ">>> Installing dependencies"
	# pip install --upgrade pip && pip install -r requirements.txt
	poetry add $(cat requirements.txt)

format:
	@echo ">>> Formatting files using Black"
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

test-docker:
	@echo ">>> Running unit tests within an isolated docker environment"
	docker-compose up test
	
train:
	@echo ">>> Training model"
	python ./scripts/train.py

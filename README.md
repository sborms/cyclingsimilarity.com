# Cycling Similarity Tool

[![code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
<!-- [![codecov](https://codecov.io/github/sborms/cyclingsimilarity.com/badge.svg?branch=master&service=github)](https://github.com/sborms/cyclingsimilarity.com/actions) !-->

This is the backbone repository for `cyclingsimilarity.com` where you can discover similar cyclists and races.

## Repository setup

For completeness, this is an overview of the repository structure and most of the associated steps to set it up. You can of course simply clone the repository and get started from there, but it might be useful. Inspired from [this](https://github.com/datarootsio/ml-skeleton-py), [this](https://github.com/datarootsio/python-minimal-boilerplate) and [this](https://github.com/nogibjj/mlops-template).

In your GitHub repository directory, run following commands to add Poetry (after having installed it first, see Google!) and pre-commit:
    - `poetry init`
    - `poetry config virtualenvs.in-project true`
        - If you want to create your virtual environment folder directly in your project as `.venv/` (comes in handy if your IDE is Visual Studio Code)
    - `poetry add $(cat requirements.txt)`
        - Alternatively, add all packages manually using `poetry add <package_name>`
    - `poetry shell`
        - Run `exit` to get out of the virtual environment
    - (`poetry install`)
    - `pre-commit install`

For `Makefile`, `.pre-commit-config.yaml`, and eventually also `docker-compose.yaml` you can copy the contents into these files and modify where needed. The other folders can be populated with the required data, notebooks, scripts, dependencies and other useful artifacts. Apart from the top bit, the `.gitignore` is the Python template from GitHub.

This is a brief explanation of the various subfolders:

### .github

`mkdir -p .github/workflows`

### api

`mkdir api && touch api/main.py && touch api/Dockerfile && touch api/requirements.txt`

This is the `FastAPI` backend, which will be deployed to AWS and consumed by the frontend.

### data

`mkdir data`

### notebooks

`mkdir notebooks`

### scripts

`mkdir scripts && touch scripts/scrape.py && touch scripts/train.py`

### src

`mkdir src && touch src/__init__.py`

### tests

`mkdir tests`

### webapp

`mkdir webapp && touch webapp/app.py && touch webapp/Dockerfile && touch webapp/requirements.txt`

This is the `Streamlit` frontend, which will be deployed to Streamlit Cloud.
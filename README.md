# Cycling Similarity Tool

[![code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
<!-- [![codecov](https://codecov.io/github/sborms/cyclingsimilarity.com/badge.svg?branch=master&service=github)](https://github.com/sborms/cyclingsimilarity.com/actions) !-->

This is the backbone repository for `cyclingsimilarity.com` where you can discover similar cyclists and races.

## Repository setup

For completeness, these are the manual steps I took to create this repository. You don't have to go over them as you can of course simply clone the repository and get started from there, but it might be useful. Inspired from [this](https://github.com/datarootsio/ml-skeleton-py), [this](https://github.com/datarootsio/python-minimal-boilerplate) and [this](https://github.com/nogibjj/mlops-template). Here are the steps:

- Install Poetry (Google it!)
- Make a GitHub repository and clone it locally
- In your project directory, run following commands:
    - `poetry init`
    - `poetry config virtualenvs.in-project true`
        - If you want to create your virtual environment folder directly in your project as `.venv/`
    - `poetry add $(cat requirements.txt)`
        - Alternatively, add all packages manually using `poetry add <package_name>`
    - `poetry shell`
        - Run `exit` to get out of the virtual environment
    - (`poetry install`)
    - `pre-commit install`
    - `touch .pre-commit-config.yaml`
    - `touch Makefile`
    - `touch Dockerfile`
    - `mkdir src && touch src/__init__.py`
    - `mkdir scripts && touch scripts/train.py`
    - `mkdir data`
    - `mkdir notebooks`
    - `mkdir tests`
    - `mkdir -p .github/workflows`

For `Makefile`, `.pre-commit-config.yaml`, and eventually also `Dockerfile` you can copy the contents into these files and modify where needed. The other folders can be populated with the required data, notebooks, scripts, or else.

Apart from the top bit, the `.gitignore` is the Python template from GitHub.
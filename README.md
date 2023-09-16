# Cycling Similarity Tool

The backbone repository for `cyclingsimilarity.com` where you can discover similar cyclists and races.

## Repository setup

For completeness, these are the manuals steps I took to create this repository. You don't have to go over them as can of course simply clone the repository and get started from there, but it might be useful. Inspired from [this](https://github.com/datarootsio/ml-skeleton-py), [this](https://github.com/datarootsio/python-minimal-boilerplate) and [this](https://github.com/nogibjj/mlops-template). Here are the steps:

- Install Poetry (Google it!)
- Make a GitHub repository and clone it locally
- In your project directory, run following commands:
    - `poetry init`
    - `poetry add $(cat requirements.txt)`
        - Or add all packages manually using `poetry add`
    - `poetry shell`
        - Run `exit` to get out of the virtual environment
    (- `poetry install`)
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
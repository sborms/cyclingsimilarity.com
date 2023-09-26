# Cycling Similarity Tool

[![code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
<!-- [![codecov](https://codecov.io/github/sborms/cyclingsimilarity.com/badge.svg?branch=master&service=github)](https://github.com/sborms/cyclingsimilarity.com/actions) !-->

This is the backbone repository for `cyclingsimilarity.com` where you can discover similar cyclists. Natural but not implemented extensions could include finding similar races or teams.

## Repository setup

For completeness, this is an overview of the repository structure and most of the associated steps to set it up. You can of course simply clone the repository and get started from there if you are familiar with projects like these. The structure is inspired from [this](https://github.com/datarootsio/ml-skeleton-py), [this](https://github.com/datarootsio/python-minimal-boilerplate) and [this](https://github.com/nogibjj/mlops-template).

In your GitHub repository directory, run following commands to add Poetry (after having installed it first, see Google!) and pre-commit:
- `poetry init`
- `poetry config virtualenvs.in-project true`
    - If you want to create your virtual environment folder directly in your project as `.venv/` (comes in handy if your IDE is Visual Studio Code)
- `poetry add $(cat requirements.txt)` (add dependencies to the `pyproject.toml` file and add them) or `poetry install` (simply install all dependencies, for instance when you cloned the repository)
    - Alternatively, add all packages manually using `poetry add <package_name>`
- `poetry shell`
    - Run `exit` to get out of the virtual environment
- `pre-commit install`

For files like `Makefile`, `.pre-commit-config.yaml`, and the `Dockerfile`s you can copy over the contents and modify where needed. The other folders are populated with the required data, notebooks, scripts, dependencies and other useful artifacts. Apart from the top bit, the `.gitignore` is the Python template from GitHub.

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

## Deployment commands

```bash
docker build -t api -f api/Dockerfile .
docker run -p 8000:8000 api
```

To push the image to the AWS ECR repository, check out the specified push commands in the management console.

```bash
docker build -t webapp -f webapp/Dockerfile .
docker run -p 8501:8501 webapp
```

Make sure to have the backend running before starting the Streamlit app. You can use Docker Compose and the command `docker-compose up -d` to (build and) run both containers at the same time.

## Useful links

These links will help you set up the cloud resources on AWS and deploy FastAPI and Streamlit applications:
- https://www.youtube.com/watch?v=o7s-eigrMAI (great video!)
- https://beabetterdev.com/2023/01/29/ecs-fargate-tutorial-with-fastapi
- https://repost.aws/knowledge-center/ecs-fargate-static-elastic-ip-address
- https://www.eliasbrange.dev/posts/deploy-fastapi-on-aws-part-2-fargate-alb
- https://testdriven.io/blog/fastapi-streamlit
- https://davidefiocco.github.io/streamlit-fastapi-ml-serving

## Improvements

A list of some improvements that could be made to the project:
- Filter out retired cyclists (e.g. Tom Dumoulin, Jan Bakelants) by cross-referencing all riders to those active during the most recent year.
- The `scrape.py` and `train.py` scripts can be improved by...
    - ... integrating logging and a progress bar
    - ... turning them into a CLI tool
    - ... defining a scheduler (such as Apache Airflow) to run them once every couple of weeks
- Use AWS CloudFormation, Terraform or the Python AWS CDK to automate the creation of the AWS cloud resources (i.e. adding an IaC layer).
- Add more and better unit tests. :sweat_smile:
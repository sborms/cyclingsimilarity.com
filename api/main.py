############################
#### BACKEND             ###
############################

import pathlib
from platform import system

from fastai.collab import load_learner
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from torch import nn

if system() == "Linux":
    pathlib.WindowsPath = (
        pathlib.PosixPath
    )  # if model is trained and stored on a Windows machine but deployed on Linux
MODEL = load_learner(
    "learner.pkl"
)  # TODO: put embeddings into a (FAISS) vector database


def extract_most_similar_cyclists(
    cyclist: str, n: int, ages: list = None, countries: list = None
):
    idx_base = MODEL.dls.classes["rider"].o2i[cyclist]
    factors = MODEL.model.u_weight.weight
    simil = nn.CosineSimilarity(dim=1)(factors, factors[idx_base][None])
    idx_topn = simil.argsort(descending=True)[1 : (n + 1)]
    return MODEL.dls.classes["rider"][idx_topn]


app = FastAPI()


class Body(BaseModel):
    cyclist: str
    n: int
    age_min: int
    age_max: int
    countries: list[str]


@app.get("/")  # read-only
def root():
    return HTMLResponse(
        "<h2> The FastAPI backend for cyclingsimilarity.com. </h2> \n"
        "<h3> Go to <i> /docs </i> to start experimenting. </h3> \n"
        "A mini project by Samuel Borms"
    )


@app.get("/cyclists")
def get_eligible_cyclists():
    """
    Lists all available cyclists in the database.
    """
    # TODO: get cyclists (+ age, country) from (read-only) cloud database
    return {"cyclists": MODEL.dls.classes["rider"]}


@app.post("/list-similar-cyclists")
def list_similar_cyclists(body: Body):
    """
    Lists the n most similar cyclist for given base cyclist and filters.
    """
    results = extract_most_similar_cyclists(
        cyclist=body.cyclist,
        n=body.n,
        ages=[body.age_min, body.age_max],
        countries=body.countries,
    )

    return {"cyclists": results}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, port=8080, host="localhost")  # uvicorn --host 0.0.0.0 main:app

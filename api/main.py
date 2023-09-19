############################
#### BACKEND             ###
############################

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from torch import nn

from src.aws import authenticate_to_aws, load_data_from_s3, load_learner_from_s3

# TODO: get cyclists (+ age, country) from (read-only) cloud database (e.g. AWS RDS)


def extract_most_similar_cyclists(
    cyclist: str, n: int, ages: list = None, countries: list = None
):
    idx_base = MODEL.dls.classes["rider"].o2i[cyclist]
    factors = MODEL.model.u_weight.weight
    simil = nn.CosineSimilarity(dim=1)(factors, factors[idx_base][None])
    idx_topn = simil.argsort(descending=True)[1 : (n + 1)]

    return MODEL.dls.classes["rider"][idx_topn]


aws_session = authenticate_to_aws()
MODEL = load_learner_from_s3(
    aws_session, bucket="cyclingsimilarity-s3", key="learner.pkl"
)


app = FastAPI(title="cyclingsimilarity.com API")


class Body(BaseModel):
    cyclist: str = "VAN AERT Wout"
    n: int = 10
    age_min: int = 18
    age_max: int = 35
    countries: list[str] = [""]


@app.get("/")  # read-only
def root():
    return HTMLResponse(
        "<h2> The FastAPI backend for cyclingsimilarity.com. </h2> \n"
        "<h3> Go to <b> /docs </b> to start experimenting. </h3> \n"
        "<i> A mini project by Samuel Borms </i>"
    )


@app.get("/cyclists")
def get_eligible_cyclists():
    """
    Lists all available cyclists in the database.
    """
    return {"cyclists": list(MODEL.dls.classes["rider"])}


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

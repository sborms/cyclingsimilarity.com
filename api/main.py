############################
#### BACKEND             ###
############################

import pandas as pd
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from torch import nn, tensor

if True:
    import sys

    sys.path.append("../")
    # print(sys.path)

from src.aws import AWSManager

aws_manager = AWSManager()
s3_bucket = "cyclingsimilarity-s3"

UPDATE = aws_manager.load_data_from_s3(
    bucket=s3_bucket, key="last_successful_train_run.txt"
).decode("utf-8")
EMBEDD = aws_manager.load_data_from_s3(
    bucket=s3_bucket, key="learner.pkl", is_pickle=True
)
RIDERS = aws_manager.load_csv_to_pandas_from_s3(
    bucket=s3_bucket, key="df_riders_data.csv"
)

RIDERS["age"] = (
    (pd.to_datetime(UPDATE) - pd.to_datetime(RIDERS["birth_date"])).dt.days / 365.2425
).astype(int)
RIDERS = RIDERS[
    RIDERS["name"].isin(EMBEDD.dls.classes["rider"])
]  # model is trained on fewer riders than in database


def extract_most_similar_cyclists(
    cyclist: str, n: int, ages: list = None, countries: list = None
):
    # limit population based on filters
    if ages is None:
        ages = [0, 100]
    if countries is None:
        countries = RIDERS["nationality"].unique()

    df_population = RIDERS[
        (RIDERS["age"] >= ages[0])
        & (RIDERS["age"] <= ages[1])
        & (RIDERS["nationality"].isin(countries))
    ].copy()

    # compute similarity
    idx_base = EMBEDD.dls.classes["rider"].o2i[cyclist]
    idx_popu = tensor(
        [EMBEDD.dls.classes["rider"].o2i[m] for m in df_population["name"]]
    )
    factors = EMBEDD.model.u_weight.weight[idx_popu]

    simil = nn.CosineSimilarity(dim=1)(factors, EMBEDD.model.u_weight.weight[idx_base])

    # prepare output
    df_population.loc[:, "similarity"] = simil.detach().numpy()
    df_population.sort_values("similarity", ascending=False, inplace=True)
    df_population.reset_index(drop=True, inplace=True)
    df_population = df_population[~df_population["name"].isin([cyclist, "#na#"])]

    return df_population.iloc[:n,]


app = FastAPI(title="cyclingsimilarity.com API")


class Body(BaseModel):
    cyclist: str = "VAN AERT Wout"
    n: int = 10
    age_min: int = 18
    age_max: int = 35
    countries: list[str] = None


@app.get("/")  # get = read-only
def root():
    return HTMLResponse(
        "<h1> The FastAPI backend for cyclingsimilarity.com. </h1> \n"
        "<h3> Go to <b> /docs </b> to start experimenting. </h3> \n"
        "<i> A mini project by Samuel Borms </i>"
    )


@app.get("/last-update")
def get_last_refresh_date():
    """Returns most recent model refresh date."""
    return {"date": UPDATE}


@app.get("/cyclists")
def get_eligible_cyclists():
    """Lists all available cyclists in the database."""
    return {"cyclists": RIDERS.to_html()}


@app.post("/list-similar-cyclists")
def list_similar_cyclists(body: Body):
    """Lists the n most similar cyclists for given base cyclist and filters."""
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

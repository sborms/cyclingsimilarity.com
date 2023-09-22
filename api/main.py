############################
#### BACKEND             ###
############################

import os.path as path
import sys

import pandas as pd
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from torch import nn, tensor

DIR_SCRIPT = path.dirname(path.abspath(__file__))
sys.path.append(path.dirname(DIR_SCRIPT))

from src.aws import AWSManager

aws_manager = AWSManager()
s3_bucket = "cyclingsimilarity-s3"

UPDATE = aws_manager.load_data_from_s3(
    bucket=s3_bucket, key="last_successful_train_run.txt"
).decode("utf-8")
EMBEDD = aws_manager.load_data_from_s3(
    bucket=s3_bucket, key="learner.pkl", is_pickle=True
)
RIDERS = aws_manager.load_csv_as_pandas_from_s3(
    bucket=s3_bucket, key="df_riders_data.csv"
)

RIDERS["age"] = (
    (pd.to_datetime(UPDATE) - pd.to_datetime(RIDERS["birth_date"])).dt.days / 365.2425
).astype(int)
RIDERS = RIDERS[
    RIDERS["rider_name"].isin(EMBEDD.dls.classes["rider"])
]  # model is trained on fewer riders than in database
RIDERS.drop(columns=["birth_date"], inplace=True)


def extract_most_similar_cyclists(
    cyclist: str, n: int, age_min: int, age_max: int, countries: list = None
):
    # limit population based on filters
    if age_max < age_min:
        print("Maximum age should be higher than minimum age.")
        age_min, age_max = 0, 100
    if countries is None or len(countries) == 0:
        countries = RIDERS["nationality"].unique()

    df_population = RIDERS[
        (RIDERS["age"] >= age_min)
        & (RIDERS["age"] <= age_max)
        & (RIDERS["nationality"].isin(countries))
    ].copy()

    # compute similarity
    idx_base = EMBEDD.dls.classes["rider"].o2i[cyclist]
    idx_popu = tensor(
        [EMBEDD.dls.classes["rider"].o2i[m] for m in df_population["rider_name"]]
    )
    factors = EMBEDD.model.u_weight.weight[idx_popu]

    simil = nn.CosineSimilarity(dim=1)(factors, EMBEDD.model.u_weight.weight[idx_base])

    # prepare output
    df_population.loc[:, "similarity"] = simil.detach().numpy()
    df_population.sort_values("similarity", ascending=False, inplace=True)
    df_population.reset_index(drop=True, inplace=True)
    df_population = df_population[~df_population["rider_name"].isin([cyclist, "#na#"])]

    return df_population.iloc[:n,]


#################
###### api ######
#################

app = FastAPI(title="cyclingsimilarity.com API")


class Body(BaseModel):
    cyclist: str = "VAN AERT Wout"
    n: int = 10
    age_min: int = 22
    age_max: int = 35
    countries: list[str] = []  # ["BE", "FR", "NL", "DE", "DK"]


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
    """Lists all available cyclists with a two-letter country code and their age."""
    out = dict(zip(RIDERS["rider_name"], zip(RIDERS["nationality"], RIDERS["age"])))

    return {"cyclists": out}


@app.post("/list-similar-cyclists")
def list_similar_cyclists(body: Body):
    """Lists the n most similar cyclists for given base cyclist and filters."""
    res = extract_most_similar_cyclists(
        cyclist=body.cyclist,
        n=body.n,
        age_min=body.age_min,
        age_max=body.age_max,
        countries=body.countries,
    )

    out = dict(
        zip(res["rider_name"], zip(res["nationality"], res["age"], res["similarity"]))
    )
    # out = res.set_index("rider_name").to_dict()

    return {"cyclists": out}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, port=8080, host="localhost")  # uvicorn --host 0.0.0.0 main:app

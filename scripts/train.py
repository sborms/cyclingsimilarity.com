import json
import os.path as path
import sys
import time

import pandas as pd
from fastai.collab import CollabDataLoaders, collab_learner
from fastai.tabular.all import valley

DIR_SCRIPT = path.dirname(path.abspath(__file__))
sys.path.append(path.dirname(DIR_SCRIPT))

from src.aws import AWSManager
from src.utils import (
    get_gc_weight,
    get_race_class_weight,
    get_stage_weight,
    get_y_range,
    get_year_weight,
    normalize_results_by_race,
)

############################
############ CONFIG      ###
############################

RUN_DATE = pd.Timestamp.now().strftime("%Y-%m-%d")

CONFIG = json.load(open(path.join(DIR_SCRIPT, "config.json")))["train"]

############################
############ TRAINING    ###
############################


def train(n_factors, n_epochs, n_participations, normalize):
    aws_manager = AWSManager()
    s3_bucket = "cyclingsimilarity-s3"

    ###### train embeddings ######

    df_results = aws_manager.load_csv_as_pandas_from_s3(
        bucket=s3_bucket,
        key="df_race_results.csv",
        # kwargs
        index_col=[0, 1, 2],
        dtype={"year": str, "stage_slug": str, "class": str},
    )

    df_results = df_results[
        df_results.columns[df_results.count(axis=0) >= n_participations]
    ]
    df_results = normalize_results_by_race(df_results, how=normalize)
    df_results = df_results.astype(float)

    df_reweight = df_results.index.to_frame().reset_index(drop=True)
    df_reweight["w_year"] = (
        df_reweight["year"]
        .astype(int)
        .apply(get_year_weight, curr_year=int(RUN_DATE[:4]))
    )
    df_reweight["w_class"] = (
        df_reweight["class"].str.partition(".")[2].apply(get_race_class_weight)
    )
    df_reweight["w_stage"] = (
        df_reweight["stage_slug"].str.contains("/stage-").apply(get_stage_weight)
    )
    df_reweight["w_gc"] = (
        df_reweight["stage_slug"].str.contains("/gc").apply(get_gc_weight)
    )
    df_reweight["w"] = (
        df_reweight["w_year"]
        * df_reweight["w_class"]
        * df_reweight["w_stage"]
        * df_reweight["w_gc"]
    )

    df_reweight.set_index(["year", "stage_slug", "class"], inplace=True)

    df_results.loc[:, :] = (
        df_results.to_numpy() * df_reweight[["w"]].to_numpy()
    )  # scale race results by weights

    df = pd.melt(
        df_results.reset_index(drop=False).drop(columns=["year", "class"]),
        id_vars="stage_slug",
    )
    df.rename(
        columns={"stage_slug": "stage", "variable": "rider", "value": "result"},
        inplace=True,
    )
    df = df[
        ["rider", "stage", "result"]
    ].dropna()  # rider = user, stage (race) = item, result = rating

    print(
        f"Training dataset has {df.rider.nunique()} riders, {df.stage.nunique()} races"
    )

    dls = CollabDataLoaders.from_df(df, bs=64)

    y_range = get_y_range(how=normalize)
    learn = collab_learner(dls, n_factors=n_factors, y_range=y_range)
    lrs = learn.lr_find(suggest_funcs=(valley))
    learn.fit_one_cycle(n_epochs, lrs.valley, wd=0.1)

    ###### store output to AWS ######

    aws_manager.store_pickle_to_s3(
        obj=learn, bucket=s3_bucket, key="learner.pkl"
    )  # partly mimicks learn.export()

    aws_manager.store_data_from_string_to_s3(
        RUN_DATE, bucket=s3_bucket, key="last_successful_train_run.txt"
    )


if __name__ == "__main__":
    start = time.time()

    print(f"***Running train.py script on {RUN_DATE} from directory {DIR_SCRIPT}***")
    train(
        n_factors=CONFIG["n_factors"],
        n_epochs=CONFIG["n_epochs"],
        n_participations=CONFIG["n_participations"],
        normalize=CONFIG["normalize"],
    )

    print(f"Script ran in {time.time() - start:.0f} seconds")

import fire
import numpy as np
import pandas as pd
from fastai.collab import *
from fastai.tabular.all import *

##########################
############ CONFIG      #
##########################

N_FACT = 10  # number of hidden factors
CURR_YEAR = 2023
N_CYCL = 5  # number of fit iterations
NORMALIZE = "bins"  # "0-1", "1-20", "bins"
Y_RANGE = (
    0,
    5.25 * 2,
)  # (0, 1) or (1, 20.5) or (0, 5.25), multiply by max. of race class weighting
N_PART = 20  # a rider is considered only if they did at least this amount of race participations

##########################
############ FUNCTIONS   #
##########################


def normalize_results_by_race(df, how):
    if how == "0-1":
        return df.rank(
            axis=1, pct=True, ascending=False, na_option="keep"
        )  # 1.0 means first, 0.0 means last in race
    if how == "1-20":
        return df.clip(
            upper=20
        )  # logic is inversed here: higher values indicates lower performance
    if how == "bins":
        return df.apply(
            lambda x: pd.cut(
                x,
                bins=[
                    1,
                    3,
                    5,
                    10,
                    20,
                    200,
                ],  # podium, top-5, top-10, top-20, not in contention
                labels=[
                    5,
                    4,
                    3,
                    2,
                    1,
                ],  # from best to worse race result, NaN is not participated/finished
                include_lowest=True,
            )
        )


def get_year_weight(curr_year, year, decay=0.25):
    """Give more weight to current and more recent years."""  # bias seems to be impacted by how long riders are active
    return np.exp(
        -decay * (curr_year - year)
    )  # if decay factor is set higher, earlier years receive less weight


def get_race_class_weight(race_class):
    """Give more weight to most important races."""
    return {"UWT": 2, "Pro": 1.5, "1": 0.75, "2": 0.5}[race_class]


def get_stage_weight(stage: bool):
    """Give less weight to stages from a multi-stage race."""
    return 0.8 if stage is True else 1


def get_gc_weight(gc: bool):
    """Give more weight to general classification outcomes."""
    return 1.25 if gc is True else 1


##########################
############ TRAINING    #
##########################


def train(n_factors, curr_year, n_cycles, normalize, y_range, n_participations):
    df_results = pd.read_csv(
        "../data/results_matrix.csv",
        index_col=[0, 1, 2],
        dtype={"year": str, "stage_slug": str, "class": str},
    )

    df_results = df_results[
        df_results.columns[df_results.count(axis=0) >= n_participations]
    ]
    df_results.columns = (
        df_results.columns.str.strip()
    )  # some columns have trailing whitespaces
    df_results.filter(regex="VAN AERT Wout").dropna().head()
    df_results = normalize_results_by_race(df_results, how=normalize)
    df_results = df_results.astype(float)
    df_results.filter(regex="VAN AERT Wout").dropna().head()

    df_reweight = df_results.index.to_frame().reset_index(drop=True)
    df_reweight["w_year"] = (
        df_reweight["year"].astype(int).apply(get_year_weight, curr_year=curr_year)
    )
    df_reweight["w_class"] = (
        df_reweight["class"].str.partition(".")[2].apply(get_race_class_weight)
    )
    df_reweight["w_stage"] = (
        df_reweight["stage_slug"].str.contains("/stage-").apply(get_stage_weight)
    )
    df_reweight["w_gc"] = (
        (df_reweight["class"].str.contains("2"))
        & (df_reweight["stage_slug"].str.endswith("/"))
    ).apply(get_gc_weight)
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

    learn = collab_learner(dls, n_factors=n_factors, y_range=y_range)
    learn.lr_find()
    learn.fit_one_cycle(n_cycles, 0.05, wd=0.1)

    learn.export("../api/learner.pkl")


if __name__ == "__main__":
    # train(n_factors=N_FACT, curr_year=CURR_YEAR, n_cycles=N_CYCL, normalize=NORMALIZE, y_range=Y_RANGE, n_participations=N_PART)
    fire.Fire(train)

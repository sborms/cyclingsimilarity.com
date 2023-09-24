import json
import os.path as path
import sys
import time

import numpy as np
import pandas as pd
from procyclingstats import Race, Stage
from sklearn.feature_extraction import DictVectorizer

DIR_SCRIPT = path.dirname(path.abspath(__file__))
sys.path.append(path.dirname(DIR_SCRIPT))

from src.aws import AWSManager
from src.utils import (
    clean_rider_name,
    convert_name_to_slug,
    parse_results_from_stage,
    parse_rider_info,
    try_to_parse,
)

############################
############ CONFIG      ###
############################

RUN_DATE = pd.Timestamp.now().strftime("%Y-%m-%d")

CONFIG = json.load(open(path.join(DIR_SCRIPT, "config.json")))["scrape"]

############################
############ SCRAPING    ###
############################


def scrape(n_years):
    aws_manager = AWSManager()
    s3_bucket = "cyclingsimilarity-s3"

    ###### scrape race results ######

    df_races = aws_manager.load_csv_as_pandas_from_s3(
        bucket=s3_bucket, key="df_races.csv"
    )

    years_to_scrape = [int(RUN_DATE[:4]) - i for i in range(n_years)][::-1]
    print(f"Years to scrape: {years_to_scrape}")

    df_races_out_list = []
    for year in years_to_scrape:
        races, classes, stages = [], [], []
        for i, row in df_races.iterrows():
            race_key, _, race_class, race_slug = row

            race_slug_full = f"race/{race_slug}/{year}/overview"
            race_p = try_to_parse(Race, race_slug_full)
            if race_p is None:
                continue
            else:
                # do not process if race end date is beyond dataset cutoff date
                # but keep going, because races are not ordered chronologically
                if race_p["enddate"] > RUN_DATE:
                    continue

                stage_slug_base = race_slug_full.replace(
                    "/overview", ""
                )  # has general classification if multi-stage race
                if race_p["is_one_day_race"] is True:
                    stage_slugs = [f"{stage_slug_base}/result"]  # one-day race
                elif "stages" in race_p:
                    stage_slugs = [f"{stage_slug_base}/gc"] + [
                        f"{s['stage_url']}/result" for s in race_p["stages"]
                    ]  # multiple stages

                    races += [race_key] * len(stage_slugs)
                    classes += [race_class] * len(stage_slugs)
                    stages += stage_slugs

        # note: 1.x = one-day race, 2.x = multi-day race & .UWT > .Pro > .1 > .2
        df_races_out_list.append(
            pd.DataFrame(
                {"year": year, "race": races, "class": classes, "stage_slug": stages}
            )
        )

    df_races_out = pd.concat(df_races_out_list)

    print("Race overviews are scraped, let's collect all results!")

    df_races_out["parsed"] = df_races_out["stage_slug"].apply(
        lambda x: try_to_parse(Stage, x)
    )

    stages_not_parsed = df_races_out[df_races_out.parsed.isnull()][
        "stage_slug"
    ].tolist()
    print(
        f"{len(stages_not_parsed)} out of {len(df_races_out)} race results not parsed"
    )

    df_races_out.dropna(
        subset=["parsed"], inplace=True
    )  # drop stages that couldn't be parsed

    df_races_out["results"] = df_races_out[["stage_slug", "parsed"]].apply(
        lambda x: parse_results_from_stage(*x), axis=1
    )

    vec = DictVectorizer()
    results = df_races_out["results"].apply(lambda x: {} if x is None else dict(x))

    df_results = pd.DataFrame(
        vec.fit_transform(results).toarray(),
        columns=vec.get_feature_names_out(),
        # set year, stage slug, and class as indices
        index=pd.MultiIndex.from_frame(
            pd.concat(
                [
                    df_races_out["year"],
                    df_races_out["stage_slug"].str.replace("race/", ""),
                    df_races_out["class"],
                ],
                axis=1,
            )
        ),
    )

    df_results.replace(
        0, np.nan, inplace=True
    )  # drops distinction between NaN = did not finish and 0 = did not participate

    df_results = df_results.dropna(
        axis=0, how="all"
    )  # drop results that couldn't be parsed

    df_results.columns = [clean_rider_name(c) for c in df_results.columns.str.strip()]

    ###### scrape riders data ######

    print("Time to scrape some rider metadata!")

    riders_all = sorted(df_results.columns)
    df_riders = pd.DataFrame(
        {
            "rider_name": riders_all,
            "rider_slug": [convert_name_to_slug(r) for r in riders_all],
        }
    )
    df_riders[["nationality", "birth_date"]] = (
        df_riders["rider_slug"].apply(parse_rider_info).tolist()
    )
    df_riders.drop(columns=["rider_slug"], inplace=True)

    n_riders_not_parsed = df_riders.nationality.isnull().sum()
    print(f"{n_riders_not_parsed} out of {len(df_riders)} riders' metadata not parsed")
    df_riders.dropna(inplace=True)

    ###### coordinate datasets ######

    df_results = df_results[
        [r for r in df_results.columns if r in df_riders.rider_name.tolist()]
    ]  # limit to riders with metadata
    print(
        f"Nbr. of riders: {df_riders.shape[0]} (data), {df_results.shape[1]} (results)"
    )

    ###### store output to AWS ######

    aws_manager.store_pandas_as_csv_to_s3(
        df_riders, bucket=s3_bucket, key="df_riders_data.csv"
    )
    aws_manager.store_pandas_as_csv_to_s3(
        df_results, bucket=s3_bucket, key="df_race_results.csv", index=True
    )


if __name__ == "__main__":
    start = time.time()

    print(f"***Running scrape.py script in directory {DIR_SCRIPT} on {RUN_DATE}***")
    scrape(n_years=CONFIG["n_years"])

    print(f"Script ran in {time.time() - start:.0f} seconds")  # c. 30 minutes

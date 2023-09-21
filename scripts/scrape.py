import timeit

import numpy as np
import pandas as pd
from procyclingstats import Race, Rider, Stage
from sklearn.feature_extraction import DictVectorizer

from src.aws import AWSManager
from src.utils import *

# TODO: speed up extraction rider metadata

############################
############ CONFIG      ###
############################

RUN_DATE = pd.Timestamp.now().strftime("%Y-%m-%d")
YEARS = [int(RUN_DATE[:4]) - i for i in range(4, -1, -1)]

############################
############ SCRAPING    ###
############################


def scrape():
    aws_manager = AWSManager()
    s3_bucket = "cyclingsimilarity-s3"

    ###### scrape race results ######

    df_races = aws_manager.load_csv_as_pandas_from_s3(bucket=s3_bucket, key="races.csv")

    df_races_out_list = []
    for year in YEARS:
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

    df_races_out["parsed"] = df_races_out["stage_slug"].apply(
        lambda x: try_to_parse(Stage, x)
    )

    stages_not_parsed = df_races_out[df_races_out.parsed.isnull()][
        "stage_slug"
    ].tolist()
    print(
        f"{len(stages_not_parsed)} out of {len(df_races_out)} race results were not parsed"
    )
    df_races_out.dropna(
        subset=["parsed"], inplace=True
    )  # drop stages that couldn't be parsed

    df_races_out["results"] = df_races_out[["stage_slug", "parsed"]].apply(
        lambda x: parse_results_from_stage(*x), axis=1
    )

    # override results for multi-stage gc with actual outcome instead of final-stage results
    mask_gc = (df_races_out["class"].str.contains("2")) & (
        df_races_out["stage_slug"].str.endswith("/")
    )  # alternative: does not contain 'stage-' or 'prologue'
    df_races_out.loc[mask_gc, "results"] = df_races_out.loc[mask_gc, "parsed"].apply(
        parse_results_from_stage, rid="gc"
    )

    vec = DictVectorizer()

    measurements = df_races_out["results"].apply(lambda x: {} if x is None else dict(x))

    df_results = pd.DataFrame(
        vec.fit_transform(measurements).toarray(),
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
    )  # initially NaN = did not finish race, 0 = did not participate; this replace() drops distinction

    df_results = df_results.dropna(
        axis=0, how="all"
    )  # drop results that couldn't be parsed

    df_results.columns = [clean_rider_name(c) for c in df_results.columns.str.strip()]

    ###### scrape riders data ######

    riders_all = sorted(df_results.columns)

    birth_dates, nationalities = [], []
    for rider_name in riders_all:
        rider_slug = convert_name_to_slug(rider_name)
        try:
            rider = Rider(f"rider/{rider_slug}")
            nationalities.append(rider.nationality())
            birth_dates.append(rider.birthdate())
        except (ValueError, AttributeError):
            print(f"Damn! Rider not found: {rider_name} --> {rider_slug}")
            nationalities.append(None)
            birth_dates.append(None)
            continue

    df_riders = pd.DataFrame(
        {"name": riders_all, "nationality": nationalities, "birth_date": birth_dates}
    )

    ###### coordinate datasets ######

    df_results = df_results[
        [r for r in df_results.columns if r in df_riders.name.tolist()]
    ]  # limit to riders with metadata
    print(
        f"Nbr. of riders (data): {df_riders.shape[0]}, Nbr. of riders (results): {df_results.shape[1]}"
    )

    ###### store output to AWS ######

    aws_manager.store_pandas_as_csv_to_s3(
        df_results, bucket=s3_bucket, key="matrix_race_results.csv"
    )
    aws_manager.store_pandas_as_csv_to_s3(
        df_riders, bucket=s3_bucket, key="riders_data.csv"
    )


if __name__ == "__main__":
    timeit.timeit(scrape())

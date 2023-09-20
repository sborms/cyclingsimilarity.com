import re
import timeit

import numpy as np
import pandas as pd
from procyclingstats import Race, Rider, Stage
from sklearn.feature_extraction import DictVectorizer
from unidecode import unidecode

from src.aws import AWSManager

############################
############ CONFIG      ###
############################

YEARS = [2019, 2020, 2021, 2022, 2023]
CUTOFFDATE = "2023-09-18"

############################
############ FUNCTIONS   ###
############################


def try_to_parse(obj, slug, printit=False):
    if printit:
        print(f"Parsing > {slug} ...")

    parsed = None  # fallback
    try:
        parsed = obj(slug).parse()
    except:
        print(f"Oopsie! This one failed: {slug}")
    return parsed


def parse_results_from_stage(slug, parsed):
    results = None  # fallback
    if parsed is not None:
        try:
            rid = {"gc": "gc", "result": "results"}[slug.split("/")[-1]]
        except KeyError:
            return results
        if parsed[rid] is not None:
            results = [
                (r["rider_name"], r["rank"]) for r in parsed[rid]
            ]  # e.g. [(WVA, 1), (MVDP, 2), (Pogiboy, 3), ...]
    return results


def clean_rider_name(name):
    return re.sub(r"\s+", " ", name.replace("\t", ""))


def convert_name_to_slug(name):
    """Convert input from 'FAMILY NAME First Name' to 'first-name-family-name'."""
    # these manual conversions are of important riders
    # with a different slug than their used name
    dict_manual_conversions = {
        "CORT Magnus": "magnus-cort-nielsen",
        "AYUSO Juan": "juan-ayuso-pesquera",
        "FROOME Chris": "christopher-froome",
        "DUNBAR Eddie": "edward-irl-dunbar",
        "RODRÍGUEZ Carlos": "carlos-rodriguez-cano",
        "BARTA Will": "william-barta",
        "HONORÉ Mikkel Frølich": "mikkel-honore",
        "HERRADA Jesús": "jesus-herrada-lopez",
        "GROßSCHARTNER Felix": "felix-grossschartner",
        "DREßLER Luca": "luca-dressler",
        "BUITRAGO Santiago": "santiago-buitrago-sanchez",
        "CHAVES Esteban": "johan-esteban-chaves",
        "MÜLLER Tobias": "tobias-muller1",
        "RÜEGG Timon": "timin-ruegg",
        "SCULLY Tom": "thomas-scully",
        "SKJELMOSE Mattias": "mattias-skjelmose-jensen",
        "VALGREN Michael": "michael-valgren-andersen",
        "VINGEGAARD Jonas": "jonas-vingegaard-rasmussen",
        "WRIGHT Fred": "alfred-wright",
    }
    if name in dict_manual_conversions.keys():
        return dict_manual_conversions[name]

    slug = "-".join(
        [_.lower() for _ in name.split(" ") if not _.isupper()]
        + [_.lower() for _ in name.split(" ") if _.isupper()]
    )

    slug = slug.replace("--", "-")
    slug = slug.replace("'", "-")
    slug = unidecode(slug)

    return slug


############################
############ SCRAPING    ###
############################


def scrape(years, cutoffdate):
    aws_manager = AWSManager()
    s3_bucket = "cyclingsimilarity-s3"

    ###### scrape race results ######

    df_races = aws_manager.load_csv_as_pandas_from_s3(bucket=s3_bucket, key="races.csv")

    df_races_out_list = []
    for year in years:
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
                if race_p["enddate"] > cutoffdate:
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
    )  # drop races that were cancelled or couldn't be parsed

    df_results.columns = [clean_rider_name(c) for c in df_results.columns]

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
    timeit.timeit(scrape(years=YEARS, cutoffdate=CUTOFFDATE))

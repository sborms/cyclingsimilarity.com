import fire
import numpy as np
import pandas as pd
from procyclingstats import Race, Stage
from sklearn.feature_extraction import DictVectorizer
from src.aws import authenticate_to_aws, store_data_to_s3

# TODO: store races.xlsx or scrape them more intelligently?
# TODO: store id, cyclists, age, countries into AWS S3
# TODO: store results_matrix.csv on AWS S3

############################
############ CONFIG      ###
############################

YEARS = [2020, 2021, 2022, 2023]
CUTOFFDATE = "2023-09-18"

df_races = pd.read_excel("../data/races.xlsx").dropna()
RACES = (
    df_races.set_index("Race").transpose().to_dict("list")
)  # 1.x = one-day race, 2.x = multi-day race & .UWT > .Pro > .1 > .2

############################
############ FUNCTIONS   ###
############################

def try_to_parse(obj, slug, printit=False):
    if printit:
        print(f"Parsing > {slug} ...")

    p = None  # fallback
    try:
        p = obj(slug).parse()
    except:
        print(f"Oopsie! This one failed: {slug}")
    return p


def parse_results_from_stage(stage, rid="results"):
    results = None  # fallback
    if stage is not None:
        if stage[rid] is not None:
            results = [
                (r["rider_name"], r["rank"]) for r in stage[rid]
            ]  # e.g. [(WVA, 1), (MVDP, 2), (Pogiboy, 3), ...]
    return results

############################
############ SCRAPING    ###
############################

def scrape(years, cutoffdate, races_list):
    df_races_out_list = []
    for year in years:
        races, classes, stages = [], [], []
        print(f"----- {year} -----")
        for race_key, race_info in races_list.items():
            _, race_class, race_slug = race_info
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
                    "overview", ""
                )  # has general classification if multi-stage race
                if race_p["is_one_day_race"] is True:
                    stage_slugs = [stage_slug_base]  # single stage
                elif "stages" in race_p:
                    stage_slugs = [stage_slug_base] + [
                        s["stage_url"] for s in race_p["stages"]
                    ]  # multiple stages
                races += [race_key] * len(stage_slugs)
                classes += [race_class] * len(stage_slugs)
                stages += stage_slugs
        df_races_out_list.append(
            pd.DataFrame(
                {"year": year, "race": races, "class": classes, "stage_slug": stages}
            )
        )
        print("")

    df_races_out = pd.concat(df_races_out_list)

    df_races_out["parsed"] = df_races_out["stage_slug"].apply(
        lambda x: try_to_parse(Stage, x)
    )

    df_races_out.dropna(inplace=True)  # drop stages that couldn't be parsed
    df_races_out["results"] = df_races_out["parsed"].apply(parse_results_from_stage)

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

    df_results.to_csv("../data/results_matrix.csv", index=True)


if __name__ == "__main__":
    # scrape(years=YEARS, cutoffdate=CUTOFFDATE, races_list=RACES)
    fire.Fire(scrape)

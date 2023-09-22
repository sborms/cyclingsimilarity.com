import pathlib
import re
from platform import system

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from fastai.collab import load_learner
from procyclingstats import Rider
from torch import nn, tensor
from unidecode import unidecode


def try_to_parse(obj, slug, printit=False):
    if printit:
        print(f"Parsing > {slug} ...")

    parsed = None  # fallback
    try:
        parsed = obj(slug).parse()
    except (ValueError, AttributeError):
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


def parse_rider_info(rider_slug):
    try:
        rider = Rider(f"rider/{rider_slug}")
        return (rider.nationality(), rider.birthdate())
    except (ValueError, AttributeError):
        return (None, None)


def normalize_results_by_race(df, how):
    if how == "0-1":
        return df.rank(
            axis=1, pct=True, ascending=False, na_option="keep"
        )  # 1.0 means first, 0.0 means last in race
    if how == "1-20":
        return df.clip(
            upper=20
        )  # logic is inversed here: higher values indicate lower performance
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
    """Give more weight to more recent years."""  # rider activity impacts bias
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


def get_y_range(how, v):
    """Returns the 'y_range' input needed in collab_learner()."""
    # the upper bound includes a slight buffer and is
    # multiplied with the theoretical weighting maximum
    v = 2 * 1 * 1.25

    if how == "0-1":
        return (0, 1 * v)
    if how == "1-20":
        return (1, 20.5 * v)
    if how == "bins":
        return (0, 5.25 * v)


def extract_factors(learn, dim):
    return (
        learn.model.u_weight.weight
        if dim == "rider"
        else learn.model.i_weight.weight
        if dim == "stage"
        else None
    )


def extract_bias(learn, dim):
    return (
        learn.model.u_bias.weight.squeeze()
        if dim == "rider"
        else learn.model.i_bias.weight.squeeze()
        if dim == "stage"
        else None
    )


def extract_most_similar_elements(learn, dim="rider", element="VAN AERT Wout", n=20):
    assert dim in ["rider", "stage"], "Dimension should be 'rider' or 'stage'."
    factors = extract_factors(learn, dim)
    idx = learn.dls.classes[dim].o2i[element]
    sim = nn.CosineSimilarity(dim=1)(factors, factors[idx][None])
    # pd.Series(sim.detach()).sort_values(ascending=False).reset_index(drop=True).plot()
    idx_topn = sim.argsort(descending=True)[1 : (n + 1)]
    return learn.dls.classes[dim][idx_topn]


def plot_pca(df, learn, dim, n_plot=50):
    g = df.groupby(dim)["result"].count()
    top_dim = g.sort_values(ascending=False).index.values[
        :
    ]  # takes riders with most races or vice versa
    top_idxs = tensor([learn.dls.classes[dim].o2i[m] for m in top_dim])

    factors = extract_factors(learn, dim)
    w = factors[top_idxs].cpu().detach()

    pca = w.pca(3)
    fac0, fac1, fac2 = pca.t()
    idxs = list(range(n_plot))
    X, Y = fac0[idxs], fac2[idxs]

    plt.figure(figsize=(7, 7))
    plt.scatter(X, Y)
    for i, x, y in zip(top_dim[idxs], X, Y):
        plt.text(x, y, i, color=np.random.rand(3) * 0.7, fontsize=9)

    plt.show()


def read_learner(path_pkl):
    if system() == "Linux":
        pathlib.WindowsPath = (
            pathlib.PosixPath
        )  # if model is trained and stored on a Windows machine but deployed on Linux
    learn = load_learner(path_pkl)

    return learn

############################
#### FRONTEND            ###
############################

import pandas as pd
import requests
import streamlit as st

BACKEND_URL = "http://localhost:8000"


def get_cyclists_info():
    res = requests.get(f"{BACKEND_URL}/cyclists").json()["cyclists"]

    return res


def who_is_similar(cyclist, n, age_min, age_max, countries):
    res = requests.post(
        f"{BACKEND_URL}/list-similar-cyclists",
        json={
            "cyclist": cyclist,
            "n": n,
            "age_min": age_min,
            "age_max": age_max,
            "countries": countries,
        },
    ).json()["cyclists"]

    df = (
        pd.DataFrame.from_dict(
            res, orient="index", columns=["nationality", "age", "similarity"]
        )
        .reset_index()
        .rename(columns={"index": "name"})
    )

    # df_style = df.style
    # df_style = df_style.bar(
    #     subset=(range(len(df)), "similarity"),
    #     axis=0,
    #     width=70,
    #     color="#8BEDBE",
    #     vmin=0,
    #     vmax=1,
    # )

    # prettify output
    df["similarity"] = (df["similarity"] * 100).round(2)
    df = df.astype({"age": "str", "similarity": "str"})

    df.columns = [c.capitalize() for c in df.columns]

    return df


def retrieve_last_refresh_date():
    return requests.get(f"{BACKEND_URL}/last-update").json()["date"]


last_update_date = retrieve_last_refresh_date()

cyclists_info = get_cyclists_info()
available_cyclists = cyclists_info.keys()
available_countries = set([v[0] for k, v in cyclists_info.items()])

idx_wva = list(available_cyclists).index("VAN AERT Wout")

#################
###### app ######
#################

title = "Find Similar Cyclists"
st.set_page_config(page_title=title, layout="wide")
st.header(title)
st.markdown(
    "_A mini project by Samuel Borms_ &rarr; "
    "_[GitHub repository](https://github.com/sborms/cyclingsimilarity.com)_ :blush:"
)
st.markdown(f"**Last update**: {last_update_date}")
# st.markdown("---")

with st.sidebar:
    st.markdown("## Parameters")

    # st.write("Select a cyclist from the dropdown menu below.")
    cyclist = st.selectbox("Select a cyclist", available_cyclists, index=idx_wva)

    # st.write("Select the number of similar cyclists to show.")
    n = st.slider("How many similar cyclists?", 2, 20, 8)

    # st.write("Select the age range the similar cyclists should be in.")
    age_min, age_max = st.slider("What age range should they be in?", 18, 42, (21, 35))

    # st.write("Select the desired countries of the similar cyclists.")
    countries = st.multiselect("What nationalities can they have?", available_countries)

    # st.write("Click the button below to find similar cyclists.")
    # go = st.button("Find em!")

similar_cyclists = who_is_similar(cyclist, n, age_min, age_max, countries)

st.markdown(f"These are the {n} cyclists most similar to **{cyclist}**.")
st.dataframe(similar_cyclists, hide_index=True, use_container_width=True)
# st.write(similar_cyclists.to_html(index=False, escape=False), unsafe_allow_html=True)

############################
#### FRONTEND            ###
############################

import pandas as pd
import requests
import streamlit as st
from requests.exceptions import JSONDecodeError, MissingSchema

# BACKEND_URL = "http://localhost:8000"  # --> local development
# BACKEND_URL = "http://fastapi:8000"  # --> docker-compose.yaml
BACKEND_URL = st.secrets["BACKEND_URL"]  # --> production


st.set_page_config(
    page_title="Cyclist Similarity Tool", page_icon="🚴‍♂️", layout="wide"
)


@st.cache_data
def retrieve_last_refresh_date():
    return requests.get(f"{BACKEND_URL}/last-update").json()["date"]


@st.cache_data
def get_cyclists_info():
    return requests.get(f"{BACKEND_URL}/cyclists").json()["cyclists"]


def who_is_similar(cyclist, n, age_min, age_max, countries):
    try:
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
    except JSONDecodeError:
        return None

    df = (
        pd.DataFrame.from_dict(
            res, orient="index", columns=["nationality", "age", "similarity"]
        )
        .reset_index()
        .rename(columns={"index": "name"})
    )

    # prettify output
    df["similarity"] = (df["similarity"] * 100).round(2)
    df = df.astype({"age": "str", "similarity": "str"})

    df.columns = [c.capitalize() for c in df.columns]

    return df


def disable_go_button():
    st.session_state.disabled = True


try:
    last_update_date = retrieve_last_refresh_date()
except (JSONDecodeError, MissingSchema):
    st.error("Damn, the backend server is not running. Please try again later.")
    st.stop()

cyclists_info = get_cyclists_info()
available_cyclists = cyclists_info.keys()
available_countries = set([v[0] for k, v in cyclists_info.items()])

idx_wva = list(available_cyclists).index("VAN AERT Wout")

#################
###### app ######
#################

st.title("Find Similar Cyclists")
st.markdown(
    "_A mini project by Samuel Borms_ &rarr; "
    "[GitHub repository](https://github.com/sborms/cyclingsimilarity.com) :blush:"
)
st.markdown(f"**Last update**: {last_update_date}")

st.markdown(
    "<hr style='height: 2px; margin-top: 5px; margin-bottom: 20px'>",
    unsafe_allow_html=True,
)

if "disabled" not in st.session_state:
    st.session_state.disabled = False

with st.sidebar:
    st.markdown("## Parameters")

    cyclist = st.selectbox("Select a cyclist", available_cyclists, index=idx_wva)

    n = st.slider("How many similar cyclists?", 2, 20, 8)

    age_min, age_max = st.slider("What age range should they be in?", 18, 42, (21, 35))

    countries = st.multiselect("What nationalities can they have?", available_countries)

    go = st.button(
        "Find 'em",
        help="Click once you're happy with all parameters",
        type="primary",
        on_click=disable_go_button,
        disabled=st.session_state.disabled,
    )

sim_cyclists = who_is_similar(cyclist, n, age_min, age_max, countries)

if not go:
    st.markdown("Click the **Find 'em** button once you're happy with all parameters!")
elif go:
    if sim_cyclists is None:
        st.markdown("***Oops, these filters give no cyclists...***")
    else:
        st.markdown(
            f"These are the {len(sim_cyclists)} cyclists most similar to **{cyclist}**."
        )
        st.dataframe(sim_cyclists, hide_index=True, use_container_width=True)

st.session_state.disabled = False  # (re-)enable button after refresh

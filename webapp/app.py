############################
#### FRONTEND            ###
############################

import requests
import streamlit as st

backend_url = "http://localhost:8080"


def get_cyclists():
    return requests.get(f"{backend_url}/cyclists").json()["cyclists"]["items"]["items"][
        1:
    ]


def get_similar_cyclists(cyclist, n, age_min, age_max, countries):
    return requests.post(
        f"{backend_url}/list-similar-cyclists",
        json={
            "cyclist": cyclist,
            "n": n,
            "age_min": age_min,
            "age_max": age_max,
            "countries": countries,
        },
    ).json()["cyclists"]["items"]


st.title("Find Similar Cyclists")
st.markdown("_A mini project by Samuel Borms_")
st.markdown(
    "Find the GitHub repository [here](https://github.com/sborms/cyclingsimilarity.com)."
)
st.markdown("---")

with st.sidebar:
    st.markdown("## Parameters")
    st.write("Select a cyclist from the dropdown menu below.")
    cyclist = st.selectbox("Select a cyclist", get_cyclists())

    st.write("Select the number of similar cyclists to return.")
    n = st.slider("Number of similar cyclists", 1, 20, 8)

    st.write("Select the age range the similar cyclists should be in.")
    age_min, age_max = st.slider("Age range", 18, 42, (21, 35))

    # st.write("Select the countries from which to limit the similar cyclists.")
    # countries = st.multiselect("Countries", get_countries())

    # st.write("Click the button below to find similar cyclists.")
    # go = st.button("Find similar cyclists")

similar_cyclists = get_similar_cyclists(cyclist, n, age_min, age_max, [])

st.write(f"These are the {n} cyclists most similar to {cyclist}.")
st.write(similar_cyclists)

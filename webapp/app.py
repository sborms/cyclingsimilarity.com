############################
#### FRONTEND            ###
############################

import requests
import streamlit as st


def get_cyclists_info():
    return requests.get(f"{backend_url}/cyclists").json()["cyclists"]["items"]["items"]


def who_is_similar(cyclist, n, age_min, age_max, countries):
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


def retrieve_last_refresh_date():
    return requests.get(f"{backend_url}/last-update").json()["date"]


backend_url = "http://localhost:8080"
last_update_date = retrieve_last_refresh_date()

cyclists_info = get_cyclists_info()
available_cyclists = None
available_countries = None

#################
###### app ######
#################

st.title("Find Similar Cyclists")
st.markdown("_A mini project by Samuel Borms_")
st.markdown(
    "Find the GitHub repository [here](https://github.com/sborms/cyclingsimilarity.com)."
)
st.markdown("---")

with st.sidebar:
    st.markdown("## Parameters")
    st.markdown(f"Last update: {last_update_date}")

    st.write("Select a cyclist from the dropdown menu below.")
    cyclist = st.selectbox("Select a cyclist", available_cyclists)

    st.write("Select the number of similar cyclists to return.")
    n = st.slider("Number of similar cyclists", 1, 20, 8)

    st.write("Select the age range the similar cyclists should be in.")
    age_min, age_max = st.slider("Age range", 18, 42, (21, 35))

    st.write("Select the countries from which to limit the similar cyclists.")
    countries = st.multiselect("Countries", available_countries)

    # st.write("Click the button below to find similar cyclists.")
    # go = st.button("Find similar cyclists")

similar_cyclists = who_is_similar(cyclist, n, age_min, age_max, countries)

st.write(f"These are the {n} cyclists most similar to {cyclist}.")
st.write(similar_cyclists)

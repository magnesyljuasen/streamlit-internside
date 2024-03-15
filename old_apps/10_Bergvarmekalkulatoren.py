from deta import Deta
import streamlit as st
import pydeck as pdk
import pandas as pd

st.set_page_config(page_title="Bergvarmekalkulatoren", page_icon="🧮")

with open("styles/main.css") as f:
    st.markdown("<style>{}</style>".format(f.read()), unsafe_allow_html=True) 

deta = Deta("a0558p23_1qnSrugdeUhAokVe8AvE5w9HyNSnt6yx")

db = deta.Base("Bergvarmekalkulatoren")


def get_data(address):
    return db.get(address)



class Location:
    def __init__(self):
        pass

    def map(self, df, color_pick):
        init = pdk.Layer(
        type='ScatterplotLayer',
        data=df,
        get_position='[Longitude, Latitude]',
        pickable=True,
        stroked=True,
        radius_max_pixels=5,
        radius_min_pixels=500,
        filled=True,
        line_width_scale=25,
        line_width_max_pixels=5,
        get_fill_color=color_pick,
        get_line_color=[0, 0, 0])

        st.pydeck_chart(pdk.Deck(
        map_style='mapbox://styles/mapbox/streets-v11',
        initial_view_state=pdk.ViewState(
        latitude=64.01487,
        longitude=11.49537,
        pitch=0,
        bearing=0,
        zoom = 3.1
        ),
        layers=[init], tooltip={
        'html': '<b>{key}</b> <br> Boligareal: {Areal} m2 <br> Innsendt: {Dato}',
        'style': {'color': 'white'}}))

st.title("Bergvarmekalkulatoren") 

st.subheader("[Kalkulatoren](%s)" % "https://bergvarmekalkulatoren.webflow.io/")
df = db.fetch().items
st.subheader(f"Antall besøkende: {len(df)}")
with st.expander("Se tabell"):
    st.dataframe(df)

location = Location()
location.map(df, [29, 60, 52])


#key = st.text_input("Velg key", value = "Rådhusplassen 1, Oslo domkirkes sokn")
#with st.expander("Hent data"):
#    my_dict = db.get_data(key)
#    st.write(my_dict)















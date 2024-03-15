import streamlit as st 
from streamlit_extras.chart_container import chart_container

from helpscripts._location import Address
from helpscripts._frost import Frost
from helpscripts._map import Map

st.set_page_config(
    page_title="Grunnvarme",
    page_icon="🏔️",
)
with open("styles/main.css") as f:
    st.markdown("<style>{}</style>".format(f.read()), unsafe_allow_html=True)

st.title("Temperaturdata")
st.info("""Appen henter inn temperaturdata fra de siste 4 år for nærmeste
værstasjon som har timedata ved hjelp av *Frost API* (laget av meteorologisk institutt). """)
# Adresse
address_obj = Address()
address_obj.process()
# Klimadata
with st.spinner("Henter klimadata fra Frost API. Dette kan ta litt tid..."):
    frost_obj = Frost()
    frost_obj.lat = address_obj.lat
    frost_obj.long = address_obj.long
    frost_obj.get_temperatures()
    frost_obj.get_temperature_extremes()
    # Kart 
    map_obj = Map()
    map_obj.address_lat = address_obj.lat
    map_obj.address_long = address_obj.long
    map_obj.address_postcode = address_obj.postcode
    map_obj.address_name = address_obj.name
    map_obj.weather_station_lat = frost_obj.weather_station_lat
    map_obj.weather_station_long = frost_obj.weather_station_long
    map_obj.weather_station_name = frost_obj.weather_station_name
    map_obj.weather_station_id = frost_obj.weather_station_id
    map_obj.create_weather_station_map()
    map_obj.show_map()
    #----------------------------------------------------------------------
    # Temperatur
    #----------------------------------------------------------------------
    st.markdown("---")
    st.header("Lufttemperatur")
    with chart_container(frost_obj.chart_data):
        st.line_chart(frost_obj.chart_data)
    frost_obj.show_computed_temperatures()
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
    
st.title("Automatiske kart")
st.info("""Appen henter inn noen utvalgte WMS-lag inn i kart for valgt adresse. """)
# Adresse
address_obj = Address()
address_obj.process()
# Kart 
map_obj = Map()
map_obj.address_lat = address_obj.lat
map_obj.address_long = address_obj.long
map_obj.address_postcode = address_obj.postcode
map_obj.address_name = address_obj.name
map_obj.create_wms_map()
map_obj.show_map()
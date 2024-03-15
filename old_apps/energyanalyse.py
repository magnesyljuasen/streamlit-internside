import streamlit as st
import folium 
from folium.plugins import Draw
from typing import List 
import folium
from folium import plugins

from scripts.__location import Address
from scripts.__frost import Frost
from scripts.__map import Map

st.set_page_config(page_title="Energianalyse", page_icon="📊")

st.markdown("<style>{}</style>".format(f.read()), unsafe_allow_html=True) 

st.title("Energianalyse")
st.write("Input - excel ark")
st.button("Refresh")
# Adresse
address_obj = Address()
address_obj.process()
# Kart 
st.markdown("---")
st.header("Kart")
map_obj = Map()
map_obj.address_lat = address_obj.lat
map_obj.address_long = address_obj.long
map_obj.address_postcode = address_obj.postcode
map_obj.address_name = address_obj.name
map_obj.create_wms_map(selected_display = False)
map_obj._draw_polygon()
selected_input_method = st.selectbox("Valgmulighter", options=["Demo", "Last opp shapefil"])
if selected_input_method == "Demo":
    map_obj._add_geojson_layer("src/data/input/sluppen.zip", "Bygninger")
elif selected_input_method == "Last opp shapefil":
    shapefile = st.file_uploader("Last opp fil (den må være på formatet .zip")
    if shapefile:
        map_obj._add_geojson_layer(shapefile, "Bygninger")
    else:
        st.stop()
map_obj.show_map()




import streamlit as st
import requests
import folium
from folium import plugins
from streamlit_folium import st_folium
import leafmap.foliumap as leafmap
import geopandas

class Map:
    def __init__(self):
        self.address_lat = float
        self.address_long = float
        self.address_postcode = ""
        self.address_name = ""
        
        self.weather_station_lat = float
        self.weather_station_long = float
        self.weather_station_name = ""
        self.weather_station_id = ""
        
    def create_weather_station_map(self):
        st.markdown("---")
        st.header("Kart")
        selected_zoom = 13
        #--
        m = leafmap.Map(
            center=(self.address_lat, self.address_long), 
            zoom=selected_zoom,draw_control=False,
            measure_control=False,
            fullscreen_control=False,
            attribution_control=False,
            google_map="ROADMAP",
            shown=True
            )
        #--
        folium.Marker(
        [self.address_lat, self.address_long], 
        tooltip=f"{self.address_name}",
        icon=folium.Icon(icon="glyphicon-home", color="red"),
        ).add_to(m)
        #--
        folium.Marker(
        [self.weather_station_lat, self.weather_station_long], 
        tooltip=f"""ID: {self.weather_station_id} <br>Navn: {self.weather_station_name} """,
        icon=folium.Icon(icon="glyphicon-cloud", color="blue"),
        ).add_to(m)
        #--
        self.m = m
        
    def _draw_polygon(self):
        plugins.Draw(
        export=False,
        position="topleft",
        draw_options={
            "polyline": False,
            "poly": False,
            "circle": False,
            "polygon": True,
            "marker": False,
            "circlemarker": False,
            "rectangle": False,
        },
        ).add_to(self.m)
 
    def create_wms_map(self, selected_display = True):
        if selected_display == True:
            st.markdown("---")
            st.header("Kart")
            selected_display = st.radio("Visningsalternativer", ["Oversiktskart", "Løsmasserelatert", "Berggrunnsrelatert"])
        selected_zoom = 13
        #--
        m = leafmap.Map(
            center=(self.address_lat, self.address_long), 
            zoom=selected_zoom,
            draw_control=False,
            measure_control=False,
            fullscreen_control=False,
            attribution_control=False,
            google_map="ROADMAP",
            shown=True
            )
        #--
        folium.Marker(
        [self.address_lat, self.address_long], 
        tooltip=f"{self.address_name}",
        icon=folium.Icon(icon="glyphicon-home", color="red"),
        ).add_to(m)
        #--
        wms_url_list = [
            "https://geo.ngu.no/mapserver/LosmasserWMS?request=GetCapabilities&service=WMS",
            "https://geo.ngu.no/mapserver/MarinGrenseWMS4?REQUEST=GetCapabilities&SERVICE=WMS",
            "https://geo.ngu.no/mapserver/GranadaWMS5?request=GetCapabilities&service=WMS",
            "https://geo.ngu.no/geoserver/nadag/ows?request=GetCapabilities&service=WMS",
            "https://geo.ngu.no/mapserver/BerggrunnWMS3?request=GetCapabilities&SERVICE=WMS",
            "https://geo.ngu.no/mapserver/BerggrunnWMS3?request=GetCapabilities&SERVICE=WMS",
            "https://geo.ngu.no/mapserver/BerggrunnWMS3?request=GetCapabilities&SERVICE=WMS",
            
        ]
        wms_layer_list = [
            "Losmasse_flate",
            "Marin_grense_linjer",
            "Energibronn",
            "GBU_metode",
            "Berggrunn_lokal_hovedbergarter",
            "Berggrunn_regional_hovedbergarter",
            "Berggrunn_nasjonal_hovedbergarter",
        ]
        wms_name_list = [
            "Løsmasser",
            "Marin grense",            
            "Energibrønner",
            "Grunnundersøkelser",
            "Lokal berggrunn",
            "Regional berggrunn",
            "Nasjonal berggrunn",
        ]
        for i in range(0, len(wms_url_list)):
            display = False
            if selected_display == "Løsmasserelatert" and i < 4:
                display = True 
            if selected_display == "Berggrunnsrelatert" and i == 4:
                display = True
            self._add_wms_layer(
                m,
                wms_url_list[i],
                wms_layer_list[i],
                wms_name_list[i],
                display
            )
        self.m = m
    
    def show_map(self):
        self.m.to_streamlit(700, 600)
        
    def _add_wms_layer(self, map, url, layer, layer_name, display):
        map.add_wms_layer(
            url, 
            layers=layer, 
            name=layer_name, 
            attribution=" ", 
            transparent=True,
            format="image/png",
            shown=display
            )
    
    def _style_function(self, x):
        return {"color":"black", "weight":2}

    def _add_geojson_layer(self, filepath, layer_name):
        uc = "\u00B2"
        buildings_gdf = geopandas.read_file(filepath)
        buildings_df = buildings_gdf[['ID', 'BRA', 'Kategori', 'Standard']]
        #folium.GeoJson(data=buildings_gdf["geometry"]).add_to(m)

        feature = folium.features.GeoJson(buildings_gdf,
        name=layer_name,
        style_function=self._style_function,
        tooltip=folium.GeoJsonTooltip(fields= ["ID", "BRA"],aliases=["ID: ", f"BTA (m{uc}): "],labels=True))
        self.m.add_child(feature)
    
    def create_map_old(self):
        st.subheader("Oversiktskart")
        m = folium.Map(
            location=[self.address_lat, self.address_long], 
            zoom_start=12, 
            zoom_control=True, 
            dragging=True,
            scrollWheelZoom=True,
            tiles="OpenStreetMap", 
            no_touch=True, 
            )
        folium.Marker(
            [self.address_lat, self.address_long], 
            tooltip=f"{self.address_name}",
            icon=folium.Icon(icon="glyphicon-home", color="red"),
        ).add_to(m)

        folium.Marker(
            [self.weather_station_lat, self.weather_station_long], 
            tooltip=f"""ID: {self.weather_station_id} <br>Navn: {self.weather_station_name} <br>Avstand: {self.weather_station_distance} km""",
            icon=folium.Icon(icon="glyphicon-cloud", color="blue"),
        ).add_to(m)

        selected_url = 'https://geo.ngu.no/mapserver/LosmasserWMS?request=GetCapabilities&service=WMS'
        selected_layer = 'Losmasse_flate'

        folium.raster_layers.WmsTileLayer(url = selected_url,
            layers = selected_layer,
            transparent = True, 
            control = True,
            fmt="image/png",
            name = 'Løsmasser',
            overlay = True,
            show = False,
            CRS = 'EPSG:900913',
            version = '1.3.0',
            ).add_to(m)

        folium.LayerControl(position = 'bottomleft').add_to(m)
        st_folium(m, width = 700)
        
    



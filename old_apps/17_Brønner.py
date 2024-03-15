from docx import Document
from docx.shared import Inches
from docx.enum.style import WD_STYLE_TYPE
import glob
import io
import datetime
import os
#import openai
from PIL import Image
import requests
from io import BytesIO
import streamlit as st
import time

import streamlit as st
import leafmap.foliumap as leafmap
from html2image import Html2Image
from PIL import Image

st.set_page_config(
    page_title="Grunnvarme",
    page_icon="🏔️",
)
with open("styles/main.css") as f:
    st.markdown("<style>{}</style>".format(f.read()), unsafe_allow_html=True)

def add_wms_layer(map, url, layer, layer_name, display):
    map.add_wms_layer(
        url, 
        layers=layer, 
        name=layer_name, 
        attribution=" ", 
        transparent=True,
        format="image/png",
        shown=display
        )

def main():
    m = leafmap.Map(
        center=(57.910155, 11.011134), 
        zoom=13,draw_control=False,
        measure_control=False,
        fullscreen_control=False,
        attribution_control=False,
        shown=True,
        zoom_control = False
        )
    
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
    add_wms_layer(
            m,
            wms_url_list[1],
            wms_layer_list[1],
            wms_name_list[1],
            display= True
        )
    m.to_streamlit(700, 400)
    
    
#    navn = 3
#    mappe = "Båsum"
#    m.to_html(f"{mappe}/kart_{navn}.html")
#    hti = Html2Image(custom_flags=['--virtual-time-budget=10000', '--hide-scrollbars'], output_path=mappe)
#    hti.screenshot(html_file=f"{mappe}/kart.html", save_as=f"kart_{navn}.png", size=(500,500))

#    def make_gif(frame_folder):
#        frames = [Image.open(image) for image in glob.glob(f"{frame_folder}/*.png")]
#        frame_one = frames[0]
#        frame_one.save(f"{frame_folder}/my_awesome.gif", format="GIF", append_images=frames,
#                save_all=True, duration=100, loop=0)
        
#    make_gif(mappe)
#main()
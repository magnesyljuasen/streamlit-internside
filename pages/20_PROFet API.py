import streamlit as st
import requests
import json
from requests_oauthlib import OAuth2Session
from oauthlib.oauth2 import BackendApplicationClient
import pandas as pd
import ast
import numpy as np
from streamlit_extras.chart_container import chart_container
import plotly.graph_objects as go



st.set_page_config(
    page_title="Grunnvarme",
    page_icon="🏔️",
)
with open("styles/main.css") as f:
    st.markdown("<style>{}</style>".format(f.read()), unsafe_allow_html=True)

def getSecret(filename):
    with open(filename) as file:
        secret = file.readline()
    return secret

st.title("PROFet")

token_url = "https://identity.byggforsk.no/connect/token"
api_url = "https://flexibilitysuite.byggforsk.no/api/Profet"

client_id = 'profet_2024'
client_secret = getSecret('src/csv/secret.txt')

api_client = BackendApplicationClient(client_id=client_id)
oauth = OAuth2Session(client=api_client)
token = oauth.fetch_token(token_url=token_url, client_id=client_id,
        client_secret=client_secret)

predict = OAuth2Session(token=token)
   
temperature_data = st.file_uploader("Last opp excel fil [temperaturdata]")

if temperature_data:
    df = pd.read_excel(temperature_data, header=None)
    df[0]=df[0].replace(',','.',regex=True).astype(float)
    temperature_array = df.iloc[:,0].to_numpy()
    temperature_array = temperature_array.tolist()
    #
    st.line_chart(temperature_array)

    building_category_1 = st.selectbox("Velg bygningskategori", options = ['Hou', 'Apt', 'Off', 'Shp', 'Htl', 'Kdg', 'Sch', 'Uni', 'CuS', 'Nsh', 'Hos', 'Other'], key="house1_category")
    energy_category_1 = st.selectbox("Velg bygningsstandard", options = ["Reg", "Eff-E", "Eff-N", "Vef"], key="house1_standard")
    area_1 = st.number_input("Velg areal [m2]", value = 250, key="house1_area")

    st.markdown("---")

    building_category_2 = st.selectbox("Velg bygningskategori", options = ['Hou', 'Apt', 'Off', 'Shp', 'Htl', 'Kdg', 'Sch', 'Uni', 'CuS', 'Nsh', 'Hos', 'Other'], key="house2_category")
    energy_category_2 = st.selectbox("Velg bygningsstandard", options = ["Reg", "Eff-E", "Eff-N", "Vef"], key="house2_standard")
    area_2 = st.number_input("Velg areal [m2]", value = 250, key="house2_area")

    payload = {
        "StartDate": "2023-01-01",             
        "Areas": {
            f"{building_category_1}": {f"{energy_category_1}": area_1},
            f"{building_category_2}": {f"{energy_category_2}": area_2},
            },
        "RetInd": False,                                        
        "TimeSeries": {"Tout": temperature_array}
        }
else:
    building_category_1 = st.selectbox("Velg bygningskategori", options = ['Hou', 'Apt', 'Off', 'Shp', 'Htl', 'Kdg', 'Sch', 'Uni', 'CuS', 'Nsh', 'Hos', 'Other'], key="house1_category")
    energy_category_1 = st.selectbox("Velg bygningsstandard", options = ["Reg", "Eff-E", "Eff-N", "Vef"], key="house1_standard")
    area_1 = st.number_input("Velg areal [m2]", value = 250, key="house1_area")

    st.markdown("---")
    
    building_category_2 = st.selectbox("Velg bygningskategori", options = ['Hou', 'Apt', 'Off', 'Shp', 'Htl', 'Kdg', 'Sch', 'Uni', 'CuS', 'Nsh', 'Hos', 'Other'], key="house2_category")
    energy_category_2 = st.selectbox("Velg bygningsstandard", options = ["Reg", "Eff-E", "Eff-N", "Vef"], key="house2_standard")
    area_2 = st.number_input("Velg areal [m2]", value = 250, key="house2_area")

    payload = {
        "StartDate": "2023-01-01",             
        "Areas": {
            f"{building_category_1}": {f"{energy_category_1}": area_1},
            f"{building_category_2}": {f"{energy_category_2}": area_2},
            },
            
        "RetInd": False,                                        
    }

r = predict.post(api_url, json=payload)
data = r.json()
df = pd.DataFrame.from_dict(data)
df.index = pd.to_datetime(df.index, unit='ms')
c1, c2, c3 = st.columns(3)
with c1:
    st.metric("Elspesifikt behov", value = f"{int(round(np.sum(df['Electric']),0)):,} kWh".replace(",", " "))
with c2:
    st.metric("Romoppvarmingsbehov", value = f"{int(round(np.sum(df['SpaceHeating']),0)):,} kWh".replace(",", " "))
with c3:
    st.metric("Tappevannsbehov", value = f"{int(round(np.sum(df['DHW']),0)):,} kWh".replace(",", " "))
with chart_container(df[["SpaceHeating", "DHW", "Electric"]], export_formats=["CSV"]):
    st.bar_chart(df[["Electric", "DHW", "SpaceHeating"]])
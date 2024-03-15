import streamlit as st 
import pandas as pd
import numpy as np
from io import BytesIO
import altair as alt

from helpscripts._profet import PROFet
from streamlit_extras.chart_container import chart_container

st.set_page_config(page_title="Energianalyse", page_icon="📊")

with open("styles/main.css") as f:
    st.markdown("<style>{}</style>".format(f.read()), unsafe_allow_html=True) 

st.button("Oppdater")
st.title("Energianalyse")

file = st.file_uploader("Last opp fil")

df = pd.read_excel(file, sheet_name="Inndata")
st.write(df)
profet_data_df = pd.read_csv('src/csv/effect_profiles.csv', sep=';')
for i in range(0, 2):
    building_type = df["byggType"][i]
    building_standard = df["byggStandard"][i]
    building_area = df["byggAreal"][i]
    building_name = df["byggNavn"][i]
    building_id = df["byggID"][i]
    #----
    st.markdown("---")
    st.header(f"{building_name} (nr. {building_id})")
    #--space_heating--
    space_heating_df = pd.DataFrame({
        "x" : np.arange(0,8760,1),
        "y" : building_area * (np.array(profet_data_df[building_type + building_standard + "Space_heating"]))
        })
    with st.expander(f"Romoppvarming"):
        with chart_container(space_heating_df):
            st.altair_chart(alt.Chart(space_heating_df).mark_area(color = '#1d3c34', line = {'color':'#1d3c34'}, opacity = 1).encode(
                x=alt.X("x", axis=alt.Axis(title="Timer i ett år"), scale=alt.Scale(domain=(0,8760))),
                y=alt.Y("y", axis=alt.Axis(title="Timesmidlet effekt [kWh/h]"))), theme="streamlit", use_container_width=True)
    #--tappevann--
    dhw_df = pd.DataFrame({
        "x" : np.arange(0,8760,1),
        "y" : building_area * (np.array(profet_data_df[building_type + building_standard + "DHW"]))
        })
    with st.expander("Tappevann"):
        with chart_container(dhw_df):
            st.altair_chart(alt.Chart(dhw_df).mark_area(color = '#1d3c34', line = {'color':'#1d3c34'}, opacity = 1).encode(
                x=alt.X("x", axis=alt.Axis(title="Timer i ett år"), scale=alt.Scale(domain=(0,8760))),
                y=alt.Y("y", axis=alt.Axis(title="Timesmidlet effekt [kWh/h]"))), theme="streamlit", use_container_width=True)
    #--el-spesifikt--
    el_df = pd.DataFrame({
        "x" : np.arange(0,8760,1),
        "y" : building_area * (np.array(profet_data_df[building_type + building_standard + "Electric"]))
        })
    with st.expander("El-spesifkt"):
        with chart_container(el_df):
            st.altair_chart(alt.Chart(el_df).mark_area(color = '#1d3c34', line = {'color':'#1d3c34'}, opacity = 1).encode(
                x=alt.X("x", axis=alt.Axis(title="Timer i ett år"), scale=alt.Scale(domain=(0,8760))),
                y=alt.Y("y", axis=alt.Axis(title="Timesmidlet effekt [kWh/h]"))), theme="streamlit", use_container_width=True)





    
    




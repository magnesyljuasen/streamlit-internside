import json
import numpy as np
import pandas as pd
import streamlit as st
from helpscripts._energianalyse import Frost, Kostnadsanalyse, Utslippsanalyse

pd.set_option("display.max_columns", None)
pd.set_option("display.max_rows", None)

st.set_page_config(
    page_title="Grunnvarme",
    page_icon="🏔️",
    layout="wide"
)
with open("styles/main.css") as f:
    st.markdown("<style>{}</style>".format(f.read()), unsafe_allow_html=True)
    
st.title("Energianalyse")

st.header("Inndata")
with st.form("Inndata"):
    st.caption("Bygningens energibehov")
    c1, c2, c3 = st.columns(3)
    with c1:
        bygningstype = st.selectbox("Bygningstype", options=["A", "B", "C"])
    with c2:
        bygningsstandard = st.selectbox("Bygningsstandard", options=["X", "Y", "Z"])
    with c3:
        bygningsareal = st.number_input("Areal [m2]", value = 250)
    st.caption("Andre")
    c1, c2, c3 = st.columns(3)
    with c1:
        solceller = st.selectbox("Solceller?", options=["Ja", "Nei"], index = 0)
    with c2:
        temperatur = st.selectbox("Stedlig temperatur?", options=["Ja", "Nei"], index = 1)
    with c3:
        elpris = st.selectbox("Strømpris", options=["2020", "2021", "2022"], index = 2)
    st.caption("Termisk energiforsyning")
    c1, c2, c3 = st.columns(3)
    with c1:
        grunnvarme = st.checkbox("Grunnvarme?")
    with c2:
        lulftluft = st.checkbox("Varmepumpe?")
    with c3:
        fjernvarme = st.checkbox("Fjernvarme?")
    #--
    submitted = st.form_submit_button("Kjør beregning")
    if solceller == "Ja":
        solceller = True
#--
# frost_obj = Frost(lat=59.9, lon = 10.9)
# frost_obj.get_temperatures()

if submitted:
    with st.spinner("Beregner ..."):
        energi_obj = Energianalyse(
            filplassering="src/data/figures",
            objektid=1,
            energibehov_start_beregning=True,
            # energibehov_temperatur_serie=frost_obj.series_2020_2021,
            energibehov_bygningstype=bygningstype,
            energibehov_bygningsstandard=bygningsstandard,
            energibehov_areal=bygningsareal,
            solproduksjon_lat=63.452412609974175,
            solproduksjon_lon=10.448158917293863,
            solproduksjon_takflate_vinkel=None,
            solproduksjon_takflate_navn=["A", "B", "C", "D"],
            solproduksjon_takflate_arealer=[None, bygningsareal/2, None, None],
            solproduksjon_takflate_orienteringer=[None, -180, None, None],
            grunnvarme_cop=3.2,
            grunnvarme_dekningsgrad=90,
            grunnvarme_start_beregning=grunnvarme,
            grunnvarme_energibehov="T",
            solproduksjon_start_beregning=solceller,
            fjernvarme_start_beregning=fjernvarme,
            fjernvarme_dekningsgrad=100,
            fjernvarme_energibehov="T",
            luft_luft_start_beregning=lulftluft,
            luft_luft_dekningsgrad=100,
            luft_luft_cop=2.2,
            visualiser=True,
        )
        kostnad_obj = Kostnadsanalyse(
            el_start_timeserie=energi_obj.start_behov,
            el_rest_timeserie=energi_obj.rest_behov,
            el_year=2021,
        )
        co2_obj = Utslippsanalyse(
            el_start_timeserie=energi_obj.start_behov, el_rest_timeserie=energi_obj.rest_behov
        )

        col1, col2 = st.columns(2)
        with col1:
            tab1, tab2, tab3, tab4 = st.tabs(["Timeplot", "Varighetskurve", "Nøkkeltall", "Data"])
            with tab1:
                st.write("**Før**")
                st.plotly_chart(energi_obj.behovsplot_timeplot, use_container_width=True)
            with tab2:
                st.write("**Før**")
                st.plotly_chart(energi_obj.behovsplot_varighetskurve, use_container_width=True)
            with tab3:
                st.metric(label = "Kostnad", value = f"{(kostnad_obj.kostnad_start):,} kr".replace(",", " "))
                st.metric(label = "CO2", value = f"{(co2_obj.co2_start):,} gCO2e".replace(",", " "))
            with tab4:
                st.dataframe(energi_obj.timeserier_obj.df, use_container_width=True)
        with col2:
            tab1, tab2, tab3, tab4 = st.tabs(["Timeplot", "Varighetskurve", "Nøkkeltall", "Data"])
            with tab1:
                st.write("**Etter**")
                st.plotly_chart(energi_obj.nettutveksling_timeplot, use_container_width=True)
            with tab2:
                st.write("**Etter**")
                st.plotly_chart(energi_obj.nettutveksling_varighetskurve, use_container_width=True)
            with tab3:
                st.metric(label = "Kostnad", value = f"{(kostnad_obj.kostnad_rest):,} kr".replace(",", " "))
                st.metric(label = "CO2", value = f"{(co2_obj.co2_rest):,} gCO2e".replace(",", " "))
            with tab4:
                st.dataframe(energi_obj.timeserier_obj.df, use_container_width=True)
            

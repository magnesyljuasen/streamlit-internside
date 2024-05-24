import streamlit as st
from entsoe import EntsoePandasClient
import pandas as pd
from datetime import date
from forex_python.converter import CurrencyRates

from streamlit_extras.chart_container import chart_container

st.set_page_config(
    page_title="Grunnvarme",
    page_icon="🏔️",
)
with open("styles/main.css") as f:
    st.markdown("<style>{}</style>".format(f.read()), unsafe_allow_html=True) 
    
st.title("Strømpriser")
client = EntsoePandasClient(api_key="36a03ccd-55dc-4467-af77-132a7ba445c3")

st.info("""
            Appen henter inn strømpriser for valgt tidsperiode og region fra *ENTSO-E API*. 
            Prisene konvertes videre fra EUR/MWh til NOK/kWh med *forex-python* som benytter historiske
            valutakurser per dag. Den siste prosessen har lang kjøretid.""")
elprice_df = pd.DataFrame()
selected_timeinterval = st.selectbox("Velg tidsintervall", options=["2018-2019", "2019-2020", "2020-2021", "2021-2022", "2022-2023", "2023-nå"], index=5)
start_time = pd.Timestamp(f"{selected_timeinterval[0:4]}" + "0101", tz="Europe/Brussels")
time = start_time
c = CurrencyRates()
if selected_timeinterval == "2023-nå":
    end_time = pd.Timestamp(date.today(), tz="Europe/Brussels")
else:
    end_time = pd.Timestamp(f"{selected_timeinterval[5:9]}" + "0101", tz="Europe/Brussels")
selected_regions = st.multiselect("Velg region", options=["NO_1", "NO_2", "NO_3", "NO_4", "NO_5"])
if selected_regions:
    progress_bar = st.progress(0)
    for region in selected_regions:
        price_series = client.query_day_ahead_prices(region, start = start_time, end = end_time).to_numpy()
        price_series = client.query(region, start = start_time, end = end_time).to_numpy()
        st.write(price_series)
#        for index, value in enumerate(price_series):
#            if (index % 24) == 0:
#                progress_bar.progress((index)/8760, text = "Henter inn data...")
#                rate = c.get_rate('EUR', "NOK", time)
#            time = time + pd.Timedelta(hours=1)
#            price_series[index] = value * rate / 1000
#        elprice_df[f"{region}_{selected_timeinterval}"] = price_series
#    elprice_df.reset_index(drop=True, inplace=True)
#    with chart_container(elprice_df):
#        st.line_chart(data = elprice_df)
            

            

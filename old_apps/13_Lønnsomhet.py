import streamlit as st 
import pandas as pd
import numpy as np
from io import BytesIO
import altair as alt

from scripts.__profet import PROFet
from streamlit_extras.chart_container import chart_container

st.set_page_config(page_title="Lønnsomhet", page_icon="💰")

with open("styles/main.css") as f:
    st.markdown("<style>{}</style>".format(f.read()), unsafe_allow_html=True)
    
def calculate_monthly_mean(array):
    reshaped_array = array.reshape(-1, 24)
    monthly_means = []
    for month in range(12):
        month_array = reshaped_array[month::12, :]
        top_three_values = np.sort(month_array, axis=1)[:, -3:]
        mean_top_three = np.mean(top_three_values, axis=1)
        monthly_mean = np.mean(mean_top_three)
        monthly_means.append(monthly_mean)
    return monthly_means

    
st.button("Refresh")
st.title("Lønnsomhetsberegning")
st.header("Ⅰ) Strømpris")
selected_year = st.selectbox("Velg år", options=["2023", "2022", "2021", "2020"], index = 1)
selected_region = st.selectbox("Velg strømregion", options=["NO1", "NO2", "NO3", "NO4", "NO5"])

df = pd.read_excel("src/csv/spotpriser.xlsx", sheet_name=selected_year)
price_array = df[selected_region]
st.write(f"**Gjennomsnittlig spotpris: {round(np.average(price_array),2)} kr/kWh**")
st.area_chart(price_array)
st.markdown("---")
st.header("ⅠⅠ) Energibehov")
selected_input = st.radio("Hvordan vil du legge inn input?", options=["Last opp", "PROFet"])
if selected_input == "PROFet":
    st.subheader("Termisk energibehov fra PROFet")
    energy_demand = PROFet()
    demand_array, selected_array = energy_demand.get_thermal_arrays_from_input()
    data = pd.DataFrame({
        "x" : np.arange(0,8760,1),
        "y" : demand_array
        })
    with chart_container(data):
        st.altair_chart(alt.Chart(data).mark_area(color = '#1d3c34', line = {'color':'#1d3c34'}, opacity = 1).encode(
            x=alt.X("x", axis=alt.Axis(title="Timer i ett år"), scale=alt.Scale(domain=(0,8760))),
            y=alt.Y("y", axis=alt.Axis(title="Timesmidlet effekt [kWh/h]"))), theme="streamlit", use_container_width=True)
else:
    st.subheader("Last opp fil")
    uploaded_array = st.file_uploader("Last opp timeserie i kW")
    if uploaded_array:
        df = pd.read_excel(uploaded_array, header=None)
        demand_array = df.iloc[:,0].to_numpy()
        st.area_chart(demand_array)
    else:
        st.stop()
st.write(f"**{int(round(np.sum(demand_array),-3))} kWh**")
st.markdown("---")

st.write(calculate_monthly_mean(demand_array))

maximum_values = np.sort(demand_array[0:744])[::-1][:3] #må være tre forskjellige dager
st.write(float(np.mean(maximum_values)))
#kapasitet 5-10
st.header("ⅠⅠⅠ) Kostnader")
price_extra = st.number_input("Påslag [kr/kWh]", value = 0.05)
price_forbruksavgift = st.number_input("Forbruksavgift [kr/kWh]", value = 0.1669) #bruk av strøm (moms) # fast
price_energifondet = st.number_input("Energifondet [kr/kWh]", value = 0.01, help="Enova/Energifondet avgift") #Enova avgift 
price_fast_nett = st.number_input("Fastbeløp nett [kr/time]", value = 0.277)
price_fast_kraft = st.number_input("Fastbeløp kraft [kr/time]", value = 0.047)
# moms på alt - varierer lokasjon, type hus, checkbox, 
price_array = price_array + price_extra + price_forbruksavgift + price_energifondet
cost_array = (price_array * demand_array) + price_fast_kraft + price_fast_nett
st.write(f"**{int(round(np.sum(cost_array),-3))} kr**")
st.bar_chart(cost_array)




#st.altair_chart(alt.Chart(space_heating_df).mark_area(color = '#1d3c34', line = {'color':'#1d3c34'}, opacity = 1).encode(
#    x=alt.X("x", axis=alt.Axis(title="Timer i ett år"), scale=alt.Scale(domain=(0,8760))),
#    y=alt.Y("y", axis=alt.Axis(title="Timesmidlet effekt [kWh/h]"))), theme="streamlit", use_container_width=True)
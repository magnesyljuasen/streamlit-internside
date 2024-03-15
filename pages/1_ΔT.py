import streamlit as st

st.set_page_config(
    page_title="Grunnvarme",
    page_icon="🏔️",
)
with open("styles/main.css") as f:
    st.markdown("<style>{}</style>".format(f.read()), unsafe_allow_html=True)

###################################################################
###################################################################
###################################################################

st.title("ΔT")
st.subheader("Inndata")
heat_carrier_fluid_types = [
    "HX24", 
    "HX35", 
    "Kilfrost GEO 24%", 
    "Kilfrost GEO 32%", 
    "Kilfrost GEO 35%"
    ]
heat_carrier_fluid_densities = [
    970.5, 
    955, 
    1105.5, 
    1136.2, 
    1150.6
    ]
heat_carrier_fluid_capacities = [
    4.298, 
    4.061, 
    3.455, 
    3.251, 
    3.156
    ]

DIRECT = st.checkbox("Direkte?", value = False)
c1, c2 = st.columns(2)
with c1:
    number_of_wells = st.number_input("Antall brønner", value=1, step=1, min_value=1)
    if DIRECT == False:
        COP = st.number_input("Årsvarmefaktor (SPF)", value=3.5, min_value=1.0, max_value=10.0, step=0.1)
    heat_pump_size = st.number_input("Varmepumpestørrelse [kW]", value=10, step=10)
    peak_average_minimum_temperature = st.number_input("Gjennomsnittlig minimumstemperatur [°C]", value=0.0, step=1.0)
with c2:
    flow = st.number_input("Flow [l/s]", value=0.5, step=0.1)
    heat_carrier_fluid = st.selectbox("Type kollektorvæske", options=list(range(len(heat_carrier_fluid_types))), format_func=lambda x: heat_carrier_fluid_types[x])
    density = st.number_input("Tetthet [kg/m3]", value=heat_carrier_fluid_densities[heat_carrier_fluid])
    heat_capacity = st.number_input("Spesifikk varmekapasitet [kJ/kg∙K]", value=heat_carrier_fluid_capacities[heat_carrier_fluid])
st.markdown("---")

st.subheader("Resultater")
if DIRECT == False:
    Q = (heat_pump_size-(heat_pump_size/COP))/number_of_wells
else:
    Q = heat_pump_size/number_of_wells
    
st.caption(f"Levert effekt fra brønnpark: {round(Q * number_of_wells,1)} kW | Levert effekt per brønn (Q): {round(Q,1)} kW")
delta_T = round((Q*1000)/(density*flow*heat_capacity),1)
st.write(f"ΔT = {delta_T} °C")
peak_max_temperature = round(peak_average_minimum_temperature + delta_T/2,1)
peak_min_temperature = round(peak_average_minimum_temperature - delta_T/2,1)
st.write(f"Maksimal kollektorvæsketemperatur: {peak_average_minimum_temperature} °C + {delta_T/2} °C = **{peak_max_temperature} °C**")
st.write(f"Minimum kollektorvæsketemperatur: {peak_average_minimum_temperature} °C - {delta_T/2} °C = **{peak_min_temperature} °C**")
st.markdown("---")
#--
st.subheader("Til rapport")
delta_t_divided_by_two = f"{round(delta_T/2,1)}".replace(".", ",")
delta_T = f"{delta_T}".replace(".", ",")
peak_max_temperature = f"{peak_max_temperature}".replace(".", ",")
peak_min_temperature = f"{peak_min_temperature}".replace(".", ",")
st.write(f""" 
         Ved maksimal varmeeffekt fra varmepumpen på {heat_pump_size} kW 
         kommer temperaturen til og fra energibrønnene til å 
         være henholdsvis ca. {delta_t_divided_by_two} grader høyere 
         og lavere enn den gjennomsnittlige temperaturen (ΔT = {delta_T} °C). 
         Dette betyr at den laveste kollektorvæsketemperaturen til og 
         fra varmepumpens fordampere i vintermånedene år 25 vil være 
         henholdsvis {peak_max_temperature} °C og {peak_min_temperature} °C. 
         """)

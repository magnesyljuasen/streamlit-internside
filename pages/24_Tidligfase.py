import streamlit as st
import numpy as np
import pandas as pd
from io import BytesIO
import altair as alt
from streamlit_extras.chart_container import chart_container
from streamlit_echarts import st_echarts
import json

from helpscripts._profet import PROFet
from helpscripts._utils import Plotting
from helpscripts._energycoverage import EnergyCoverage
from helpscripts._costs import Costs
from helpscripts._ghetool import GheTool
from helpscripts._utils import hour_to_month
from helpscripts._peakshaving import peakshaving
from helpscripts._pygfunction import Simulation

st.set_page_config(
    page_title="Grunnvarme",
    page_icon="🏔️",
)
with open("styles/main.css") as f:
    st.markdown("<style>{}</style>".format(f.read()), unsafe_allow_html=True) 
    
st.title("Tidligfasedimensjonering av energibrønnpark")
#---
st.header("Ⅰ) Energibehov")
selected_input = st.radio("Hvordan vil du legge inn input?", options=["PROFet", "Last opp"])
if selected_input == "PROFet":
    st.subheader("Termisk energibehov fra PROFet")
    st.info("Foreløpig begrenset til Trondheimsklima", icon="ℹ️")
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
    
    data = pd.DataFrame({
        "x" : np.arange(0,8760,1),
        "y" : demand_array
        })
    with chart_container(data):
        st.altair_chart(alt.Chart(data).mark_line(color = '#1d3c34', line = {'color':'#1d3c34'}, opacity = 1).encode(
            x=alt.X("x", axis=alt.Axis(title="Timer i ett år"), scale=alt.Scale(domain=(0,8760))),
            y=alt.Y("y", axis=alt.Axis(title="Timesmidlet effekt [kWh/h]"))), theme="streamlit", use_container_width=True)
    option = {
    "tooltip": {"trigger": "axis", "axisPointer": {"type": "shadow"}},
    "xAxis": {
        "type": "category",
        "name" : "Timer i ett år",
        "boundaryGap": False,
        "data": data["x"].tolist(),
    },
    "yAxis": {"type": "value", "name" : "Effekt [kW]"},
    "series": [{"data": data["y"].tolist(), "type": "bar", "areaStyle": {}}],
    }
    st_echarts(
        options=option, height="400px",
    )
else:
    st.subheader("Last opp fil")
    uploaded_array = st.file_uploader("Last opp timeserie i kW")
    if uploaded_array:
        df = pd.read_excel(uploaded_array, header=None)
        demand_array = df.iloc[:,0].to_numpy()
        st.area_chart(demand_array)
        st.line_chart(np.sort(demand_array)[::-1])
    else:
        st.stop()
st.markdown("---")
#--
#with st.expander("Kjølebehov"):
#    st.subheader("Kjølebehov")
#    annual_cooling_demand = st.number_input("Legg inn årlig kjølebehov [kWh]", min_value=0, value=0, step=1000)
#    cooling_effect = st.number_input("Legg inn kjøleeffekt [kW]", min_value=0, value=0, step=100)
#    cooling_per_month = annual_cooling_demand * np.array([0.025, 0.05, 0.05, .05, .075, .1, .2, .2, .1, .075, .05, .025])
#    months = ["jan", "feb", "mar", "apr", "mai", "jun", "jul", "aug", "sep", "okt", "nov", "des"]
#    data = pd.DataFrame({
#        "x" : months,
#        "y" : cooling_per_month
#        })
#    with chart_container(data):
#        st.altair_chart(alt.Chart(data).mark_bar(color = '#1d3c34', line = {'color':'#1d3c34'}, opacity = 1).encode(
#            x=alt.X("x", axis=alt.Axis(title="Måneder")),
#            y=alt.Y("y", axis=alt.Axis(title="Kjølebehov [kWh]"))), theme="streamlit", use_container_width=True)

#st.markdown("---")
#--
#st.subheader("Dekningsgrad")
#energy_coverage = EnergyCoverage(demand_array)
#energy_coverage.COVERAGE = st.number_input("Velg energidekningsgrad [%]", min_value=50, value=90, max_value=100, step=2)    
#energy_coverage._coverage_calculation()
#st.caption(f"**Varmepumpe: {energy_coverage.heat_pump_size} kW | Effektdekningsgrad: {int(round((energy_coverage.heat_pump_size/np.max(demand_array))*100,0))} %**")

#data = pd.DataFrame({
#    'Timer i ett år' : np.arange(0,8760,1),
#    'Spisslast' : energy_coverage.non_covered_arr,
#    'a' : energy_coverage.covered_arr, 
#    })

#with chart_container(data):
#    c = alt.Chart(data).transform_fold(
#    ['a', 'Spisslast'],
#    as_=['key', 'Timesmidlet effekt (kWh/h)']).mark_bar(color = '#b7dc8f', line = {'color':'#b7dc8f'}, opacity=1).encode(
#        x=alt.X('Timer i ett år:Q', scale=alt.Scale(domain=[0, 8760])),
#        y=alt.Y('Timesmidlet effekt (kWh/h):Q', stack = True),
#        color=alt.Color('key:N', scale=alt.Scale(domain=['a', 'Spisslast'], 
#        range=['#1d3c34', '#ffdb9a']), legend=alt.Legend(orient='top', direction='vertical', title=None))
#    )
#    st.altair_chart(c, use_container_width=True)

#Plotting().hourly_stack_plot(energy_coverage.covered_arr, energy_coverage.non_covered_arr, "Grunnvarmedekning", "Spisslast (dekkes ikke av brønnparken)", Plotting().FOREST_GREEN, Plotting().SUN_YELLOW)
#Plotting().hourly_stack_plot(np.sort(energy_coverage.covered_arr)[::-1], np.sort(energy_coverage.non_covered_arr)[::-1], "Grunnvarmedekning", "Spisslast (dekkes ikke av brønnparken)", Plotting().FOREST_GREEN, Plotting().SUN_YELLOW)
#--
#st.subheader("Årsvarmefaktor")
#energy_coverage.COP = st.number_input("Velg årsvarmefaktor (SCOP)", min_value=1.0, value=3.5, max_value=5.0, step=0.2)
#energy_coverage._geoenergy_cop_calculation()
#data = pd.DataFrame({
#    'Timer i ett år' : np.arange(0,8760,1),
#    'Spisslast' : energy_coverage.gshp_delivered_arr,
#    "Levert fra brønner" : energy_coverage.non_covered_arr,
#    'Strøm til varmepumpe' : energy_coverage.gshp_compressor_arr, 
#    })
#with chart_container(data):
#    c = alt.Chart(data).transform_fold(
#    ['Spisslast', 'Levert fra brønner', 'Strøm til varmepumpe'],
#    as_=['key', 'Timesmidlet effekt (kWh/h)']).mark_bar(color = '#b7dc8f', line = {'color':'#b7dc8f'}, opacity=1).encode(
#        x=alt.X('Timer i ett år:Q', scale=alt.Scale(domain=[0, 8760])),
#        y=alt.Y('Timesmidlet effekt (kWh/h):Q', stack = True),
#        color=alt.Color('key:N', scale=alt.Scale(domain=['Spisslast', 'Levert fra brønner', 'Strøm til varmepumpe'], 
#        range=['#1d3c34', '#ffdb9a', '#ffdb3b']), legend=alt.Legend(orient='top', direction='vertical', title=None))
#    )
#    st.altair_chart(c, use_container_width=True)
#--
#data = pd.DataFrame({
#    'Varighet (timer)' : np.arange(0,8760,1),
#    'Spisslast' : np.sort(energy_coverage.gshp_delivered_arr)[::-1],
#    "Levert fra brønner" : np.sort(energy_coverage.non_covered_arr)[::-1],
#    'Strøm til varmepumpe' : np.sort(energy_coverage.gshp_compressor_arr)[::-1], 
#    })
#with chart_container(data):
#    c = alt.Chart(data).transform_fold(
#    ['Spisslast', 'Levert fra brønner', 'Strøm til varmepumpe'],
#    as_=['key', 'Timesmidlet effekt (kWh/h)']).mark_bar(color = '#b7dc8f', line = {'color':'#b7dc8f'}, opacity=1).encode(
#        x=alt.X('Varighet (timer):Q', scale=alt.Scale(domain=[0, 8760])),
#        y=alt.Y('Timesmidlet effekt (kWh/h):Q', stack = True),
#        color=alt.Color('key:N', scale=alt.Scale(domain=['Spisslast', 'Levert fra brønner', 'Strøm til varmepumpe'], 
#        range=['#1d3c34', '#ffdb9a', '#ffdb3b']), legend=alt.Legend(orient='top', direction='vertical', title=None))
#    )
#    st.altair_chart(c, use_container_width=True)

#st.markdown("---")
#st.subheader("Oppsummert")
#st.write(f"Totalt energibehov: {int(round(np.sum(demand_array),0)):,} kWh | {int(round(np.max(demand_array),0)):,} kW".replace(',', ' '))
#st.write(f"- Dekkes av grunnvarmeanlegget: {int(round(np.sum(energy_coverage.covered_arr),0)):,} kWh | **{int(round(np.max(energy_coverage.covered_arr),0)):,}** kW".replace(',', ' '))
#st.write(f"- - Strøm til varmepumpe: {int(round(np.sum(energy_coverage.gshp_compressor_arr),0)):,} kWh | {int(round(np.max(energy_coverage.gshp_compressor_arr),0)):,} kW".replace(',', ' '))
#st.write(f"- - Levert fra brønn(er): {int(round(np.sum(energy_coverage.gshp_delivered_arr),0)):,} kWh | {int(round(np.max(energy_coverage.gshp_delivered_arr),0)):,} kW".replace(',', ' '))
#st.write(f"- Spisslast (dekkes ikke av brønnparken): {int(round(np.sum(energy_coverage.non_covered_arr),0)):,} kWh | {int(round(np.max(energy_coverage.non_covered_arr),0)):,} kW".replace(',', ' '))
#st.markdown("---")

st.button("Refresh")
#st.bar_chart(demand_array)
simulation_obj = Simulation()
simulation_obj.YEARS = 30
simulation_obj.U_PIPE = "Single"  # Choose between "Single" and "Double"
simulation_obj.R_B = 0.0575  # Radius (m)
simulation_obj.R_OUT = 0.025  # Pipe outer radius (m)
simulation_obj.R_IN = 0.0224  # Pipe inner radius (m)
simulation_obj.D_S = 0.064/2  # Shank spacing (m)
simulation_obj.EPSILON = 1.0e-6  # Pipe roughness (m)
simulation_obj.ALPHA = 1.39e-6  # Ground thermal diffusivity (m2/s)
simulation_obj.K_S = 3.0  # Ground thermal conductivity (W/m.K)            
simulation_obj.T_G = 8.1  # Undisturbed ground temperature (degrees)   
simulation_obj.K_G = 0.825  # Grout thermal conductivity (W/m.K)
simulation_obj.K_P = 0.42  # Pipe thermal conductivity (W/m.K)
simulation_obj.H = 295  # Borehole depth (m)
simulation_obj.B = st.number_input("Distanse mellom borehull", value = 12)  # Distance between boreholes (m)
simulation_obj.D = 10  # Borehole buried depth
simulation_obj.FLOW_RATE = 0.88  # Flow rate (kg/s)
simulation_obj.FLUID_NAME = "MPG"  # The fluid is propylene-glycol 
simulation_obj.FLUID_DEGREES = 5  # at 20 degC
simulation_obj.BOUNDARY_CONDITION = 'MIFT'
simulation_obj.select_borehole_field(10)
if st.checkbox("Kjør simulering"):
    simulation_obj.run_simulation(demand_array)


#---
#with st.expander("GHEtool"):
#    st.header("Ⅱ) Dimensjonering av brønnpark")
#    simulation_obj = GheTool()
#    simulation_obj.monthly_load_heating = hour_to_month(energy_coverage.gshp_delivered_arr)
#    simulation_obj.peak_heating = np.full((1, 12), energy_coverage.heat_pump_size).flatten().tolist()
#    simulation_obj.monthly_load_cooling = cooling_per_month
#    simulation_obj.peak_cooling = np.full((1, 12), cooling_effect).flatten().tolist()
#    well_guess = int(round(np.sum(energy_coverage.gshp_delivered_arr)/80/300,2))
#    if well_guess == 0:
#        well_guess = 1
#    with st.form("Inndata"):
#        c1, c2 = st.columns(2)
#        with c1:
#            simulation_obj.K_S = st.number_input("Effektiv varmledningsevne [W/m∙K]", min_value=1.0, value=3.5, max_value=10.0, step=1.0) 
#            simulation_obj.T_G = st.number_input("Uforstyrret temperatur [°C]", min_value=1.0, value=8.0, max_value=20.0, step=1.0)
#            simulation_obj.R_B = st.number_input("Borehullsmotstand [m∙K/W]", min_value=0.0, value=0.10, max_value=2.0, step=0.01) + 0.03
#            simulation_obj.N_1= st.number_input("Antall brønner (X)", value=well_guess, step=1) 
#            simulation_obj.N_2= st.number_input("Antall brønner (Y)", value=1, step=1)
#            #--
#            simulation_obj.COP = energy_coverage.COP
#        with c2:
#            H = st.number_input("Brønndybde [m]", min_value=100, value=300, max_value=500, step=10)
#            GWT = st.number_input("Grunnvannsstand [m]", min_value=0, value=5, max_value=100, step=1)
#            simulation_obj.H = H - GWT
#            simulation_obj.B = st.number_input("Avstand mellom brønner", min_value=1, value=15, max_value=30, step=1)
#            simulation_obj.RADIUS = st.number_input("Brønndiameter [mm]", min_value = 80, value=115, max_value=300, step=1) / 2000
#            heat_carrier_fluid_types = ["HX24", "HX35", "Kilfrost GEO 24%", "Kilfrost GEO 32%", "Kilfrost GEO 35%"]    
#            heat_carrier_fluid = st.selectbox("Type kollektorvæske", options=list(range(len(heat_carrier_fluid_types))), format_func=lambda x: heat_carrier_fluid_types[x])
#            simulation_obj.FLOW = 0.5
#            #simulation_obj.peak_heating = st.number_input("Varmepumpe [kW]", value = int(round(energy_coverage.heat_pump_size,0)), step=10)
#        st.form_submit_button("Kjør simulering")
#    heat_carrier_fluid_densities = [970.5, 955, 1105.5, 1136.2, 1150.6]
#    heat_carrier_fluid_capacities = [4.298, 4.061, 3.455, 3.251, 3.156]
#    simulation_obj.DENSITY = heat_carrier_fluid_densities[heat_carrier_fluid]
#    simulation_obj.HEAT_CAPACITY = heat_carrier_fluid_capacities[heat_carrier_fluid]
#    simulation_obj._run_simulation()


#st.markdown("---")   


#st.markdown("---")
#st.header("Oppsummering")
#buffer = BytesIO()

#df1 = pd.DataFrame({
#    "Termisk energibehov" : demand_array, 
#    "Strøm til varmepumpe" : energy_coverage.gshp_compressor_arr,
#    "Levert energi fra brønner" : energy_coverage.gshp_delivered_arr,
#    "Spisslast" : energy_coverage.non_covered_arr
#    })

#with pd.ExcelWriter(buffer, engine="xlsxwriter") as writer:
#    df1.to_excel(writer, sheet_name="Sheet1", index=False)
#    writer.save()

#    st.write("Her kan du laste ned resultater fra beregningene til excel-format.")
#    st.download_button(
#        label="Last ned resultater",
#        data=buffer,
#        file_name="Energibehov.xlsx",
#        mime="application/vnd.ms-excel",
#    )


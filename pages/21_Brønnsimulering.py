import streamlit as st
from st_aggrid import AgGrid, GridOptionsBuilder
from streamlit_extras.chart_container import chart_container
from matplotlib import pyplot as plt

from GHEtool import Borefield, GroundData
import pygfunction as gt
import altair as alt
import numpy as np 
import pandas as pd
from helpscripts._utils import st_modified_number_input

st.set_page_config(
    page_title="Grunnvarme",
    page_icon="🏔️",
)

with open("styles/main.css") as f:
    st.markdown("<style>{}</style>".format(f.read()), unsafe_allow_html=True) 
    
def xy_simulation_plot(x, xmin, xmax, x_label, y1, y2, y_label, y_legend1, y_legend2, COLOR1, COLOR2, ymin = -8, ymax = 16):
    fig, ax = plt.subplots()
    x = x/12
    ax.plot(x, y2, linewidth=1.0, color=COLOR2, label=y_legend2)
    ax.plot(x, y1, linewidth=1.0, color=COLOR1, label=y_legend1)
    #ax.axhline(y = 1, color = 'black', linestyle = '--', linewidth=0.3)
    ax.axhline(y = 0, color = 'black', linestyle = '-.', linewidth=0.3)        
    ax.legend()
    ax.grid(color='black', linestyle='--', linewidth=0.1)
    ax.set(xlim=(xmin, xmax), xlabel=(x_label), ylabel=(y_label), yticks=(np.arange(ymin, ymax, 1)))
    plt.close()
    return fig
    
st.title("Månedssimulering")
st.warning("Under utvikling ...")
st.info("""Appen utfører månedssimulering med *GHEtool* basert på oppgitte energi- og effekttall. 
Her legges alle tall inn direkte (dvs. ingen COP).""")
tab1, tab2 = st.tabs(["Energibehov", "Effektbehov"])
with tab1:
    st.header("Energibehov")
    c1, c2 = st.columns(2)
    with c1:
        annual_heat_load = st.number_input("Årlig varmebehov [kWh]", value = 2308000)
    with c2:
        annual_cool_load = st.number_input("Årlig kjølebehov [kWh]", value = 350000)
    if annual_heat_load != None and annual_cool_load != None:
        df = pd.DataFrame({
            "Varme [%]" : np.array([0.155, 0.148, 0.125, .099, .064, 0., 0., 0., 0.061, 0.087, 0.117, 0.144]) * 100,
            "Kjøling [%]" : np.array([0.025, 0.05, 0.05, .05, .075, .1, .2, .2, .1, .075, .05, .025]) * 100,
            })

        gb = GridOptionsBuilder.from_dataframe(df)
        gb.configure_default_column(editable=True)
        grid_table = AgGrid(
            df,
            height=400,
            gridOptions=gb.build(),
            fit_columns_on_grid_load=True,
            allow_unsafe_jscode=True,
            key="energibehov",
        )
        grid_table_df = pd.DataFrame(grid_table['data'])
        monthly_load_heating = annual_heat_load * (grid_table_df["Varme [%]"]/100)   # kWh
        monthly_load_cooling = annual_cool_load * (grid_table_df["Kjøling [%]"]/100)   # kWh
        
        monthly_load_heating = np.array([326.444, 284.144, 259.819, 199.729, 19.265, 0, 0, 0, 0, 68.966, 203.658, 304.271])*1000
        monthly_load_cooling = np.array([0, 0, 0, 0, 0, 136.543, 209.043, 142.184, 85.310, 0, 0, 0])*1000  
    
        months = ["a_jan", "b_feb", "c_mar", "d_apr", "e_mai", "f_jun", "g_jul", "h_aug", "i_sep", "j_okt", "k_nov", "l_des"]
        energy_df = pd.DataFrame({
            "Måneder" : months,
            "Varmebehov [kWh]" : monthly_load_heating,
            "Kjølebehov [kWh]" : -monthly_load_cooling  
        })
        with chart_container(energy_df):
            st.bar_chart(data = energy_df, x = "Måneder", y = ["Varmebehov [kWh]", "Kjølebehov [kWh]"])
    else:
        monthly_load_heating = np.zeros(12)
        monthly_load_cooling = np.zeros(12)
#--
with tab2:
    st.header("Effektbehov")
    c1, c2 = st.columns(2)
    with c1:
        peak_heat_load = st.number_input("Maksimal varmeeffekt [kW]", value = 516)
    with c2:
        peak_cool_load = st.number_input("Maksimal kjøleeffekt [kW]", value = 413)
    if peak_heat_load != None and peak_cool_load != None:
        df = pd.DataFrame({
            "Varme [%]" : np.array([0.191, 0.169, 0.122, 0.066, 0.000, 0.000, 0.000, 0.000, 0.048, 0.101, 0.142, 0.162]) * 100,
            "Kjøling [%]" : np.array([0.000, 0.000, 0.032, 0.064, 0.124, 0.174, 0.199, 0.224, 0.149, 0.034, 0.000, 0.000]) * 100,
            })

        gb = GridOptionsBuilder.from_dataframe(df)
        gb.configure_default_column(editable=True)
        grid_table = AgGrid(
            df,
            height=400,
            gridOptions=gb.build(),
            fit_columns_on_grid_load=True,
            allow_unsafe_jscode=True,
            key="effektbehov",
        )
        grid_table_df = pd.DataFrame(grid_table['data'])
        monthly_peak_heating = peak_heat_load * (grid_table_df["Varme [%]"]/100)   # kWh
        monthly_peak_cooling = peak_cool_load * (grid_table_df["Kjøling [%]"]/100)   # kWh

        months = ["a_jan", "b_feb", "c_mar", "d_apr", "e_mai", "f_jun", "g_jul", "h_aug", "i_sep", "j_okt", "k_nov", "l_des"]
        peak_df = pd.DataFrame({
            "Måneder" : months,
            "Varmebehov [kW]" : monthly_peak_heating,
            "Kjølebehov [kW]" : -monthly_peak_cooling  
        })
        with chart_container(peak_df):
            st.bar_chart(data = peak_df, x = "Måneder", y = ["Varmebehov [kW]", "Kjølebehov [kW]"])
    else:
        monthly_peak_heating = np.zeros(12)
        monthly_peak_cooling = np.zeros(12)
#--

#if np.max(monthly_peak_cooling) > 0 and np.max(monthly_peak_cooling) > 0 and np.max(monthly_load_heating) > 0 and np.max(monthly_load_cooling) > 0:
st.markdown("---")
st.header("Dimensjonering av brønnpark")
st.subheader("Inndata")
with st.form("Inndata"):
    c1, c2 = st.columns(2)
    with c1:
        YEARS = st.number_input("Simuleringstid [år]", min_value=1, value=25, max_value=50, step=5) 
        K_S = st.number_input("Effektiv varmledningsevne [W/m∙K]", min_value=1.0, value=3.9, max_value=10.0, step=1.0) 
        T_G = st.number_input("Uforstyrret temperatur [°C]", min_value=1.0, value=6.2, max_value=20.0, step=1.0)
        R_B = st.number_input("Borehullsmotstand [m∙K/W]", min_value=0.0, value=0.105, max_value=2.0, step=0.01)
        H = st.number_input("Brønndybde [m]", min_value=100, value=283, max_value=500, step=10)
    with c2:
        GWT = st.number_input("Grunnvannsstand [m]", min_value=0, value=0, max_value=100, step=1)
        H = H - GWT
        B = st.number_input("Avstand mellom brønner", min_value=1, value=14, max_value=30, step=1)
        RADIUS = st.number_input("Brønndiameter [mm]", min_value = 80, value=115, max_value=300, step=1) / 2000
        heat_carrier_fluid_types = ["HX24", "HX35", "Kilfrost GEO 24%", "Kilfrost GEO 32%", "Kilfrost GEO 35%"]    
        heat_carrier_fluid = st.selectbox("Type kollektorvæske", options=list(range(len(heat_carrier_fluid_types))), format_func=lambda x: heat_carrier_fluid_types[x])
        FLOW = 0.5
    st.form_submit_button("Kjør simulering")
st.subheader("Konfigurasjon")
N_b_estimated = int(np.sum(monthly_load_heating)/80/H)
selected_field = st.selectbox("Konfigurasjon", options = ["Rektangulær", "Boks", "U", "L", "Sirkulær", "Fra tekstfil"])
if selected_field == "Rektangulær":
    N_1 = st.number_input("Antall brønner (X)", value = int(N_b_estimated/2) + 1, step = 1)
    N_2 = st.number_input("Antall brønner (Y)", value = 2, step = 1)
    N_b = N_1 * N_2
    borefield_gt = gt.boreholes.rectangle_field(N_1, N_2, B, B, H, 10, RADIUS)
if selected_field == "Boks": 
    N_1 = st.number_input("Antall brønner (X)", value = N_b_estimated, step = 1)
    N_2 = st.number_input("Antall brønner (Y)", value = 1, step = 1)
    N_b = N_1 * N_2
    borefield_gt = gt.boreholes.box_shaped_field(N_1, N_2, B, B, H, 10, RADIUS)
if selected_field == "U":
    N_1 = st.number_input("Antall brønner (X)", value = N_b_estimated, step = 1)
    N_2 = st.number_input("Antall brønner (Y)", value = 1, step = 1)
    N_b = N_1 * N_2
    borefield_gt = gt.boreholes.U_shaped_field(N_1, N_2, B, B, H, 10, RADIUS)
if selected_field == "L":
    N_1 = st.number_input("Antall brønner (X)", value = N_b_estimated - int(N_b_estimated/2), step = 1)
    N_2 = st.number_input("Antall brønner (Y)", value = int(N_b_estimated/2), step = 1)
    N_b = N_1 + N_2
    borefield_gt = gt.boreholes.L_shaped_field(N_1, N_2, B, B, H, 10, RADIUS)
if selected_field == "Sirkulær":
    N_b = st.number_input("Antall borehull", value = N_b_estimated, step = 1)
    borefield_gt = gt.boreholes.circle_field(N_b, B, H, 10, RADIUS)
if selected_field == "Fra tekstfil":
    file = st.file_uploader("Last opp DataFrame")
    if file:
        df = pd.read_csv(file, sep = "   ", header=None)
        pos = []
        for i in range(0, len(df)):
            x = df[0][i]
            y = df[1][i]
            pos.append((x,y))
        borefield_gt = [gt.boreholes.Borehole(H, 10, RADIUS, x, y, 0, 0) for (x, y) in pos]
    else:
        st.stop()
    #file_location = st.text_input("Fillokasjon", value=r"S:\Oppdrag\Trondheim\10438\06\Grunnvarme\GIS - Delt\Andslimoen\Andslimoen.gdb\Brønner")
    #bronner = r"S:\Oppdrag\Trondheim\10438\06\Grunnvarme\GIS - Delt\Andslimoen\Andslimoen.gdb\Brønner"
    #df = pd.DataFrame.spatial.from_featureclass(file_location)
    #df = df.drop(df[df.Scenario == "S2"].index)
    #df = df.reset_index()
    #df.head()
st.pyplot(gt.boreholes.visualize_field(borefield_gt))
    
#ground parameters
data = GroundData(K_S,   # ground thermal conductivity (W/mK)
                    T_G,  # initial/undisturbed ground temperature (deg C)
                    R_B, # borehole equivalent resistance (mK/W)
                    2.16*10**6) # volumetric heat capacity of the ground (J/m3K) 

# create the borefield object
borefield = Borefield(simulation_period=YEARS,
                    peak_heating=monthly_peak_heating,
                    peak_cooling=monthly_peak_cooling,
                    baseload_heating=monthly_load_heating,
                    baseload_cooling=monthly_load_cooling)
borefield.set_borefield(borefield_gt)
borefield.set_ground_parameters(data)
borefield.calculate_temperatures()
st.subheader("Resultater")
results_df = pd.DataFrame({
    "Ved dellast [°C]" : borefield.results_month_heating,
    "Ved maksimal varmeffekt [°C]" : borefield.results_peak_heating
})
plot = xy_simulation_plot(np.arange(0,len(borefield.results_month_heating)), 0, YEARS, "År", borefield.results_month_heating, borefield.results_peak_heating, "Gj.snittlig kollektorvæsketemperatur [°C]", "Ved dellast", f"Ved maksimal varmeeffekt", "black", "red")
st.pyplot(plot)
#    with chart_container(results_df):
#        st.line_chart(data = results_df)
st.write(f"Laveste gj.snittlige kollektorvæsketemperatur v/dellast: **{round(min(borefield.results_month_heating),1)} °C**")
st.write(f"Laveste gj.snittlige kollektorvæsketemperatur v/maksimal varmeeffekt: **{round(min(borefield.results_peak_heating),1)} °C**")
Q = (max(monthly_peak_heating)/borefield.number_of_boreholes)
DENSITY = 955
HEAT_CAPACITY = 4.061
st.caption(f"Levert effekt fra brønnpark: {round(max(monthly_peak_heating))} kW | Levert effekt per brønn (Q): {round(Q,1)} kW")
delta_T = round((Q*1000)/(DENSITY*FLOW*HEAT_CAPACITY),1)
st.write(f"- ΔT: {delta_T:,} °C".replace(',', ' '))
st.write(f"- Kollektorvæsketemperatur inn til varmepumpe: {round(min(borefield.results_peak_heating) + delta_T/2,1):,} °C".replace(',', ' '))
st.write(f"- Kollektorvæsketemperatur ut fra varmepumpe: {round(min(borefield.results_peak_heating) - delta_T/2,1):,} °C".replace(',', ' '))
#    #--
#    if np.sum(self.monthly_load_cooling) > 0:   
#        st.markdown("---")
#        Plotting().xy_simulation_plot(x, 0, self.YEARS, "År", borefield.results_month_cooling, 
#        borefield.results_peak_cooling, "Gj.snittlig kollektorvæsketemperatur [°C]", "Ved dellast", f"Ved maksimal kjøleeffekt", Plotting().GRASS_GREEN, Plotting().GRASS_BLUE)   
#        st.write(f"Høyeste gj.snittlige kollektorvæsketemperatur v/maksimal kjøleeffekt: **{round(max(borefield.results_peak_cooling),1)} °C**")
#        st.write(f"Laveste gj.snittlige kollektorvæsketemperatur v/maksimal kjøleeffekt: **{round(min(borefield.results_peak_cooling),1)} °C**")  
#    st.markdown("---")
#    """


    






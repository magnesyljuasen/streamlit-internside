import streamlit as st
import numpy_financial as npf
import numpy as np
import pandas as pd
import plotly.express as px
from helpscripts._green_energy_fund import GreenEnergyFund

st.set_page_config(
    page_title="Fond",
    layout="wide"
)

with open("styles/main.css") as f:
    st.markdown("<style>{}</style>".format(f.read()), unsafe_allow_html=True)

st.title("Finansiering")
green_energy = GreenEnergyFund()

def plot_prismodell(df):
    custom_colors = {
        "EAAS": "#48a23f",
        "15": "#1d3c34",
    }
    fig = px.bar(df, x=df.index, y=["EAAS", "15"], labels={"value": "Values"}, color_discrete_map=custom_colors)

    fig["data"][0]["showlegend"] = True
    fig.update_layout(
        legend=dict(
            title=None),
        barmode='group',
        xaxis = dict(
                tickmode = 'array',
                tickvals = [i for i in range(0, YEARS, 1)],
                ticktext = [f"{i + 1}" for i in range(0, YEARS, 1)]
                )
    )

    fig.update_xaxes(
        title="År",
        #range=[0, YEARS],
        ticks="outside",
        linecolor="black",
        gridcolor="lightgrey",
        mirror=True
            )
    fig.update_yaxes(
        title="Kostnader [kr/år]",
        tickformat=",",
        ticks="outside",
        linecolor="black",
        gridcolor="lightgrey",
        mirror=True)
    fig.update_layout(
        separators="* .*",
        margin=dict(t=50, b=50),)
    st.plotly_chart(fig, use_container_width=True, config = {'displayModeBar': False, 'staticPlot': True})

def create_accumulated_dataframe(dataframe):
    # Initialize an empty DataFrame to store the accumulated values
    accumulated_df = pd.DataFrame(columns=dataframe.columns)

    # Initialize an accumulator
    cumulative_sum = pd.Series(0, index=dataframe.columns, dtype=float)
    
    for index, row in dataframe.iterrows():
        # Accumulate the values in each row
        cumulative_sum += row
        # Append the accumulated values to the new DataFrame
        accumulated_df = accumulated_df.append(cumulative_sum, ignore_index=True)

    return accumulated_df

def plot_prismodell_akkumulert(df):
    st.title("Prismodell - Akkumulert")
    custom_colors = {
        "EAAS": "#48a23f",
        "15": "#1d3c34",
    }
    #st.write(df)
    #df = create_accumulated_dataframe(df)
    st.write(df)
    fig = px.bar(df, x=df.index, y=["EAAS", "15"], labels={"value": "Values"}, color_discrete_map=custom_colors)
    df = create_accumulated_dataframe(df)
    st.write(df)
    fig["data"][0]["showlegend"] = True
    fig.update_layout(
        legend=dict(
            title=None),
        barmode='group',
        xaxis = dict(
                tickmode = 'array',
                tickvals = [i for i in range(0, YEARS, 1)],
                ticktext = [f"{i + 1}" for i in range(0, YEARS, 1)]
                )
    )
    fig.update_xaxes(
        title="År",
        #range=[0, YEARS],
        ticks="outside",
        linecolor="black",
        gridcolor="lightgrey",
        mirror=True
            )
    fig.update_yaxes(
        title="Kostnader [kr/år]",
        tickformat=",",
        ticks="outside",
        linecolor="black",
        gridcolor="lightgrey",
        mirror=True)
    fig.update_layout(
        separators="* .*",
        margin=dict(t=50, b=50),)
    st.plotly_chart(fig, use_container_width=True, config = {'displayModeBar': False, 'staticPlot': True})

st.title("Inndata")

st.caption("**1) Varmeleveranse**")
c1, c2, c3 = st.columns(3)
with c1:
    green_energy.effekt_vp = st.number_input("Levert varmeeffekt fra varmepumpe [kW]", value=None, min_value=0, max_value=500)
with c2:
    from_wells = st.number_input("Levert varme fra brønner [kWh]", value=None, min_value=0, max_value=1000000, step=1000)
with c3:
    from_compressor = st.number_input("Strømforbruk kompressor [kWh]", value=None, min_value=0, max_value=500000, step=1000)
st.markdown("---")
if green_energy.effekt_vp != None and from_wells != None and from_compressor != None:
    green_energy.el_vp = from_compressor
    green_energy.levert_varme = from_wells + from_compressor
    st.caption("**2) Investeringskostnader**")
    st.caption(f"*Antatte verdier basert på utfylt data i 1) Varmeleveranse*: | Ca. antall brønnmeter {int(from_wells/80):,} m | Tilsvarer {int(from_wells/80/300):,} brønner á 300 m | COP {round(float((from_wells + from_compressor)/from_compressor), 1)}".replace(",", " "))
    c1, c2, c3 = st.columns(3)
    with c1:
        wells_cost_guess_value = 20000 + (from_wells/80) * 437.5
        green_energy.boring = st.number_input("Energibrønner [kr]", value=int(wells_cost_guess_value), min_value=0, max_value=10000000)
    with c2:
        heatpump_cost_guess_value = 214000 + (green_energy.effekt_vp) * 2200
        green_energy.vp = st.number_input("Varmepumpe [kr]", value=heatpump_cost_guess_value, min_value=0, max_value=10000000)
    with c3:
        green_energy.sol = st.number_input("Solenergi [kr]", value=None, min_value=0, max_value=10000000)
    st.markdown("---")
    if green_energy.boring != None and green_energy.vp != None and green_energy.sol != None:
        st.caption("**3) Andre forutsetninger**")
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            green_energy.ØKONOMISK_LEVETID = st.number_input("Økonomisk levetid [år]", value=15)
            green_energy.RENTEMARGINAL = st.number_input("Rentemarginal [%]", value=1.5, step = 0.1)
            green_energy.BOLAGSSKATT = st.number_input("Bolagsskatt [%]", value=22)
        with c2:
            green_energy.INFLASJON = st.number_input("Inflasjon [%]", value=2.0, step = 0.1)
            green_energy.BELAANING = st.number_input("Belåning [%]", value=30, step = 1) / 100
            green_energy.ENOVA = st.number_input("Enova [kr]", value=1600)
        with c3:
            green_energy.RENTE_SWAP_5 = st.number_input("Swaprente år 5 [%]", value=2.25, step = 0.1)
            green_energy.MANAGEMENT_FEE = st.number_input("Management fee [%]", value=1)
        with c4:
            green_energy.AV_VARME = st.number_input("Asplan Viak Varme [%]", value=20)
            green_energy.AV_SOL = st.number_input("Asplan Viak Sol [%]", value=10)
        st.markdown("---")
        c1, c2, c3 = st.columns(3)
        # Define investment parameters
        with c1:
            st.caption("**4) Driftskostnader**")
            green_energy.elpris = st.number_input("Strømpris [kr/kWh]", value=1.0, step = 0.1)
            green_energy.driftskostnad = st.number_input("Driftskostnad [kr/år]", value=50000, step = 1000)
        with c2:
            st.caption("**5) Energy as a service**")
            green_energy.LEASING_EAAS = st.number_input("Leasing [kr]", value=450000, step = 1000, key = "eaas1")            
            green_energy.REINVEST_VP_2 = st.number_input("Reinvestering VP [kr]", value = int(2 * 7e5), step = 1000)
            green_energy.AVKASTNINGSKRAV_BYGG = st.number_input("Avkastningskrav bygg [%]", value=4, key = "eaas2")
        with c3:
            st.caption("**6) 15 års beregning**")
            green_energy.LEASING_15 = st.number_input("Leasing [kr]", value= int(round(0.102 * green_energy.investering,-3)), step = 1000, key = "151")
            green_energy.REINVEST_VP_1 = st.number_input("Reinvestering VP [kr]", value = int(0.2 * green_energy.vp), step = 1000, key = "152")        
        st.markdown("---")
        c1, c2 = st.columns(2)
        with c1:
            # Create an instance of the GreenEnergyFund class
            st.header("15 års-beregning")
            investering, IRR, pris_15, pris_kWh, pris_15_etter, verdi = green_energy.seb_15_year()
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Investering", value = f"{int(round(investering,-3)):,} kr".replace(",", " "))
                st.metric("IRR", value = f"{(round(IRR * 100,2)):,} %".replace(",", " "))
            with col2:
                st.metric("Pris", value = f"{int(round(pris_15,-3)):,} kr".replace(",", " "))
                st.metric("Pris per kWh", value = f"{(round(pris_kWh,2)):,} kr/kWh".replace(",", " "))
            st.metric("Verdi av anlegget", value = f"{int(round(verdi,-3)):,} kr".replace(",", " "))
        with c2:
            st.header("Energy as a service")
            investering, IRR, pris_eaas, pris_kWh, arvode_av_varme, arvode_av_sol, verdi = green_energy.seb_energy_as_a_service()
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Investering", value = f"{int(round(investering,-3)):,} kr".replace(",", " "))
                st.metric("IRR", value = f"{(round(IRR * 100,2)):,} %".replace(",", " "))
            with col2:
                st.metric("Pris", value = f"{int(round(pris_eaas,-3)):,} kr".replace(",", " "))
                st.metric("Pris per kWh", value = f"{(round(pris_kWh,2)):,} kr/kWh".replace(",", " "))
            st.metric("Verdi av anlegget", value = f"{int(round(verdi,-3)):,} kr".replace(",", " "))

        YEARS = 30
        pris_eaas_list = []
        pris_15_list = []
        for i in range(0, YEARS):
            pris_eaas_list.append(pris_eaas)
            if i < 15:
                pris_15_list.append(pris_15)
            else:
                pris_15_list.append(pris_15_etter)

        df = pd.DataFrame({"EAAS" : pris_eaas_list, "15" : pris_15_list})
        plot_prismodell(df)
        #plot_prismodell_akkumulert(df)






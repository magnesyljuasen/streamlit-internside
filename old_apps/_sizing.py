import streamlit as st
import numpy as np

from scripts._pygfunction import Simulation
from scripts._profet import EnergyDemand
from scripts._utils import Plotting
from scripts._energy_coverage import EnergyCoverage
from scripts._costs import Costs


def sizing():
    st.title("Energibehov")
    selected_input_option = st.radio("Velg inputform", options=["PROFet", "Last opp fil"], horizontal=True)
    if selected_input_option == "PROFet":
        st.header("PROFet")
        st.caption("Foreløpig begrenset til Trondheimsklima")
        energy_demand = EnergyDemand()
        demand_array, selected_array = energy_demand.get_thermal_arrays_from_input()
    if selected_input_option == "Last opp fil":
        st.header("Filopplasting")
        st.caption("Under arbeid...")
        demand_array = st.file_uploader("Last opp fil")
    Plotting().hourly_plot(demand_array, selected_array, Plotting().FOREST_GREEN)
    Plotting().hourly_plot(np.sort(demand_array)[::-1], selected_array, Plotting().FOREST_GREEN)
    st.markdown("---")
    #--
    st.header("Dekningsgrad")
    energy_coverage = EnergyCoverage(demand_array)
    energy_coverage.COVERAGE = st.number_input("Velg energidekningsgrad [%]", min_value=50, value=90, max_value=100, step=2)    
    energy_coverage._coverage_calculation()
    Plotting().hourly_stack_plot(energy_coverage.covered_arr, energy_coverage.non_covered_arr, "Grunnvarmedekning", "Spisslast", Plotting().FOREST_GREEN, Plotting().SUN_YELLOW)
    #--
    st.header("Årsvarmefaktor")
    energy_coverage.COP = st.number_input("Velg COP", min_value=1.0, value=3.5, max_value=5.0, step=0.2)
    energy_coverage._geoenergy_cop_calculation()
    Plotting().hourly_triple_stack_plot(energy_coverage.gshp_compressor_arr, energy_coverage.gshp_delivered_arr, 
    energy_coverage.non_covered_arr, "Kompressor", "Levert fra brønn(er)", "Spisslast", Plotting().FOREST_GREEN, Plotting().GRASS_GREEN, Plotting().SUN_YELLOW)
    Plotting().hourly_triple_stack_plot(np.sort(energy_coverage.gshp_compressor_arr)[::-1], np.sort(energy_coverage.gshp_delivered_arr)[::-1], 
    np.sort(energy_coverage.non_covered_arr)[::-1], "Kompressor", "Levert fra brønn(er)", "Spisslast", Plotting().FOREST_GREEN, Plotting().GRASS_GREEN, Plotting().SUN_YELLOW)

    st.markdown("---")
    #--
    st.title("Dimensjonering")
    kWh_per_meter = st.number_input("Velg kWh/m", min_value=60, value=80, max_value=120, step=5)
    meters = (np.sum(energy_coverage.gshp_delivered_arr)/kWh_per_meter)
    number_of_wells_300 = int(round(meters/300,0))
    number_of_wells_250 = int(round(meters/250,0))
    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric("Ca. antall brønnmeter", value=f"{int(round(meters,0)):,} m".replace(',', ' '))
    with c2:
        st.metric("Ca. antall brønner a 300 meter", value=f"{number_of_wells_300:,}".replace(',', ' '))
    with c3:
        st.metric("Ca. antall brønner a 250 meter", value=f"{number_of_wells_250:,}".replace(',', ' '))
    simulation_obj = Simulation()
    st.subheader("Pygfunction")
    c1, c2 = st.columns(2)
    with c1:
        simulation_obj.H = st.number_input("Brønndybde", min_value=100, value=300, max_value=500, step=10)
        simulation_obj.B = st.number_input("Avstand mellom brønner", min_value=1, value=15, max_value=30, step=1)
    with c2:
        simulation_obj.K_S = st.number_input("Varmledningsevne", min_value=1.0, value=3.5, max_value=10.0, step=1.0)
        simulation_obj.T_G = st.number_input("Uforstyrret temperatur", min_value=1.0, value=8.0, max_value=20.0, step=1.0)
    simulation_obj.select_borehole_field(number_of_wells_300)
    if st.checkbox("Kjør simulering"):
        with st.spinner("Beregner..."):
            simulation_obj.run_simulation(energy_coverage.gshp_delivered_arr)
            meters = int(round(simulation_obj.N_B * simulation_obj.H,0))
            c1, c2, c3 = st.columns(3)
            with c1:
                st.metric("Antall brønnmeter", value=f"{meters:,} m".replace(',', ' '))
            with c2:
                st.metric("Antall brønner", value=f"{int(round(simulation_obj.N_B,0)):,}".replace(',', ' '))
            with c3:
                st.metric("Brønndybde", value=f"{int(round(simulation_obj.H,0)):,} m".replace(',', ' '))
            #--
            st.title("Kostnader")
            st.caption("Under arbeid")
            costs = Costs()
            costs.calculate_investment(energy_coverage.heat_pump_size, meters, 5)
            costs.adjust()
            tab1, tab2 = st.tabs(["Direkte kjøp", "Lånefinansiert"])
            with tab1:
                costs.calculate_monthly_costs(demand_array, energy_coverage.gshp_compressor_arr, energy_coverage.non_covered_arr, costs.elprice, 0, 0)
                costs.operation_show_after()
                costs.plot("Driftskostnad")
                costs.profitibality_operation()

            with tab2:
                costs.calculate_monthly_costs(demand_array, energy_coverage.gshp_compressor_arr, energy_coverage.non_covered_arr, costs.elprice, costs.investment, costs.payment_time)

                costs.operation_and_investment_show()

                costs.plot("Totalkostnad")
                costs.profitibality_operation_and_investment()
    
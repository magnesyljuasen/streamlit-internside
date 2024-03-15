import streamlit as st
import numpy as np
import pandas as pd
from PIL import Image
from streamlit_extras.chart_container import chart_container


from scripts._profet import EnergyDemand
from scripts._utils import Plotting
from scripts._energy_coverage import EnergyCoverage
from scripts._costs import Costs
from scripts._ghetool import GheTool
from scripts._utils import hour_to_month
from scripts._peakshaving import peakshaving
from scripts._utils import negative_sum



def energy_analysis():
    st.button("Refresh")
    st.title("Energianalyse")
    #st.header("Last opp fil")
    #with st.expander("Hvordan skal filen se ut?"):
    #    st.write("Det kan kun importeres **excel ark** med maks 5 timeserier på formatet som under. Det er at rekkefølgen er lik som under (og med overskrift).")
    #    image = Image.open("src/data/img/example_input_energy_analysis.PNG")
    #    st.image(image)  
    #uploaded_array = st.file_uploader("Last opp timeserier [kW]")
    st.header("Kostnadsforutsetninger")
    selected_prices = st.selectbox("Pris", options=["Flat", "Historisk"])
    if selected_prices == "Flat":
        c1, c2 = st.columns(2)
        with c1:
            ELPRICE = st.number_input("Velg total strømpris [kr/kwh]", min_value=0.0, value=1.0, max_value=10.0, step=0.5)
        with c2:
            DISTRICTHEATING_PRICE = st.number_input("Velg total fjernvarmepris [kr/kwh]", min_value=0.0, value=1.0, max_value=10.0, step=0.5)
    if selected_prices == "Historisk":
        year = st.selectbox("Velg år", options= [2018, 2019, 2020, 2021])
        elspot_df = pd.read_csv(f'src/data/csv/el_spot_hourly_{year}.csv', sep=';', on_bad_lines='skip')
        NETTLEIE = st.number_input("Fast nettleie og andre avgifter [kr/kWh]", value=0.44, min_value=0.0, step=0.1)
        ELPRICE = np.resize(elspot_df.iloc[:, 5].to_numpy()/1000, 8760) 
        ELPRICE[np.isnan(ELPRICE)] = 0
        ELPRICE = ELPRICE + NETTLEIE
        Plotting().hourly_price_plot(ELPRICE, "Strømpris", Plotting().FOREST_GREEN)
        PRICE_RATIO = st.slider("Forhold mellom fjernvarmepris og strømpris. Til venstre: fjernvarme billigere enn strøm. Til høyre: fjernvarme dyrere enn strøm", value=1.0, step=0.1, max_value=2.0)
        DISTRICTHEATING_PRICE = ELPRICE * PRICE_RATIO
        Plotting().hourly_price_plot(DISTRICTHEATING_PRICE, "Fjernvarmepris", Plotting().FOREST_DARK_BROWN)


    with st.expander("Plotting"):
        MAX_VALUE = st.number_input("Maksverdi for plotting", min_value=0, value=1000000, max_value=10000000, step = 1000)
    st.markdown("---")
    #if uploaded_array:
    selected_df = st.selectbox("Input?", options=["TEK10/TEK17", "Passivhus"])
    if selected_df == "TEK10/TEK17":
        df = pd.read_excel("src/data/input/yrkesskolevegen.xlsx")
    if selected_df == "Passivhus":
        df = pd.read_excel("src/data/input/yrkesskolevegen2.xlsx")
    electric_array = df.iloc[:,0].to_numpy()
    space_heating_array = df.iloc[:,1].to_numpy()
    dhw_array = df.iloc[:,2].to_numpy()
    solar_array = df.iloc[:,3].to_numpy()
    thermal_array = df.iloc[:,4].to_numpy()
    Plotting().hourly_plot(electric_array, "El-spesifikt behov", Plotting().GRASS_BLUE)
    df = pd.DataFrame({"El-spesifikt behov" : electric_array})
    #np.savetxt('src/data/output/Elspesifikt.csv', electric_array, delimiter=',')
    with st.expander("Varighetskurve"):
        Plotting().hourly_duration_plot(electric_array, "El-spesifikt behov", Plotting().GRASS_BLUE)

    Plotting().hourly_plot(space_heating_array, "Romoppvarmingsbehov", Plotting().FOREST_BROWN)
    df["Romoppvarmingsbehov"] = space_heating_array
    with st.expander("Varighetskurve"):
        Plotting().hourly_duration_plot(space_heating_array, "Romoppvarmingsbehov", Plotting().FOREST_BROWN)

    df["Tappevannsbehov"] = dhw_array
    Plotting().hourly_plot(dhw_array, "Tappevannsbehov", Plotting().FOREST_PURPLE)
    with st.expander("Varighetskurve"):
        Plotting().hourly_duration_plot(dhw_array, "Tappevannsbehov", Plotting().FOREST_PURPLE)
    
    df["Termisk behov"] = thermal_array
    Plotting().hourly_plot(thermal_array, "Termisk (romoppvarming + tappevann)", Plotting().FOREST_DARK_BROWN)
    with st.expander("Varighetskurve"):
        Plotting().hourly_duration_plot(thermal_array, "Termisk (romoppvarming + tappevann)", Plotting().FOREST_DARK_BROWN)
    
    Plotting().hourly_stack_plot(electric_array, thermal_array, "El-spesifikt behov", "Termisk behov", Plotting().GRASS_BLUE, Plotting().FOREST_BROWN)
    Plotting().hourly_stack_plot(np.sort(electric_array)[::-1], np.sort(thermal_array)[::-1], "El-spesifikt behov", "Termisk behov", Plotting().GRASS_BLUE, Plotting().FOREST_BROWN)

    Plotting().hourly_stack_plot(np.sort(dhw_array)[::-1], np.sort(space_heating_array)[::-1], "Tappevannsbehov", "Romoppvarmingsbehov", Plotting().FOREST_PURPLE, Plotting().FOREST_BROWN)
    Plotting().hourly_stack_plot(dhw_array, space_heating_array, "Tappevannsbehov", "Romoppvarmingsbehov", Plotting().FOREST_PURPLE, Plotting().FOREST_BROWN)


    df["Solenergi"] = solar_array
    Plotting().hourly_plot(solar_array, "Produsert solenergi", Plotting().SUN_YELLOW)
    #np.savetxt('src/data/output/Produsert solenergi.csv', solar_array, delimiter=',')
    with st.expander("Varighetskurve"):
        Plotting().hourly_duration_plot(solar_array, "Produsert solenergi", Plotting().SUN_YELLOW)

    st.header("Scenarier")
    if st.checkbox("Scenario 1) Fjernvarme og solenergi"):
        #--
        #st.header("Kjølebehov")
        #annual_cooling_demand = st.number_input("Legg inn årlig kjølebehov [kWh]", min_value=0, value=0, step=1000)
        #cooling_effect = st.number_input("Legg inn kjøleeffekt [kW]", min_value=0, value=0, step=100)
        #cooling_per_month = annual_cooling_demand * np.array([0.025, 0.05, 0.05, .05, .075, .1, .2, .2, .1, .075, .05, .025])
        #months = ["jan", "feb", "mar", "apr", "mai", "jun", "jul", "aug", "sep", "okt", "nov", "des"]
        #Plotting().xy_plot_bar(months, "Måneder", cooling_per_month, 0, max(cooling_per_month) + max(cooling_per_month)/10, "Effekt [W]", Plotting().GRASS_GREEN)
        #st.markdown("---")
        #--
        st.markdown("---")
        st.header("Fjernvarme og solenergi")
        st.subheader("Dekningsgrad")
        energy_coverage = EnergyCoverage(thermal_array)
        energy_coverage.COVERAGE = st.number_input("Velg energidekningsgrad [%]", min_value=50, value=100, max_value=100, step=2, key="fjernvarmedekning")    
        energy_coverage._coverage_calculation()
        df["S1 - Fjernvarmedekning"] = energy_coverage.covered_arr
        df["S1 - Spisslast"] = energy_coverage.non_covered_arr
        Plotting().hourly_plot(energy_coverage.covered_arr, "Fjernvarmedekning", Plotting().FOREST_GREEN)
        Plotting().hourly_plot(np.sort(energy_coverage.covered_arr)[::-1], "Fjernvarmedekning", Plotting().FOREST_GREEN)
        #Plotting().hourly_stack_plot(energy_coverage.covered_arr, energy_coverage.non_covered_arr, "Fjernvarmedekning", "Spisslast", Plotting().FOREST_GREEN, Plotting().GRASS_BLUE)
        #np.savetxt('src/data/output/Fjernvarmedekning.csv', energy_coverage.covered_arr, delimiter=',')
        #np.savetxt('src/data/output/Spisslast.csv', energy_coverage.non_covered_arr, delimiter=',')
        with st.expander("Varighetskurve"):
            Plotting().hourly_stack_plot(np.sort(energy_coverage.covered_arr)[::-1], np.sort(energy_coverage.non_covered_arr)[::-1], "Fjernvarmedekning", "Spisslast", Plotting().FOREST_GREEN, Plotting().GRASS_BLUE)
        st.subheader("Gjenstående elektrisk behov")
        df["S1 - Totalt elektrisk behov"] = electric_array + energy_coverage.non_covered_arr
        Plotting().hourly_plot(electric_array + energy_coverage.non_covered_arr, "Totalt elektrisk behov; uten solproduksjon", Plotting().GRASS_BLUE)
        with st.expander("Varighetskurve"):
            Plotting().hourly_plot(np.sort(electric_array + energy_coverage.non_covered_arr)[::-1], "Totalt elektrisk behov; uten solproduksjon", Plotting().GRASS_BLUE)
        df["S1 - Totalt elektrisk behov med solproduksjon"] = electric_array + energy_coverage.non_covered_arr - solar_array
        Plotting().hourly_negative_plot(electric_array + energy_coverage.non_covered_arr - solar_array, "Totalt elektrisk behov; med solproduksjon", Plotting().GRASS_BLUE)
        with st.expander("Varighetskurve"):
            Plotting().hourly_negative_plot(np.sort(electric_array + energy_coverage.non_covered_arr - solar_array)[::-1], "Totalt elektrisk behov; med solproduksjon", Plotting().GRASS_BLUE)
        with st.expander("Kostnader", expanded=True):
            months = ["jan", "feb", "mar", "apr", "mai", "jun", "jul", "aug", "sep", "okt", "nov", "des"]
            cost_per_month_el = hour_to_month(ELPRICE*(electric_array + energy_coverage.non_covered_arr - solar_array))
            cost_per_month_districtheating = hour_to_month(DISTRICTHEATING_PRICE*(energy_coverage.covered_arr))
            Plotting().xy_plot_bar_stacked(months, "Måneder i ett år", cost_per_month_el, cost_per_month_districtheating, f"Strøm: {int(round(np.sum(cost_per_month_el),-3)):,} kr/år".replace(",", " "), f"Fjernvarme: {int(round(np.sum(cost_per_month_districtheating),-3)):,} kr/år".replace(",", " "), 0, MAX_VALUE, "Kostnad [kr]", Plotting().GRASS_BLUE, Plotting().FOREST_GREEN)
            st.write(f"**Sum: {int(round(np.sum(cost_per_month_districtheating) + np.sum(cost_per_month_el),-3)):,} kr**".replace(",", " "))
            df1 = pd.DataFrame({"Strøm" : cost_per_month_el, "Fjernvarme" : cost_per_month_districtheating})
        st.markdown("---")
        #--
    if st.checkbox("Scenario 2) Grunnvarme og solenergi"):
        st.markdown("---")
        st.header("Grunnvarme og solenergi")
        st.subheader("Dekningsgrad")
        energy_coverage = EnergyCoverage(thermal_array)
        energy_coverage.COVERAGE = st.number_input("Velg energidekningsgrad [%]", min_value=50, value=90, max_value=100, step=2, key="grunnvarmedekning1")    
        energy_coverage._coverage_calculation()
        df["S2 - Grunnvarmedekning"] = energy_coverage.covered_arr
        df["S2 - Spisslast"] = energy_coverage.non_covered_arr
        Plotting().hourly_stack_plot(energy_coverage.covered_arr, energy_coverage.non_covered_arr, "Grunnvarmedekning", "Spisslast", Plotting().SPRING_GREEN, Plotting().SPRING_BLUE)
        #np.savetxt('src/data/output/Grunnvarmedekning.csv', energy_coverage.covered_arr, delimiter=',')
        #np.savetxt('src/data/output/Spisslast.csv', energy_coverage.non_covered_arr, delimiter=',')
        with st.expander("Varighetskurve"):
            Plotting().hourly_stack_plot(np.sort(energy_coverage.covered_arr)[::-1], np.sort(energy_coverage.non_covered_arr)[::-1], "Grunnvarmedekning", "Spisslast", Plotting().SPRING_GREEN, Plotting().SPRING_BLUE)
        st.subheader("Årsvarmefaktor")
        energy_coverage.COP = st.number_input("Velg COP", min_value=1.0, value=3.5, max_value=5.0, step=0.2)
        energy_coverage._geoenergy_cop_calculation()
        df["S2 - Kompressor"] = energy_coverage.gshp_compressor_arr
        df["S2 - Levert energi fra brønner"] = energy_coverage.gshp_delivered_arr
        Plotting().hourly_triple_stack_plot(energy_coverage.gshp_compressor_arr, energy_coverage.gshp_delivered_arr, energy_coverage.non_covered_arr, "Strøm til varmepumpe", "Levert energi fra brønner", "Spisslast", Plotting().GRASS_BLUE, Plotting().GRASS_GREEN, Plotting().SPRING_BLUE)
        with st.expander("Varighetskurve"):
            Plotting().hourly_triple_stack_plot(np.sort(energy_coverage.gshp_compressor_arr)[::-1], np.sort(energy_coverage.gshp_delivered_arr)[::-1], np.sort(energy_coverage.non_covered_arr)[::-1], "Kompressor", "Levert energi fra brønner", "Spisslast", Plotting().GRASS_BLUE, Plotting().GRASS_GREEN, Plotting().SPRING_BLUE)
        st.subheader("Gjenstående elektrisk behov")
        df["S2 - Totalt elektrisk"] = electric_array + energy_coverage.non_covered_arr + energy_coverage.gshp_compressor_arr
        Plotting().hourly_plot(electric_array + energy_coverage.non_covered_arr + energy_coverage.gshp_compressor_arr, "Totalt elektrisk behov; uten solproduksjon", Plotting().GRASS_BLUE)
        with st.expander("Varighetskurve"):
            Plotting().hourly_plot(np.sort(electric_array + energy_coverage.non_covered_arr + energy_coverage.gshp_compressor_arr)[::-1], "Totalt elektrisk behov; uten solproduksjon", Plotting().GRASS_BLUE)
        df["S2 - Totalt elektrisk med solproduksjon"] = electric_array + energy_coverage.non_covered_arr + energy_coverage.gshp_compressor_arr - solar_array
        Plotting().hourly_negative_plot(electric_array + energy_coverage.non_covered_arr + energy_coverage.gshp_compressor_arr - solar_array, "Totalt elektrisk behov; med solproduksjon", Plotting().GRASS_BLUE)
        with st.expander("Varighetskurve"):
            Plotting().hourly_negative_plot(np.sort(electric_array + energy_coverage.non_covered_arr + energy_coverage.gshp_compressor_arr - solar_array)[::-1], "Totalt elektrisk behov; med solproduksjon", Plotting().GRASS_BLUE)
        with st.expander("Kostnader", expanded=True):
            months = ["jan", "feb", "mar", "apr", "mai", "jun", "jul", "aug", "sep", "okt", "nov", "des"]
            cost_per_month_el = hour_to_month(ELPRICE*(electric_array + energy_coverage.non_covered_arr + energy_coverage.gshp_compressor_arr - solar_array))
            cost_per_month_districtheating = 0
            Plotting().xy_plot_bar_stacked(months, "Måneder i ett år", cost_per_month_el, cost_per_month_districtheating, f"Strøm: {int(round(np.sum(cost_per_month_el),-3)):,} kr/år".replace(",", " "), f"Fjernvarme: {int(round(np.sum(cost_per_month_districtheating),-3)):,} kr/år".replace(",", " "), 0, MAX_VALUE, "Kostnad [kr]", Plotting().GRASS_BLUE, Plotting().FOREST_GREEN)
            st.write(f"**Sum: {int(round(np.sum(cost_per_month_districtheating) + np.sum(cost_per_month_el),-3)):,} kr**".replace(",", " "))
            df2 = pd.DataFrame({"Strøm" : cost_per_month_el, "Fjernvarme" : cost_per_month_districtheating})
        st.markdown("---")
        #np.savetxt('src/data/output/Kompressor.csv', energy_coverage.gshp_compressor_arr, delimiter=',')
        #--
        st.header("Alternativer for spisslast - Akkumuleringstank")
        selected_max_index = st.number_input("Velg maksindeks", value=8623, step = 10)
        max_effect_noncovered = max(energy_coverage.non_covered_arr)
        st.write("**Før akkumulering**")
        Plotting().hourly_plot(energy_coverage.non_covered_arr, "Spisslast", Plotting().SPRING_BLUE, 0, 1.1*max_effect_noncovered, max_effect_noncovered, winterweek=True, max_index=selected_max_index)
        Plotting().hourly_plot(energy_coverage.non_covered_arr, "Spisslast", Plotting().SPRING_BLUE, 0, 1.1*max_effect_noncovered, max_effect_noncovered, winterweek=0)
        with st.expander("Varighetskurve"):
            Plotting().hourly_plot(np.sort(energy_coverage.non_covered_arr)[::-1], "Spisslast", Plotting().SPRING_BLUE, 0, 1.1*max_effect_noncovered, max_effect_noncovered)
        st.write("**Etter akkumulering**")
        effect_reduction = st.number_input("Ønsket effektreduksjon [kW]", value=int(round(max_effect_noncovered/10,0)), step=10)
        if effect_reduction > max_effect_noncovered:
            st.warning("Effektreduksjon kan ikke være høyere enn effekttopp")
            st.stop()
        TO_TEMP = st.number_input("Turtemperatur [°C]", value = 60)
        FROM_TEMP = st.number_input("Returtemperatur [°C]", value = 40)
        peakshaving_arr, peakshaving_effect = peakshaving(energy_coverage.non_covered_arr, effect_reduction, TO_TEMP, FROM_TEMP)
        Plotting().hourly_plot(peakshaving_arr, "Spisslast", Plotting().SPRING_BLUE, 0, 1.1*max_effect_noncovered, peakshaving_effect, winterweek=True, max_index=selected_max_index)
        Plotting().hourly_plot(peakshaving_arr, "Spisslast", Plotting().SPRING_BLUE, 0, 1.1*max_effect_noncovered, peakshaving_effect, winterweek=0)
        with st.expander("Varighetskurve"):
            Plotting().hourly_plot(np.sort(peakshaving_arr)[::-1], "Spisslast", Plotting().SPRING_BLUE, 0, 1.1*max_effect_noncovered, peakshaving_effect)
        st.write("**Oppsummert**")
        Plotting().hourly_double_plot(energy_coverage.non_covered_arr, peakshaving_arr, "Spisslast (opprinnelig)", "Spisslast med akkumuleringstank", Plotting().SPRING_BLUE, Plotting().GRASS_BLUE, winterweek=True, max_index=selected_max_index)
        Plotting().hourly_double_plot(energy_coverage.non_covered_arr, peakshaving_arr, "Spisslast (opprinnelig)", "Spisslast med akkumuleringstank", Plotting().SPRING_BLUE, Plotting().GRASS_BLUE, winterweek=True, hours=100, max_index=selected_max_index)
        Plotting().hourly_double_plot(energy_coverage.non_covered_arr, peakshaving_arr, "Spisslast (opprinnelig)", "Spisslast med akkumuleringstank", Plotting().SPRING_BLUE, Plotting().GRASS_BLUE, winterweek=0)
        st.markdown("---")
    if st.checkbox("Scenario 3) Fjernvarme og grunnvarme"):
        #--
        st.markdown("---")
        st.header("Fjernvarme/grunnvarme")
        new_thermal_array = thermal_array
        st.subheader("Lading av brønner med fjernvarme")
        selected_case = st.selectbox("Type lading?", options=["Lading hver natt hele året", "Konstant lading om sommeren", "Lading hver natt om sommeren"], index=2)
        st.caption("Om natten betyr fra klokken 00 - 06")
        charge_arr = np.zeros(8760)
        charging_amount = st.number_input("Lading [kW]", value = 800)
        if selected_case == "Lading hver natt hele året":
            #case 1 - lading hver natt
            for i in range(0, len(charge_arr)):
                j = i % 24
                if j == 0 or j == 1 or j == 1 or j == 2 or j == 3 or j == 4 or j == 5:
                    charge_arr[i] = charging_amount
        if selected_case == "Konstant lading om sommeren":
            #case 2 - lading om sommeren
            for i in range(0, len(charge_arr)):
                if i > 2904 and i < 5856:
                    charge_arr[i] = charging_amount
        if selected_case == "Lading hver natt om sommeren":
            #case 3 - lading hver natt om sommeren
            for i in range(0, len(charge_arr)):
                if i > 2904 and i < 5856:
                    j = i % 24
                    if j == 0 or j == 1 or j == 1 or j == 2 or j == 3 or j == 4 or j == 5:
                        charge_arr[i] = charging_amount

        if np.sum(charge_arr) > np.sum(thermal_array):
            st.stop()
        Plotting().hourly_plot(charge_arr, "Lading", Plotting().FOREST_GREEN)
        np.savetxt('src/data/output/Lading.csv', charge_arr, delimiter=',')
        Plotting().hourly_plot(charge_arr, "Lading (zoomet inn)", Plotting().FOREST_GREEN, winterweek=True, max_index=4000)
        st.subheader("Sammenstilt termisk behov med lading")
        #se på denne
        Plotting().hourly_plot_with_negative(new_thermal_array, charge_arr, "Termisk (romoppvarming + tappevann)", Plotting().FOREST_DARK_BROWN, Plotting().FOREST_GREEN)

        st.subheader("Dekningsgrad")
        selected_fjernvarme = st.selectbox("Velg fjernvarmedekning", options=["Fjernvarme dekker tappevann", "Grunnvarme dekker tappevann"])
        if selected_fjernvarme == "Fjernvarme dekker tappevann":
            new_thermal_array = space_heating_array
        elif selected_fjernvarme == "Grunnvarme dekker tappevann":
            new_thermal_array = thermal_array
        energy_coverage = EnergyCoverage(new_thermal_array)
        energy_coverage.COVERAGE = st.number_input("Velg energidekningsgrad [%]", min_value=50, value=90, max_value=100, step=2, key="grunnvarmedekning")    
        energy_coverage._coverage_calculation()
        df["S2 - Grunnvarmedekning"] = energy_coverage.covered_arr
        df["S2 - Spisslast"] = energy_coverage.non_covered_arr
        #Plotting().hourly_stack_plot(energy_coverage.covered_arr, energy_coverage.non_covered_arr, "Grunnvarmedekning", "Spisslast", Plotting().SPRING_GREEN, Plotting().SPRING_BLUE)
        if selected_fjernvarme == "Fjernvarme dekker tappevann":
            Plotting().hourly_stack_plot_quad_negative(dhw_array, energy_coverage.covered_arr, charge_arr, energy_coverage.non_covered_arr, "Tappevann (fjernvarme)", "Grunnvarme", "Spisslast", Plotting().FOREST_PURPLE, Plotting().SPRING_GREEN, Plotting().FOREST_GREEN, Plotting().SPRING_BLUE)
            np.savetxt('src/data/output/dhw_array.csv', dhw_array, delimiter=',')
            np.savetxt('src/data/output/grunnvarmedekning.csv', energy_coverage.covered_arr, delimiter=',')
            np.savetxt('src/data/output/lading.csv', charge_arr, delimiter=',')
            np.savetxt('src/data/output/spisslast.csv', energy_coverage.non_covered_arr, delimiter=',')
        elif selected_fjernvarme == "Grunnvarme dekker tappevann":
            Plotting().hourly_stack_plot_negative(energy_coverage.covered_arr, energy_coverage.non_covered_arr, charge_arr, "Grunnvarme", "Spisslast", Plotting().SPRING_GREEN, Plotting().SPRING_BLUE, Plotting().FOREST_PURPLE)
        #np.savetxt('src/data/output/Grunnvarmedekning.csv', energy_coverage.covered_arr, delimiter=',')
        #np.savetxt('src/data/output/Spisslast.csv', energy_coverage.non_covered_arr, delimiter=',')
        with st.expander("Varighetskurve"):
            Plotting().hourly_stack_plot(np.sort(energy_coverage.covered_arr)[::-1], np.sort(energy_coverage.non_covered_arr)[::-1], "Grunnvarmedekning", "Spisslast", Plotting().SPRING_GREEN, Plotting().SPRING_BLUE)
        st.subheader("Årsvarmefaktor")
        energy_coverage.COP = st.number_input("Velg COP", min_value=1.0, value=3.5, max_value=5.0, step=0.2, key="cop1")
        energy_coverage._geoenergy_cop_calculation()
        df["S2 - Kompressor"] = energy_coverage.gshp_compressor_arr
        df["S2 - Levert energi fra brønner"] = energy_coverage.gshp_delivered_arr
        #Plotting().hourly_triple_stack_plot(energy_coverage.gshp_compressor_arr, energy_coverage.gshp_delivered_arr, energy_coverage.non_covered_arr, "Kompressor", "Levert energi fra brønner", "Spisslast", Plotting().GRASS_BLUE, Plotting().GRASS_GREEN, Plotting().SPRING_BLUE)
        if selected_fjernvarme == "Grunnvarme dekker tappevann":
            Plotting().hourly_triple_stack_plot_negative(energy_coverage.gshp_compressor_arr, energy_coverage.gshp_delivered_arr, energy_coverage.non_covered_arr, charge_arr, "Strøm til varmepumpe", "Levert energi fra brønner", "Spisslast", Plotting().GRASS_BLUE, Plotting().GRASS_GREEN, Plotting().SPRING_BLUE, Plotting().FOREST_GREEN)
            Plotting().hourly_triple_stack_plot_negative(np.sort(energy_coverage.gshp_compressor_arr)[::-1], np.sort(energy_coverage.gshp_delivered_arr)[::-1], np.sort(energy_coverage.non_covered_arr)[::-1], -np.sort(charge_arr)[::-1], "Strøm til varmepumpe", "Levert energi fra brønner", "Spisslast", Plotting().GRASS_BLUE, Plotting().GRASS_GREEN, Plotting().SPRING_BLUE, Plotting().FOREST_GREEN)

        if selected_fjernvarme == "Fjernvarme dekker tappevann":
            Plotting().hourly_quad_stack_plot_negative(dhw_array, energy_coverage.gshp_compressor_arr, energy_coverage.gshp_delivered_arr, energy_coverage.non_covered_arr, charge_arr, "Tappevann (fjernvarme)", "Strøm til varmepumpe", "Levert energi fra brønner", "Spisslast", Plotting().FOREST_PURPLE, Plotting().GRASS_BLUE, Plotting().GRASS_GREEN, Plotting().SPRING_BLUE, Plotting().FOREST_GREEN)
            Plotting().hourly_quad_stack_plot_negative(np.sort(dhw_array)[::-1], np.sort(energy_coverage.gshp_compressor_arr)[::-1], np.sort(energy_coverage.gshp_delivered_arr)[::-1], np.sort(energy_coverage.non_covered_arr)[::-1], -np.sort(charge_arr)[::-1], "Tappevann (fjernvarme)", "Strøm til varmepumpe", "Levert energi fra brønner", "Spisslast", Plotting().FOREST_PURPLE, Plotting().GRASS_BLUE, Plotting().GRASS_GREEN, Plotting().SPRING_BLUE, Plotting().FOREST_GREEN)

        with st.expander("Varighetskurve"):
            Plotting().hourly_triple_stack_plot(np.sort(energy_coverage.gshp_compressor_arr)[::-1], np.sort(energy_coverage.gshp_delivered_arr)[::-1], np.sort(energy_coverage.non_covered_arr)[::-1], "Strøm til varmepumpe", "Levert energi fra brønner", "Spisslast", Plotting().GRASS_BLUE, Plotting().GRASS_GREEN, Plotting().SPRING_BLUE)
        st.subheader("Gjenstående elektrisk behov")
        df["S2 - Totalt elektrisk"] = electric_array + energy_coverage.non_covered_arr + energy_coverage.gshp_compressor_arr
        Plotting().hourly_plot(electric_array + energy_coverage.non_covered_arr + energy_coverage.gshp_compressor_arr, "Totalt elektrisk behov; uten solproduksjon", Plotting().GRASS_BLUE)
        with st.expander("Varighetskurve"):
            Plotting().hourly_plot(np.sort(electric_array + energy_coverage.non_covered_arr + energy_coverage.gshp_compressor_arr)[::-1], "Totalt elektrisk behov; uten solproduksjon", Plotting().GRASS_BLUE)
        df["S2 - Totalt elektrisk med solproduksjon"] = electric_array + energy_coverage.non_covered_arr + energy_coverage.gshp_compressor_arr - solar_array
        Plotting().hourly_negative_plot(electric_array + energy_coverage.non_covered_arr + energy_coverage.gshp_compressor_arr - solar_array, "Totalt elektrisk behov; med solproduksjon", Plotting().GRASS_BLUE)
        with st.expander("Varighetskurve"):
            Plotting().hourly_negative_plot(np.sort(electric_array + energy_coverage.non_covered_arr + energy_coverage.gshp_compressor_arr - solar_array)[::-1], "Totalt elektrisk behov; med solproduksjon", Plotting().GRASS_BLUE)
        with st.expander("Kostnader", expanded=True):
            months = ["jan", "feb", "mar", "apr", "mai", "jun", "jul", "aug", "sep", "okt", "nov", "des"]
            cost_per_month_el = hour_to_month(ELPRICE*(electric_array + energy_coverage.non_covered_arr + energy_coverage.gshp_compressor_arr - solar_array))
            cost_per_month_districtheating = hour_to_month(charge_arr * DISTRICTHEATING_PRICE)
            if selected_fjernvarme == "Fjernvarme dekker tappevann":
                cost_per_month_districtheating = hour_to_month((charge_arr + dhw_array) * DISTRICTHEATING_PRICE)
            else:
                cost_per_month_districtheating = hour_to_month(charge_arr * DISTRICTHEATING_PRICE)
            Plotting().xy_plot_bar_stacked(months, "Måneder i ett år", cost_per_month_el, cost_per_month_districtheating, f"Strøm: {int(round(np.sum(cost_per_month_el),-3)):,} kr/år".replace(",", " "), f"Fjernvarme: {int(round(np.sum(cost_per_month_districtheating),-3)):,} kr/år".replace(",", " "), 0, MAX_VALUE, "Kostnad [kr]", Plotting().GRASS_BLUE, Plotting().FOREST_GREEN)
            st.write(f"**Sum: {int(round(np.sum(cost_per_month_districtheating) + np.sum(cost_per_month_el),-3)):,} kr**".replace(",", " "))
            df3 = pd.DataFrame({"Strøm" : cost_per_month_el, "Fjernvarme" : cost_per_month_districtheating})

        simulation_obj = GheTool()
        a = False
        b = True
        heat_arr = []
        cool_arr = []
        st.write(f"Hentes fra brønner: {int(np.sum(energy_coverage.gshp_delivered_arr))} kWh")
        #Plotting().hourly_plot(energy_coverage.gshp_delivered_arr, "Hentes fra brønner", Plotting().FOREST_DARK_PURPLE)
        st.write(f"Lading: {int(np.sum(charge_arr))} kWh")
        #Plotting().hourly_plot(charge_arr, "Lading (tilføres brønner)", Plotting().FOREST_DARK_PURPLE)
        
        if b == True:
            heat_arr = energy_coverage.gshp_delivered_arr
            cool_arr = charge_arr
            simulation_obj.monthly_load_heating = hour_to_month(heat_arr)
            simulation_obj.monthly_load_cooling = hour_to_month(cool_arr)
        if a == True:
            for i in range(0, len(energy_coverage.gshp_delivered_arr)):
                value = energy_coverage.gshp_delivered_arr[i]
                heat_arr.append(value)
                cool_arr.append(value)
            heat_arr = np.array(heat_arr)
            cool_arr = np.array(cool_arr)
            heat_arr[heat_arr < 0] = 0
            cool_arr[cool_arr > 0] = 0
            cool_arr = -cool_arr
            simulation_obj.monthly_load_heating = hour_to_month(heat_arr)
            st.write(np.sum(heat_arr))
            st.write(np.sum(cool_arr))
            #--
            #heat_arr skal være samme som opprinnelig 90% dekningsgrad
            #cool_arr skal være samme som charge_arr 
            #--
            simulation_obj.peak_heating = np.full((1, 12), energy_coverage.heat_pump_size).flatten().tolist()
            simulation_obj.monthly_load_cooling = hour_to_month(cool_arr)
        else:
            simulation_obj.monthly_load_heating = hour_to_month(energy_coverage.gshp_delivered_arr)
            simulation_obj.peak_heating = np.full((1, 12), energy_coverage.heat_pump_size).flatten().tolist()
            simulation_obj.monthly_load_cooling = hour_to_month(charge_arr)
            #simulation_obj.peak_cooling = np.full((1, 12), cooling_effect).flatten().tolist()
        #well_guess = int(round(np.sum(energy_coverage.gshp_delivered_arr)/80/300,2))

        with st.form("Inndata"):
            c1, c2 = st.columns(2)
            with c1:
                simulation_obj.K_S = st.number_input("Effektiv varmledningsevne [W/m∙K]", min_value=1.0, value=4.0, max_value=10.0, step=1.0) 
                simulation_obj.T_G = st.number_input("Uforstyrret temperatur [°C]", min_value=1.0, value=8.5, max_value=20.0, step=1.0)
                simulation_obj.R_B = st.number_input("Borehullsmotstand [m∙K/W]", min_value=0.0, value=0.10, max_value=2.0, step=0.01)
                simulation_obj.N_1= st.number_input("Antall brønner (X)", value=21, step=1) 
                simulation_obj.N_2= st.number_input("Antall brønner (Y)", value=2, step=1)
                #--
                simulation_obj.COP = energy_coverage.COP
            with c2:
                H = st.number_input("Brønndybde [m]", min_value=100, value=300, max_value=500, step=10)
                GWT = st.number_input("Grunnvannsstand [m]", min_value=0, value=5, max_value=100, step=1)
                simulation_obj.H = H - GWT
                simulation_obj.B = st.number_input("Avstand mellom brønner", min_value=1, value=15, max_value=30, step=1)
                simulation_obj.RADIUS = st.number_input("Brønndiameter [mm]", min_value = 80, value=115, max_value=300, step=1) / 2000
                heat_carrier_fluid_types = ["HX24", "HX35", "Kilfrost GEO 24%", "Kilfrost GEO 32%", "Kilfrost GEO 35%"]    
                heat_carrier_fluid = st.selectbox("Type kollektorvæske", options=list(range(len(heat_carrier_fluid_types))), format_func=lambda x: heat_carrier_fluid_types[x])
                simulation_obj.FLOW = 0.5
                #simulation_obj.peak_heating = st.number_input("Varmepumpe [kW]", value = int(round(energy_coverage.heat_pump_size,0)), step=10)
            st.form_submit_button("Kjør simulering")
            heat_carrier_fluid_densities = [970.5, 955, 1105.5, 1136.2, 1150.6]
            heat_carrier_fluid_capacities = [4.298, 4.061, 3.455, 3.251, 3.156]
            simulation_obj.DENSITY = heat_carrier_fluid_densities[heat_carrier_fluid]
            simulation_obj.HEAT_CAPACITY = heat_carrier_fluid_capacities[heat_carrier_fluid]
            simulation_obj._run_simulation()
            
    #Plotting().plot_clustered_stacked([df1, df2, df3],["Scenario 1", "Scenario 2", "Scenario 3"], color=[Plotting().GRASS_BLUE, Plotting().FOREST_GREEN])


#    st.header("Fjernvarme/grunnvarme/solenergi")
#    st.subheader("Dekningsgrad, grunnvarme/romoppvarming")
#    energy_coverage = EnergyCoverage(space_heating_array)
#    energy_coverage.COVERAGE = st.number_input("Velg energidekningsgrad for romoppvarming [%]", min_value=50, value=70, max_value=100, step=2, key="fjernvarme/grunnvarme/solenergi")    
#    energy_coverage._coverage_calculation()
#    df["S3 - Grunnvarmedekning"] = energy_coverage.covered_arr
#    df["S3 - Spisslast"] = energy_coverage.non_covered_arr
#    Plotting().hourly_stack_plot(energy_coverage.covered_arr, energy_coverage.non_covered_arr, "Grunnvarmedekning", "Spisslast", Plotting().FOREST_BROWN, Plotting().SPRING_BLUE)
#    with st.expander("Varighetskurve"):
#        Plotting().hourly_stack_plot(np.sort(energy_coverage.covered_arr)[::-1], np.sort(energy_coverage.non_covered_arr)[::-1], "Grunnvarmedekning", "Spisslast", Plotting().FOREST_BROWN, Plotting().SPRING_BLUE)
#    st.subheader("Årsvarmefaktor, grunnvarme/romoppvarming")
#    energy_coverage.COP = st.number_input("Velg COP", min_value=1.0, value=3.5, max_value=5.0, step=0.2, key="fjernvarme/grunnvarme/solenergi-cop")
#    energy_coverage._geoenergy_cop_calculation()
#    df["S3 - Kompressor"] = energy_coverage.gshp_compressor_arr
#    df["S3 - Levert fra brønner"] = energy_coverage.gshp_delivered_arr
#    Plotting().hourly_triple_stack_plot(energy_coverage.gshp_compressor_arr, energy_coverage.gshp_delivered_arr, energy_coverage.non_covered_arr, "Kompressor", "Levert energi fra brønner", "Spisslast", Plotting().GRASS_BLUE, Plotting().GRASS_GREEN, Plotting().SPRING_BLUE)
#    with st.expander("Varighetskurve"):
#        Plotting().hourly_triple_stack_plot(np.sort(energy_coverage.gshp_compressor_arr)[::-1], np.sort(energy_coverage.gshp_delivered_arr)[::-1], np.sort(energy_coverage.non_covered_arr)[::-1], "Kompressor", "Levert energi fra brønner", "Spisslast", Plotting().GRASS_BLUE, Plotting().GRASS_GREEN, Plotting().SPRING_BLUE)
#    st.subheader("Konsept")
#    Plotting().hourly_triple_stack_plot(dhw_array, energy_coverage.covered_arr, energy_coverage.non_covered_arr, "Tappevann(fjernvarme)", "Romoppvarming(grunnvarme)", "Romoppvarmingsspisslast(fjernvarme)", 
#    Plotting().FOREST_PURPLE, Plotting().SPRING_GREEN, Plotting().SPRING_BLUE)
#    Plotting().hourly_quad_stack_plot(dhw_array, energy_coverage.gshp_compressor_arr, energy_coverage.gshp_delivered_arr, energy_coverage.non_covered_arr, "Tappevann(fjernvarme)", "Kompressor(grunnvarme)", "Levert fra brønner(grunnvarme)", "Romoppvarmingspisslast(fjernvarme)", 
#    Plotting().FOREST_PURPLE, Plotting().GRASS_BLUE, Plotting().GRASS_GREEN, Plotting().SPRING_BLUE)
#    with st.expander("Varighetskurve"):
#        Plotting().hourly_quad_stack_plot(np.sort(dhw_array)[::-1], np.sort(energy_coverage.gshp_compressor_arr)[::-1], np.sort(energy_coverage.gshp_delivered_arr)[::-1], np.sort(energy_coverage.non_covered_arr)[::-1], "Tappevann(fjernvarme)", "Kompressor(grunnvarme)", "Levert fra brønner(grunnvarme)", "Romoppvarmingspisslast(fjernvarme)", 
#    Plotting().FOREST_PURPLE, Plotting().GRASS_BLUE, Plotting().GRASS_GREEN, Plotting().SPRING_BLUE)
#    st.subheader("Gjenstående elektrisk behov")
#    df["S3 - Totalt elektrisk"] = electric_array + energy_coverage.gshp_compressor_arr
#    df["S3 - Totalt elektrisk med solproduksjon"] = electric_array + energy_coverage.gshp_compressor_arr - solar_array
#    Plotting().hourly_plot(electric_array + energy_coverage.gshp_compressor_arr, "Totalt elektrisk behov; uten solproduksjon", Plotting().GRASS_BLUE)
#    Plotting().hourly_negative_plot(electric_array + energy_coverage.gshp_compressor_arr - solar_array, "Totalt elektrisk behov; med solproduksjon", Plotting().GRASS_BLUE)

#    with st.expander("Kostnader"):
#        months = ["jan", "feb", "mar", "apr", "mai", "jun", "jul", "aug", "sep", "okt", "nov", "des"]
#        cost_per_month_el = hour_to_month(ELPRICE*(electric_array + energy_coverage.gshp_compressor_arr - solar_array))
#        cost_per_month_districtheating = hour_to_month(DISTRICTHEATING_PRICE*(energy_coverage.non_covered_arr + dhw_array))
#        Plotting().xy_plot_bar_stacked(months, "Måneder i ett år", cost_per_month_el, cost_per_month_districtheating, f"Strøm: {int(round(np.sum(cost_per_month_el),-3)):,} kr/år".replace(",", " "), f"Fjernvarme: {int(round(np.sum(cost_per_month_districtheating),-3)):,} kr/år".replace(",", " "), 0, MAX_VALUE, "Kostnad [kr]", Plotting().GRASS_BLUE, Plotting().FOREST_GREEN)
#        st.write(f"**Sum: {int(round(np.sum(cost_per_month_districtheating) + np.sum(cost_per_month_el),-3)):,} kr**".replace(",", " "))
#        df3 = pd.DataFrame({"Strøm" : cost_per_month_el, "Fjernvarme" : cost_per_month_districtheating})

#    #np.savetxt('src/data/output/Fjernvarme_3.csv', (dhw_array + energy_coverage.non_covered_arr), delimiter=',')
#    #np.savetxt('src/data/output/Kompressor_3.csv', (energy_coverage.gshp_compressor_arr), delimiter=',')
#    df.to_csv("src/data/output/hei.csv", sep=";")

#    # create fake dataframes
#    df1 = pd.DataFrame(np.random.rand(4, 5),
#                    index=["A", "B", "C", "D"],
#                    columns=["I", "J", "K", "L", "M"])
#    df2 = pd.DataFrame(np.random.rand(4, 5),
#                    index=["A", "B", "C", "D"],
#                    columns=["I", "J", "K", "L", "M"])
#    df3 = pd.DataFrame(np.random.rand(4, 5),
#                    index=["A", "B", "C", "D"], 
#                    columns=["I", "J", "K", "L", "M"])

    # Then, just call :
#    Plotting().plot_clustered_stacked([df1, df2, df3],["Scenario 1", "Scenario 2", "Scenario 3"], color=[Plotting().GRASS_BLUE, Plotting().FOREST_GREEN])

#    st.markdown("---")
    #--
#    st.title("Brønnpark")
#    simulation_obj = GheTool()
#    simulation_obj.monthly_load_heating = hour_to_month(energy_coverage.gshp_delivered_arr)
#    simulation_obj.monthly_load_cooling = cooling_per_month
#    simulation_obj.peak_heating = energy_coverage.heat_pump_size
#    simulation_obj.peak_cooling = cooling_effect
#    well_guess = int(round(np.sum(energy_coverage.gshp_delivered_arr)/80/300,2))
#    st.markdown(f"Estimert ca. **{well_guess}** brønner a 300 m ")
#    verdi = 5
#    with st.form("Inndata"):
#        c1, c2 = st.columns(2)
#        with c1:
#            simulation_obj.K_S = st.number_input("Varmledningsevne", min_value=1.0, value=3.5, max_value=10.0, step=1.0) 
#            simulation_obj.T_G = st.number_input("Uforstyrret temperatur", min_value=1.0, value=8.0, max_value=20.0, step=1.0)
#            simulation_obj.R_B = st.number_input("Målt borehullsmotstand", min_value=0.0, value=0.08, max_value=2.0, step=0.01) + 0.02
#            simulation_obj.N_1= st.number_input("Antall brønner (X)", value=well_guess, step=1) 
#            simulation_obj.N_2= st.number_input("Antall brønner (Y)", value=1, step=1) 
#        with c2:
#            H = st.number_input("Brønndybde [m]", min_value=100, value=300, max_value=500, step=10)
#            GWT = st.number_input("Grunnvannsstand [m]", min_value=0, value=5, max_value=100, step=1)
#            simulation_obj.H = H - GWT
#            simulation_obj.B = st.number_input("Avstand mellom brønner", min_value=1, value=15, max_value=30, step=1)
#            simulation_obj.RADIUS = st.number_input("Brønndiameter [mm]", min_value = 80, value=115, max_value=300, step=1) / 2000
#        st.form_submit_button("Kjør simulering")
#        simulation_obj._run_simulation()

#    #st.title("Kostnader")
#    #st.caption("Under arbeid")
#    #tab1, tab2 = st.tabs(["Direkte kjøp", "Lånefinansiert"])
#    #with tab1:
#    #    costs_operation = Costs(meters)
#    #    costs_operation._calculate_monthly_costs(demand_array, energy_coverage.gshp_compressor_arr, energy_coverage.non_covered_arr, costs_operation.INVESTMENT)
#    #    costs_operation._show_operation_costs(costs_operation.INVESTMENT)
#        #costs.operation_show_after()
#        #costs.plot("Driftskostnad")
#        #costs.profitibality_operation()
#    #with tab2:
#    #    costs_operation_and_investment = Costs(meters)
#    #    costs_operation_and_investment._calculate_monthly_costs(demand_array, energy_coverage.gshp_compressor_arr, energy_coverage.non_covered_arr, 0)
#    #    costs_operation_and_investment._show_operation_costs(0)
#        #costs.operation_and_investment_show()
#        #costs.plot("Totalkostnad")
#        #         #costs.profitibality_operation_and_investment() 
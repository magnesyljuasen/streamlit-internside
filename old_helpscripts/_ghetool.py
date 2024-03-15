# import all the relevant functions
from GHEtool import Borefield, GroundData
from old_helpscripts._utils import Plotting
import numpy as np
import streamlit as st
import pygfunction as gt
#--
import streamlit as st 

class GheTool:
    def __init__(self):
        self.YEARS = 50
        #  extras
        self.COP = 3.5
        self.DENSITY = 970.5
        self.HEAT_CAPACITY = 4.298
        self.FLOW = 0.5
        #  ground
        self.K_S = 3  # conductivity of the soil (W/mK)
        self.T_G = 8  # Ground temperature at infinity (degrees C)
        self.R_B = 0.10  # equivalent borehole resistance (K/W)
        self.VOL = 2.4 * 10**6  # ground volumetric heat capacity (J/m3K)
        self.FLUX = 0.04  # geothermal heat flux (W/m2)
        #  well
        self.H = 300
        self.B = 15
        self.RADIUS = 0.0575
        #  number of wells
        self.N_1 = 10
        self.N_2 = 10
        #  monthly loading values
        self.peak_cooling = np.array([0., 0, 34., 69., 133., 187., 213., 240., 160., 37., 0., 0.])  # Peak cooling in kW
        self.peak_heating = np.array([160., 142, 102., 55., 0., 0., 0., 0., 40.4, 85., 119., 136.])  # Peak heating in kW
        #  annual heating and cooling load
        self.annual_heating_load = 300 * 10 ** 3  # kWh
        self.annual_cooling_load = 150 * 10 ** 3  # kWh
        #  percentage of annual load per month (15.5% for January ...)
        self.monthly_load_heating_percentage = np.array([0.155, 0.148, 0.125, .099, .064, 0., 0., 0., 0.061, 0.087, 0.117, 0.144])
        self.monthly_load_cooling_percentage = np.array([0.025, 0.05, 0.05, .05, .075, .1, .2, .2, .1, .075, .05, .025])
        #  resulting load per month
        self.monthly_load_heating = self.annual_heating_load * self.monthly_load_heating_percentage   # kWh
        self.monthly_load_cooling = self.annual_cooling_load * self.monthly_load_cooling_percentage   # kWh      

    def _run_simulation(self):
        #  grounddata
        data = GroundData(self.K_S, self.T_G, self.R_B, self.VOL, self.FLUX)
        #  create the borefield object
        borefield = Borefield(simulation_period=self.YEARS,
                    peak_heating=self.peak_heating,
                    peak_cooling=self.peak_cooling,
                    baseload_heating=self.monthly_load_heating,
                    baseload_cooling=self.monthly_load_cooling)
        monthly_load_heating_sum = int(np.sum(self.monthly_load_heating))

        borefield.set_ground_parameters(data)
        selected_field = st.selectbox("Type konfigurasjon", options=["Linje/rektangel", "Åpent"])
        if selected_field == "Linje/rektangel":
            field = borefield.create_rectangular_borefield(self.N_1, self.N_2, self.B, self.B, self.H, 10, self.RADIUS)
        if selected_field == "Åpent":
            field = gt.boreholes.U_shaped_field(self.N_1, self.N_2, self.B, self.B, self.H, 10, self.RADIUS)
        borefield.set_borefield(field)
        with st.expander("Se konfigurasjon"):
            st.pyplot(gt.boreholes.visualize_field(field))
        borefield.calculate_temperatures()
        x = np.arange(0,len(borefield.results_month_heating))
        with st.expander("Se resultater", expanded=True):
            st.write(f"**{borefield.number_of_boreholes} brønn(er) á {self.H} aktiv brønndybde med {self.B} m avstand**")
            meters = (self.N_1 * self.N_2) * self.H
            Plotting().xy_simulation_plot(x, 0, self.YEARS, "År", borefield.results_month_heating, 
            borefield.results_peak_heating, "Gj.snittlig kollektorvæsketemperatur [°C]", "Ved dellast", f"Ved maksimal varmeeffekt", Plotting().GRASS_GREEN, Plotting().GRASS_RED)
            st.write(f"Laveste gj.snittlige kollektorvæsketemperatur v/dellast: **{round(min(borefield.results_month_heating),1)} °C**")
            st.write(f"Laveste gj.snittlige kollektorvæsketemperatur v/maksimal varmeeffekt: **{round(min(borefield.results_peak_heating),1)} °C**")
            #--
            Q = (max(self.peak_heating)-max(self.peak_heating)/self.COP)/(self.N_1 * self.N_2)
            #st.caption(f"Levert effekt fra brønnpark: {round(self.peak_heating-self.peak_heating/self.COP,1)} kW | Levert effekt per brønn (Q): {round(Q,1)} kW")
            delta_T = round((Q*1000)/(self.DENSITY*self.FLOW*self.HEAT_CAPACITY),1)
            st.write(f"- ΔT: {delta_T:,} °C".replace(',', ' '))
            st.write(f"- Kollektorvæsketemperatur inn til varmepumpe: {round(min(borefield.results_peak_heating) + delta_T/2,1):,} °C".replace(',', ' '))
            st.write(f"- Kollektorvæsketemperatur ut fra varmepumpe: {round(min(borefield.results_peak_heating) - delta_T/2,1):,} °C".replace(',', ' '))
            #--
            st.markdown("---")
            st.write(f"*Energi per meter: {int(round(monthly_load_heating_sum/meters,0)):,} kWh/m*".replace(',', ' '))
            st.write(f"*Effekt per meter: {int(round(np.max(self.peak_heating)*1000/meters,1)):,} W/m*".replace(',', ' '))
            #--
            if np.sum(self.monthly_load_cooling) > 0:   
                st.markdown("---")
                Plotting().xy_simulation_plot(x, 0, self.YEARS, "År", borefield.results_month_cooling, 
                borefield.results_peak_cooling, "Gj.snittlig kollektorvæsketemperatur [°C]", "Ved dellast", f"Ved maksimal kjøleeffekt", Plotting().GRASS_GREEN, Plotting().GRASS_BLUE)   
                st.write(f"Høyeste gj.snittlige kollektorvæsketemperatur v/maksimal kjøleeffekt: **{round(max(borefield.results_peak_cooling),1)} °C**")
                st.write(f"Laveste gj.snittlige kollektorvæsketemperatur v/maksimal kjøleeffekt: **{round(min(borefield.results_peak_cooling),1)} °C**")  
#            Q = (self.peak_heating-self.peak_heating/self.COP)/(self.N_1 * self.N_2)
#            st.caption(f"Levert effekt fra brønnpark: {round(self.peak_heating-self.peak_heating/self.COP,1)} kW | Levert effekt per brønn (Q): {round(Q,1)} kW")
#            delta_T = round((Q*1000)/(self.DENSITY*self.FLOW*self.HEAT_CAPACITY),1)
#            c1, c2, c3 = st.columns(3)
#            with c1:
#                st.metric("Aktive brønnmetere", value = f"{meters:,} m".replace(',', ' '))
#                st.metric("ΔT", value = f"{delta_T:,} °C".replace(',', ' '))
#            with c2:
          
#                st.metric("Inn til varmepumpe", value = f"{round(min(borefield.results_peak_heating) + delta_T/2,1):,} °C".replace(',', ' '))
#            with c3:
#                st.metric("Ut fra varmepumpe", value = f"{round(min(borefield.results_peak_heating) - delta_T/2,1):,} °C".replace(',', ' '))

            
            #borefield.results_peak_heating()
            #borefield.results_peak_cooling()











def main_functionalities():
    # relevant borefield data for the calculations
    data = GroundData(3,             # conductivity of the soil (W/mK)
                      8,            # Ground temperature at infinity (degrees C)
                      0.1,           # equivalent borehole resistance (K/W)
                      2.4 * 10**6)   # ground volumetric heat capacity (J/m3K)

    # monthly loading values
    peak_cooling = np.array([0., 0, 34., 69., 133., 187., 213., 240., 160., 37., 0., 0.])  # Peak cooling in kW
    peak_heating = np.array([160., 142, 102., 55., 0., 0., 0., 0., 40.4, 85., 119., 136.])  # Peak heating in kW

    # annual heating and cooling load
    annual_heating_load = 300 * 10 ** 3  # kWh
    annual_cooling_load = 150 * 10 ** 3  # kWh

    # percentage of annual load per month (15.5% for January ...)
    monthly_load_heating_percentage = np.array([0.155, 0.148, 0.125, .099, .064, 0., 0., 0., 0.061, 0.087, 0.117, 0.144])
    monthly_load_cooling_percentage = np.array([0.025, 0.05, 0.05, .05, .075, .1, .2, .2, .1, .075, .05, .025])

    # resulting load per month
    monthly_load_heating = annual_heating_load * monthly_load_heating_percentage   # kWh
    monthly_load_cooling = annual_cooling_load * monthly_load_cooling_percentage   # kWh

    # create the borefield object
    borefield = Borefield(simulation_period=20,
                          peak_heating=peak_heating,
                          peak_cooling=peak_cooling,
                          baseload_heating=monthly_load_heating,
                          baseload_cooling=monthly_load_cooling)

    borefield.set_ground_parameters(data)
    n = st.number_input("Antall", value=1, step=1)
    borefield.create_rectangular_borefield(n, 1, 15, 15, 300, 1, 0.075)
    
    # set temperature boundaries
    #borefield.set_max_ground_temperature(16)   # maximum temperature
    #borefield.set_min_ground_temperature(0)    # minimum temperature

    # size borefield
    #depth = borefield.size()
    #st.write("The borehole depth is: ", depth, "m")

    # print imbalance
    #st.write("The borefield imbalance is: ", borefield.imbalance, "kWh/y. (A negative imbalance means the the field is heat extraction dominated so it cools down year after year.)") # print imbalance

    # plot temperature profile for the calculated depth
    borefield.calculate_temperatures()
    st.line_chart(borefield.results_month_heating)
    st.line_chart(borefield.results_peak_heating)
    st.line_chart(borefield.results_peak_cooling)

    # plot temperature profile for a fixed depth
    #borefield.print_temperature_profile_fixed_depth(depth=75, legend=False)

    # print gives the array of monthly temperatures for peak cooling without showing the plot
    #borefield.calculate_temperatures(depth=90)
    #st.write("Result array for cooling peaks")
    #st.write("---------------------------------------------")

    # size the borefield for quadrant 3
    # for more information about borefield quadrants, see (Peere et al., 2021)
    #depth = borefield.size(100, quadrant_sizing=3)
    #st.write("The borehole depth is: ", str(round(depth, 2)), "m for a sizing in quadrant 3")
    # plot temperature profile for the calculated depth
    #borefield.print_temperature_profile(legend=True)

    # size with a dynamic Rb* value
    # note that the original Rb* value will be overwritten!

    # this requires pipe and fluid data
    #fluid_data = FluidData(0.2, 0.568, 998, 4180, 1e-3)
    #pipe_data = PipeData(1, 0.015, 0.02, 0.4, 0.05, number_of_pipes=2)
    #borefield.set_fluid_parameters(fluid_data)
    #borefield.set_pipe_parameters(pipe_data)

    # disable the use of constant_Rb with the setup, in order to plot the profile correctly
    # when it is given as an argument to the size function, it will size correctly, but the plot will be with
    # constant Rb* since it has not been changed in the setup function
    #borefield.sizing_setup(use_constant_Rb=False)
    #depth = borefield.size(100)
    #st.write("The borehole depth is: ", str(round(depth, 2)), "m for a sizing with dynamic Rb*.")
    #borefield.print_temperature_profile(legend=True)

import streamlit as st
import matplotlib.pyplot as plt
import numpy as np
from scipy.constants import pi
import pygfunction as gt
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
import numpy as np
from scipy.constants import pi
import pygfunction as gt
import pandas as pd
from old_helpscripts._utils import Plotting

class Simulation:
    def __init__(self):
        self._properties()

    def run_simulation(self, demand_array):
        self._fluid_properties()
        self._simulation_settings()
        self._pipe_position()
        self._initialize_bore_field_and_pipes()
        self._calculate_g_function()
        self._load(demand_array)
        self._simulation()
        self._effective_borehole_thermal_resistance()
        #with st.expander("Borehull"):
        #    self._visualize_pipes()
        #with st.expander("Varmeuttak"):
        #    self._plot_hourly_extraction_rate()
        self._plot_hourly_temperatures()
        #self._plot_fluid_temperature_profiles()
        st.write(self.R_B)

    def _properties(self):
        self.YEARS = 25
        self.U_PIPE = "Single"  # Choose between "Single" and "Double"
        self.R_B = 0.0575  # Radius (m)
        self.R_OUT = 0.020  # Pipe outer radius (m)
        self.R_IN = 0.0176  # Pipe inner radius (m)
        self.D_S = 0.067/2  # Shank spacing (m)
        self.EPSILON = 1.0e-6  # Pipe roughness (m)
        self.ALPHA = 1.39e-6  # Ground thermal diffusivity (m2/s)
        self.K_S = 4.0  # Ground thermal conductivity (W/m.K)            
        self.T_G = 8.5  # Undisturbed ground temperature (degrees)   
        self.K_G = 2  # Grout thermal conductivity (W/m.K)
        self.K_P = 0.42  # Pipe thermal conductivity (W/m.K)
        self.H = 300  # Borehole depth (m)
        self.B = 15  # Distance between boreholes (m)
        self.D = 0  # Borehole buried depth
        self.FLOW_RATE = 0.5  # Flow rate (kg/s)
        self.FLUID_NAME = "MPG"  # The fluid is propylene-glycol 
        self.FLUID_DEGREES = 5  # at 20 degC
        self.BOUNDARY_CONDITION = 'MIFT'

    def _borehole_field_shape(self, N_b_estimated):
        N_1 = st.number_input("Antall brønner (X)", value = N_b_estimated, step = 1)
        N_2 = st.number_input("Antall brønner (Y)", value = 1, step = 1)
        N_b = N_1 * N_2
        return N_1, N_2, N_b

    def select_borehole_field(self, N_b_estimated):
        B, H, D, R_B = self.B, self.H, self.D, self.R_B
        selected_field = st.selectbox("Konfigurasjon", options = ["Rektangulær", "Boks", "U", "L", "Sirkulær", "Fra fil"])
        if selected_field == "Rektangulær":
            N_1, N_2, N_B = self._borehole_field_shape(N_b_estimated) 
            FIELD = gt.boreholes.rectangle_field(N_1, N_2, B, B, H, D, R_B)
        if selected_field == "Boks": 
            N_1, N_2, N_B = self._borehole_field_shape(N_b_estimated) 
            FIELD = gt.boreholes.box_shaped_field(N_1, N_2, B, B, H, D, R_B)
        if selected_field == "U":
            N_1, N_2, N_B = self._borehole_field_shape(N_b_estimated) 
            FIELD = gt.boreholes.U_shaped_field(N_1, N_2, B, B, H, D, R_B)
        if selected_field == "L":
            N_1, N_2, N_B = self._borehole_field_shape(N_b_estimated) 
            FIELD = gt.boreholes.L_shaped_field(N_1, N_2, B, B, H, D, R_B)
        if selected_field == "Sirkulær":
            N_B = st.number_input("Antall borehull", value = 10, step = 1)
            FIELD = gt.boreholes.circle_field(N_B, B, H, D, R_B)
        st.pyplot(gt.boreholes.visualize_field(FIELD))
        self.FIELD = FIELD
        self.N_B = N_B

    def _fluid_properties(self):
        self.M_FLOW_BOREHOLE = self.FLOW_RATE  # Total fluid mass flow rate per borehole (kg/s)
        self.M_FLOW_NETWORK = self.M_FLOW_BOREHOLE * self.N_B  # Total fluid mass flow rate (kg/s)
        fluid = gt.media.Fluid(self.FLUID_NAME, self.FLUID_DEGREES)
        #self.CP_F = fluid.cp  # Fluid specific isobaric heat capacity (J/kg.K)
        #self.RHO_F = fluid.rho  # Fluid density (kg/m3)
        #self.MU_F = fluid.mu  # Fluid dynamic viscosity (kg/m.s)
        #self.K_F = fluid.k  # Fluid thermal conductivity (W/m.K)

        self.CP_F = 4297.6001  # Fluid specific isobaric heat capacity (J/kg.K)
        self.RHO_F = 970.500  # Fluid density (kg/m3)
        self.MU_F = 0.004490  # Fluid dynamic viscosity (kg/m.s)
        self.K_F = 0.4320  # Fluid thermal conductivity (W/m.K)

    def _simulation_settings(self):
        self.DT = 3600.  # Time step (s)
        self.T_MAX = self.YEARS * 8760. * 3600.  # Maximum time (s)
        self.nt = int(np.ceil(self.T_MAX/self.DT))  # Number of time steps
        self.time = self.DT * np.arange(1, self.nt+1)
        self.load_agg = gt.load_aggregation.ClaessonJaved(self.DT, self.T_MAX)  # Load aggregation scheme
        self.OPTIONS = {'nSegments': 8, 'disp': True}   # g-Function calculation options

    def _pipe_position(self):
        if self.U_PIPE == "Single":
            self.POS = [(-self.D_S, 0.), (self.D_S, 0.)]
        elif self.U_PIPE == "Double":
            self.POS = [(-self.D_S, 0.), (0., -self.D_S), (self.D_S, 0.), (0., self.D_S)]

    def _initialize_bore_field_and_pipes(self):
        self.R_P = gt.pipes.conduction_thermal_resistance_circular_pipe(self.R_IN, self.R_OUT, self.K_P)  # Pipe thermal resistance
        H_F = gt.pipes.convective_heat_transfer_coefficient_circular_pipe(self.M_FLOW_BOREHOLE/2, self.R_IN, self.MU_F, self.RHO_F, self.K_F, self.CP_F, self.EPSILON)  # Fluid to inner pipe wall thermal resistance 
        self.R_F = 1.0/(H_F*2*pi*self.R_IN)  # Fluid to inner pipe wall thermal resistance 
        # Same for all boreholes in the bore field
        u_tubes = []
        for borehole in self.FIELD:
            if self.U_PIPE == "Single":
                u_tube = gt.pipes.SingleUTube(self.POS, self.R_IN, self.R_OUT, borehole, self.K_S, self.K_G, self.R_F + self.R_P)
            elif self.U_PIPE == "Double":
                u_tube = gt.pipes.MultipleUTube(self.POS, self.R_IN, self.R_OUT, borehole, self.K_S, self.K_G, self.R_F + self.R_P, nPipes=2, config='parallel')
            u_tubes.append(u_tube)
        self.network = gt.networks.Network(self.FIELD, u_tubes, m_flow_network=self.M_FLOW_NETWORK, cp_f=self.CP_F)  # Build a network object from the list of UTubes
        self.u_tubes = u_tubes

    def _calculate_g_function(self):
        time_req = self.load_agg.get_times_for_simulation()  # Get time values needed for g-function evaluation
        gFunc = gt.gfunction.gFunction(self.network, self.ALPHA, time=time_req, boundary_condition=self.BOUNDARY_CONDITION, options=self.OPTIONS)  # Calculate g-function
        self.load_agg.initialize(gFunc.gFunc/(2*pi*self.K_S))  # Initialize load aggregation scheme

    def _load(self, demand_array):
        stacked_arr = []
        arr = demand_array * 1000
        for i in range(0, self.YEARS):    
            stacked_arr.append(arr)
        stacked_arr = np.array(stacked_arr)
        load_arr = np.vstack([stacked_arr]).flatten()
        load_arr[0:730] = 0
        self.load_arr = load_arr
    
    def _load_from_file(self):
        file_path = "src/data/input/to_simulation.csv"
        stacked_arr = []
        arr = pd.read_csv(file_path, header=None).to_numpy()
        for i in range(0, self.YEARS):    
            stacked_arr.append(arr)
        stacked_arr = np.array(stacked_arr)
        load_arr = np.vstack([stacked_arr]).flatten()
        load_arr[0:730] = 0
        self.load_arr = load_arr
        #np.savetxt('data1.csv', arr, delimiter=',')

    def _simulation(self):
        q_tot = self.load_arr  # Evaluate heat extraction rate
        t_b, tf_in, tf_out = np.zeros(self.nt), np.zeros(self.nt), np.zeros(self.nt)  # Initialize empty arrays
        for i, (t, q_i) in enumerate(zip(self.time, q_tot)):
            self.load_agg.next_time_step(t)  # Increment time step by (1)
            q_b = q_i/self.N_B  # Apply current load (in watts per meter of borehole)
            self.load_agg.set_current_load(q_b/self.H)  # Apply current load (in watts per meter of borehole)
            t_b[i] = self.T_G - self.load_agg.temporal_superposition()  # Evaluate borehole wall temperature
            tf_in[i] = self.network.get_network_inlet_temperature(q_tot[i], t_b[i], self.M_FLOW_NETWORK, self.CP_F, nSegments=1)  # Evaluate inlet fluid temperature (all boreholes are the same)
            tf_out[i] = self.network.get_network_outlet_temperature(tf_in[i], t_b[i], self.M_FLOW_NETWORK, self.CP_F, nSegments=1)  # Evaluate outlet fluid temperature
        
        self.tf_mean = (tf_in + tf_out)/2
        self.q_tot, self.t_b, self.tf_in, self.tf_out = q_tot, t_b, tf_in, tf_out

    def _effective_borehole_thermal_resistance(self):
        self.R_B = self.u_tubes[0].effective_borehole_thermal_resistance(self.M_FLOW_BOREHOLE, self.CP_F)

    def _visualize_pipes(self):
         fig_single = self.u_tubes[0].visualize_pipes()
         st.pyplot(fig_single)

    def _plot_hourly_extraction_rate(self):
        hours = np.arange(1, self.nt+1) * self.DT / 3600.
        Plotting().xy_plot(hours, 0, max(hours), "Timer", self.q_tot, min(self.q_tot), max(self.q_tot), "Varmeuttak [W]", Plotting().FOREST_GREEN)

    def _plot_hourly_temperatures(self):
        hours = np.arange(1, self.nt+1) * self.DT / 3600.
        x_label, y_label = "Timer", "Temperatur [℃]"
        y_min, y_max = -2, 10
        #Plotting().xy_plot(hours, 0, max(hours), x_label, self.tf_mean, y_min, y_max, f"Gjennomsnittlig kollektorvæsketemperatur [°C]", Plotting().FOREST_GREEN)
        Plotting().xy_simulation_pygf_plot(hours, self.tf_in, Plotting().FOREST_GREEN)
        st.write(f"Laveste gj.snittlige kollektorvæsketemperatur: **{round(min(self.tf_mean),1)} °C**")
        st.write(f" - Laveste kollektorvæsketemperatur inn til varmepumpe: {round(min(self.tf_out),1)} °C")        
        st.write(f" - Laveste kollektorvæsketemperatur ut fra varmepumpe: {round(min(self.tf_in),1)} °C")
        #np.savetxt('src/data/output/data_mean.csv', self.tf_mean, delimiter=',')
        #np.savetxt('src/data/output/data_in.csv', self.tf_in, delimiter=',')
        #np.savetxt('src/data/output/data_out.csv', self.tf_out, delimiter=',')

    def _plot_fluid_temperature_profiles(self):
        NZ = 20
        IT = 0
        z = np.linspace(0., self.H, num=NZ)
        tf = self.u_tubes[0].get_temperature(z, self.tf_in[IT], self.t_b[IT], self.M_FLOW_BOREHOLE, self.CP_F)  # Evaluate temperatures at nz evenly spaced depths along the borehole at the (it+1)-th time step
        fig = gt.utilities._initialize_figure()  # Configure figure and axes
        ax = fig.add_subplot(111)
        ax.set_xlabel(r'Temperature [degC]')  # Axis labels
        ax.set_ylabel(r'Depth from borehole head [m]')  # Axis labels
        gt.utilities._format_axes(ax)
        plt_fluid = ax.plot(tf, z, 'b-', label='Fluid')  # Plot temperatures
        plt_wall = ax.plot(np.array([self.t_b[IT], self.t_b[IT]]), np.array([0., self.H]), 'k--', label='Borehole wall')
        ax.legend(handles=[plt_fluid[0]] + plt_wall)
        ax.set_ylim(ax.get_ylim()[::-1])  # Reverse y-axes
        plt.tight_layout()  # Adjust to plot window
        st.pyplot(fig)

import numpy as np
import streamlit as st
import scipy
import copy

def peakshaving(energy_arr, REDUCTION, TO_TEMP, FROM_TEMP):
    energy_arr = copy.deepcopy(energy_arr)
    RHO, HEAT_CAPACITY = 0.96, 4.2
    NEW_MAX_EFFECT = max(energy_arr) - REDUCTION
    
    #Finne topper
    peakshaving_arr = energy_arr
    max_effect_arr = np.zeros(len(energy_arr))
    for i in range(0, len(energy_arr)):
        effect = energy_arr[i]
        if effect > NEW_MAX_EFFECT:
            max_effect_arr[i] = effect - NEW_MAX_EFFECT
    
    #Lade tanken før topper, og ta bort topper
    day = 12
    peakshave_accumulated = 0
    peakshave_arr = []
    for i in range(0, len(energy_arr)-day):
        peakshave = max_effect_arr[i+day]
        peakshave_accumulated += peakshave
        if peakshave > 0:
            peakshaving_arr[i+day] -= peakshave
            peakshaving_arr[i] += peakshave/6
            peakshaving_arr[i+1] += peakshave/6
            peakshaving_arr[i+2] += peakshave/6
            peakshaving_arr[i+3] += peakshave/6
            peakshaving_arr[i+4] += peakshave/6
            peakshaving_arr[i+5] += peakshave/6
        else:
            peakshave_arr.append(peakshave_accumulated)
            peakshave_accumulated = 0

    #Maksimum akkumulert
    max_accumulated_energy = int(round(max(peakshave_arr),0))
    st.write(f"Maksimum akkumulert energi i en periode: {max_accumulated_energy} kWh")
    #Totalenergi
    tank_size = round(max_accumulated_energy*3600/(RHO*HEAT_CAPACITY*(TO_TEMP-FROM_TEMP))/1000,1)
    st.write(f"Tankstørrelse {tank_size} m3")
    diameter_list = [0.5, 1, 1.5, 2, 2.5, 3]
    for i in range(0, len(diameter_list)):
        diameter = diameter_list[i]
        height = round(4*tank_size/(scipy.pi*diameter**2),1)
        st.caption(f"{i}) Diameter: {diameter} m | Høyde: {height} m")
    return peakshaving_arr, max(peakshaving_arr)
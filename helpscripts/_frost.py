import streamlit as st
import requests
import pandas as pd
from shapely import Point
import numpy as np

class Frost:
    client_id = "248d45de-6fc1-4e3b-a4b0-e2932420605e"
    def __init__(self):
        self.lat = float
        self.long = float
        self.number_of_stations = 10

    def find_weather_station(self, selected_station = 0):
        endpoint = f"https://frost.met.no/sources/v0.jsonld?geometry=nearest(POINT({self.long}%20{self.lat}))"
        parameters = {
            "types" : "SensorSystem",
            "elements" : "air_temperature",
            "validtime" : "2019-01-01/2023-01-01",
            "nearestmaxcount" : self.number_of_stations
        }
        r = requests.get(endpoint, parameters, auth=(self.client_id,""))
        json = r.json()
        self.weather_station_name = json["data"][selected_station]["shortName"]
        self.weather_station_id = json["data"][selected_station]["id"]
        self.weather_station_lat = json["data"][selected_station]["geometry"]["coordinates"][1]
        self.weather_station_long = json["data"][selected_station]["geometry"]["coordinates"][0]
        
    def get_climate_normals(self):
        endpoint = f"https://frost.met.no/climatenormals/v0.jsonld?sources={self.weather_station_id}"
        r = requests.get(endpoint, auth=(self.client_id,""))
        json = r.json() 
        st.write(json)    

    def get_time_series(self, time_interval = "2022-01-01/2023-01-01"):
        endpoint = f"https://frost.met.no/observations/v0.jsonld?"
        parameters = {
            'sources' : self.weather_station_id,
            'referencetime' : time_interval,
            'elements' : 'air_temperature',
            'timeoffsets': 'PT0H',
            'timeresolutions' : 'PT1H'
            }
        r = requests.get(endpoint, parameters, auth=(self.client_id,""))
        if r.status_code != 200:
            return False
        json = r.json() 
        air_temperature = np.zeros(8760)
        for index, value in enumerate(json["data"]):
            if index == 8760: 
                break
            timestamp = value['referenceTime']
            if (timestamp[11] +timestamp[12] + ':00') == (timestamp[11] + timestamp[12] + timestamp[13] + timestamp[14] + timestamp[15]):
                air_temperature [index] = (value['observations'][0]['value'])     
            self.air_temperature_h = np.array(air_temperature)
        return True
            
    def get_temperatures(self):
        for selected_weather_station in range(0, self.number_of_stations):
            self.find_weather_station(selected_station=selected_weather_station)
            if (self.get_time_series(time_interval= "2019-01-01/2020-01-01") == True and
                self.get_time_series(time_interval= "2020-01-01/2021-01-01") == True and
                self.get_time_series(time_interval= "2021-01-01/2022-01-01") == True and
                self.get_time_series(time_interval= "2022-01-01/2023-01-01") == True):
                self.get_time_series(time_interval= "2020-01-01/2021-01-01")                
                self.series_2019_2020 = self.air_temperature_h
                self.get_time_series(time_interval= "2020-01-01/2021-01-01")
                self.series_2020_2021 = self.air_temperature_h
                self.get_time_series(time_interval= "2021-01-01/2022-01-01")
                self.series_2021_2022 = self.air_temperature_h
                self.get_time_series(time_interval= "2022-01-01/2023-01-01")
                self.series_2022_2023 = self.air_temperature_h
                self.median_series = np.array(list(map(np.median, zip(self.series_2019_2020, self.series_2020_2021, self.series_2021_2022, self.series_2022_2023))))
                self.chart_data = pd.DataFrame({
                    "2019-2020" : self.series_2019_2020,
                    "2020-2021" : self.series_2020_2021,
                    "2021-2022" : self.series_2021_2022,
                    "2022-2023" : self.series_2022_2023,
                    "Median" : self.median_series,
                })
                break
        
    def get_temperature_extremes(self):
        self.median_temperature = np.median(np.stack([self.series_2019_2020, self.series_2020_2021, self.series_2021_2022, self.series_2022_2023], axis=0))
        self.average_temperature = np.mean(np.stack([self.series_2019_2020, self.series_2020_2021, self.series_2021_2022, self.series_2022_2023], axis=0))
        self.max_temperature = np.max(np.stack([self.series_2019_2020, self.series_2020_2021, self.series_2021_2022, self.series_2022_2023], axis=0))
        self.min_temperature = np.min(np.stack([self.series_2019_2020, self.series_2020_2021, self.series_2021_2022, self.series_2022_2023], axis=0))
          
    def show_computed_temperatures(self):
        c1, c2 = st.columns(2)
        with c1:
            st.write(f""" - • Mediantemperatur: {round(self.median_temperature,2)} °C""")
            st.write(f""" - • Gjennomsnittstemperatur: {round(self.average_temperature,2)} °C""")
        with c2:
            st.write(f""" - • Minimumstemperatur: {round(self.min_temperature,2)} °C""")
            st.write(f""" - • Maksimumstemperatur: {round(self.max_temperature,2)} °C""")
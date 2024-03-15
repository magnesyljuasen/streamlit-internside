# -*- coding: utf-8 -*-
from pandas import DataFrame, to_datetime, pivot
from plotly import graph_objects as go
from plotly.subplots import make_subplots
from requests_oauthlib import OAuth2Session
from oauthlib.oauth2 import BackendApplicationClient
from requests import get
import pathlib
from math import sqrt, cos, radians
from copy import deepcopy
import time
import datetime
import numpy as np
import pandas as pd


# ---------------------------------------------------------------------------------------------------------------#
# -- Utslippsanalyse
class Utslippsanalyse:
    def __init__(self, el_start_timeserie, el_rest_timeserie, co2faktor=116.9):
        co2faktor = co2faktor / 1000
        self.el_start_timeserie = el_start_timeserie
        self.el_rest_timeserie = el_rest_timeserie
        self.co2_start_timeserie = self.el_start_timeserie * co2faktor
        self.co2_rest_timeserie = self.el_rest_timeserie * co2faktor
        self.co2_besparelse_timeserie = (
            self.co2_start_timeserie - self.co2_rest_timeserie
        )
        # --
        self.co2_start = int(round(np.sum(self.co2_start_timeserie), -2))
        self.co2_rest = int(round(np.sum(self.co2_rest_timeserie), -2))
        self.co2_besparelse = int(round(np.sum(self.co2_besparelse_timeserie), -2))


# ---------------------------------------------------------------------------------------------------------------#
# -- Kostnadsanalyse
class Kostnadsanalyse:
    def __init__(
        self,
        el_start_timeserie,
        el_rest_timeserie,
        el_region="NO1",
        el_year=2022,
        el_flat_pris=None,
    ):
        self.el_start_timeserie = el_start_timeserie
        self.el_rest_timeserie = el_rest_timeserie
        self.region = el_region
        self.year = el_year
        if el_flat_pris is not None:
            elpris = np.full(8760, el_flat_pris)
            self.kostnad_start_timeserie = self.el_start_timeserie * elpris
            self.kostnad_rest_timeserie = self.el_rest_timeserie * elpris
            self.kostnad_besparelse_timeserie = (
                self.kostnad_start_timeserie - self.kostnad_rest_timeserie
            )
        else:
            self.kostnad_start_timeserie = self._beregn_kostnad(self.el_start_timeserie)
            self.kostnad_rest_timeserie = self._beregn_kostnad(self.el_rest_timeserie)
            self.kostnad_besparelse_timeserie = (
                self.kostnad_start_timeserie - self.kostnad_rest_timeserie
            )
        # --
        self.kostnad_start = int(round(np.sum(self.kostnad_start_timeserie), -2))
        self.kostnad_rest = int(round(np.sum(self.kostnad_rest_timeserie), -2))
        self.kostnad_besparelse = int(
            round(np.sum(self.kostnad_besparelse_timeserie), -2)
        )

    def _beregn_kostnad(self, el_timeserie):
        elspot_arr = el_timeserie * self._hent_spotpris()  # kr
        kapasitestledd_arr, energiledd_arr = self._beregn_nettleie(el_timeserie)
        kapasitetsledd_arr = month_to_hour(kapasitestledd_arr)  # kr
        fast_gebyr_arr = np.full(8760, 49 / 8760)  # kr
        pslag_arr = el_timeserie * (1 / 100)  # kr
        forbruksavgift_arr = el_timeserie * (15.41 / 100)  # kr
        enova_avgift_arr = el_timeserie * (1 / 100)  # kr
        return (
            fast_gebyr_arr
            + elspot_arr
            + pslag_arr
            + forbruksavgift_arr
            + enova_avgift_arr
            + kapasitetsledd_arr
            + energiledd_arr
        )

    def _hent_spotpris(self):
        df = pd.read_excel(
            "src/csv/spotpriser_energianalyse.xlsx", sheet_name=str(self.year)
        )
        return df[self.region].to_numpy() / 1.25

    def _beregn_nettleie(self, el_timeserie):
        max_value = 0
        max_value_list = []
        day = 0
        kapasitetsledd_mapping = {
            1: 130,
            2: 190,
            3: 280,
            4: 375,
            5: 470,
            6: 565,
            7: 1250,
            8: 1720,
            9: 2190,
            10: 4180,
        }
        energiledd_day = 35.20 / 100  # kr/kWh
        energliedd_night = 28.95 / 100  # kr/kWh
        state = "night"
        energiledd_arr = []
        for i, new_max_value in enumerate(el_timeserie):
            # finne state
            if (i % 6) == 0:
                state = "day"
            if (i % 22) == 0:
                state = "night"
            # energiledd
            if state == "night":
                energiledd_arr.append(new_max_value * energliedd_night)
            elif state == "helg":
                energiledd_arr.append(new_max_value * energliedd_night)
            elif state == "day":
                energiledd_arr.append(new_max_value * energiledd_day)
            # kapasitetsledd
            if new_max_value > max_value:
                max_value = new_max_value
            if i % 24 == 0:
                # energliedd
                day_type = self._ukedag_eller_helligdag(day)
                if day_type == "helg":
                    state = "night"
                if day_type == "ukedag":
                    state = "day"
                # kapasitetsledd
                max_value_list.append(max_value)
                max_value = 0
                day = day + 1
                if day == 31:
                    max_jan = float(
                        round(np.mean(np.sort(max_value_list)[::-1][:3]), 2)
                    )
                    max_value_list = []
                if day == 31 + 28:
                    max_feb = float(
                        round(np.mean(np.sort(max_value_list)[::-1][:3]), 2)
                    )
                    max_value_list = []
                if day == 31 + 28 + 31:
                    max_mar = float(
                        round(np.mean(np.sort(max_value_list)[::-1][:3]), 2)
                    )
                    max_value_list = []
                if day == 31 + 28 + 31 + 30:
                    max_apr = float(
                        round(np.mean(np.sort(max_value_list)[::-1][:3]), 2)
                    )
                    max_value_list = []
                if day == 31 + 28 + 31 + 30 + 31:
                    max_may = float(
                        round(np.mean(np.sort(max_value_list)[::-1][:3]), 2)
                    )
                    max_value_list = []
                if day == 31 + 28 + 31 + 30 + 31 + 30:
                    max_jun = float(
                        round(np.mean(np.sort(max_value_list)[::-1][:3]), 2)
                    )
                    max_value_list = []
                if day == 31 + 28 + 31 + 30 + 31 + 30 + 31:
                    max_jul = float(
                        round(np.mean(np.sort(max_value_list)[::-1][:3]), 2)
                    )
                    max_value_list = []
                if day == 31 + 28 + 31 + 30 + 31 + 30 + 31 + 31:
                    max_aug = float(
                        round(np.mean(np.sort(max_value_list)[::-1][:3]), 2)
                    )
                    max_value_list = []
                if day == 31 + 28 + 31 + 30 + 31 + 30 + 31 + 31 + 30:
                    max_sep = float(
                        round(np.mean(np.sort(max_value_list)[::-1][:3]), 2)
                    )
                    max_value_list = []
                if day == 31 + 28 + 31 + 30 + 31 + 30 + 31 + 31 + 30 + 31:
                    max_oct = float(
                        round(np.mean(np.sort(max_value_list)[::-1][:3]), 2)
                    )
                    max_value_list = []
                if day == 31 + 28 + 31 + 30 + 31 + 30 + 31 + 31 + 30 + 31 + 30:
                    max_nov = float(
                        round(np.mean(np.sort(max_value_list)[::-1][:3]), 2)
                    )
                    max_value_list = []
                if day == 31 + 28 + 31 + 30 + 31 + 30 + 31 + 31 + 30 + 31 + 30 + 31:
                    max_dec = float(
                        round(np.mean(np.sort(max_value_list)[::-1][:3]), 2)
                    )
                    max_value_list = []
        max_array = [
            max_jan,
            max_feb,
            max_mar,
            max_apr,
            max_may,
            max_jun,
            max_jul,
            max_aug,
            max_sep,
            max_oct,
            max_nov,
            max_dec,
        ]
        kapasitestledd_arr = []
        for i, mnd_max in enumerate(max_array):
            if mnd_max < 2:
                kapasitestledd_arr.append(kapasitetsledd_mapping[1])
            if mnd_max > 2 and mnd_max < 5:
                kapasitestledd_arr.append(kapasitetsledd_mapping[2])
            if mnd_max > 5 and mnd_max < 10:
                kapasitestledd_arr.append(kapasitetsledd_mapping[3])
            if mnd_max > 10 and mnd_max < 15:
                kapasitestledd_arr.append(kapasitetsledd_mapping[4])
            if mnd_max > 15 and mnd_max < 20:
                kapasitestledd_arr.append(kapasitetsledd_mapping[5])
            if mnd_max > 20 and mnd_max < 25:
                kapasitestledd_arr.append(kapasitetsledd_mapping[6])
            if mnd_max > 25 and mnd_max < 50:
                kapasitestledd_arr.append(kapasitetsledd_mapping[7])
            if mnd_max > 50 and mnd_max < 75:
                kapasitestledd_arr.append(kapasitetsledd_mapping[8])
            if mnd_max > 75 and mnd_max < 100:
                kapasitestledd_arr.append(kapasitetsledd_mapping[9])
            if mnd_max > 100:
                kapasitestledd_arr.append(kapasitetsledd_mapping[10])
        return kapasitestledd_arr, energiledd_arr

    def _ukedag_eller_helligdag(self, dag_nummer):
        # Convert day number to a date object
        year = datetime.datetime.now().year  # Get the current year
        dato = datetime.datetime(year, 1, 1) + datetime.timedelta(dag_nummer - 1)

        # Check if the date is a weekend (Saturday or Sunday)
        if dato.weekday() >= 5:
            return "helg"

        # Check if the date is a holiday in the Norwegian calendar
        norske_helligdager = [
            (1, 1),  # New Year's Day
            (5, 1),  # Labor Day
            (5, 17),  # Constitution Day
            (12, 25),  # Christmas Day
            (12, 26),  # Boxing Day
        ]

        if (dato.month, dato.day) in norske_helligdager:
            return "helg"

        # If neither weekend nor holiday, consider it a regular weekday
        return "ukedag"


# ---------------------------------------------------------------------------------------------------------------#
# -- Temperaturdata fra FROST API
class Frost:
    client_id = "248d45de-6fc1-4e3b-a4b0-e2932420605e"

    def __init__(self, lat, lon):
        self.lat = lat
        self.long = lon
        self.number_of_stations = 10

    def find_weather_station(self, selected_station=0):
        endpoint = f"https://frost.met.no/sources/v0.jsonld?geometry=nearest(POINT({self.long}%20{self.lat}))"
        parameters = {
            "types": "SensorSystem",
            "elements": "air_temperature",
            "validtime": "2019-01-01/2023-01-01",
            "nearestmaxcount": self.number_of_stations,
        }
        r = get(endpoint, parameters, auth=(self.client_id, ""))
        json = r.json()
        self.weather_station_name = json["data"][selected_station]["shortName"]
        self.weather_station_id = json["data"][selected_station]["id"]
        self.weather_station_lat = json["data"][selected_station]["geometry"][
            "coordinates"
        ][1]
        self.weather_station_long = json["data"][selected_station]["geometry"][
            "coordinates"
        ][0]

    def get_climate_normals(self):
        endpoint = f"https://frost.met.no/climatenormals/v0.jsonld?sources={self.weather_station_id}"
        r = get(endpoint, auth=(self.client_id, ""))
        json = r.json()

    def get_time_series(self, time_interval="2022-01-01/2023-01-01"):
        endpoint = f"https://frost.met.no/observations/v0.jsonld?"
        parameters = {
            "sources": self.weather_station_id,
            "referencetime": time_interval,
            "elements": "air_temperature",
            "timeoffsets": "PT0H",
            "timeresolutions": "PT1H",
        }
        r = get(endpoint, parameters, auth=(self.client_id, ""))
        if r.status_code != 200:
            return False
        json = r.json()
        air_temperature = np.zeros(8760)
        for index, value in enumerate(json["data"]):
            if index == 8760:
                break
            timestamp = value["referenceTime"]
            if (timestamp[11] + timestamp[12] + ":00") == (
                timestamp[11]
                + timestamp[12]
                + timestamp[13]
                + timestamp[14]
                + timestamp[15]
            ):
                air_temperature[index] = value["observations"][0]["value"]
            self.air_temperature_h = np.array(air_temperature)
        return True

    def get_temperatures(self):
        for selected_weather_station in range(0, self.number_of_stations):
            self.find_weather_station(selected_station=selected_weather_station)
            if (
                self.get_time_series(time_interval="2019-01-01/2020-01-01") == True
                and self.get_time_series(time_interval="2020-01-01/2021-01-01") == True
                and self.get_time_series(time_interval="2021-01-01/2022-01-01") == True
                and self.get_time_series(time_interval="2022-01-01/2023-01-01") == True
            ):
                self.get_time_series(time_interval="2020-01-01/2021-01-01")
                self.series_2019_2020 = self.air_temperature_h
                self.get_time_series(time_interval="2020-01-01/2021-01-01")
                self.series_2020_2021 = self.air_temperature_h
                self.get_time_series(time_interval="2021-01-01/2022-01-01")
                self.series_2021_2022 = self.air_temperature_h
                self.get_time_series(time_interval="2022-01-01/2023-01-01")
                self.series_2022_2023 = self.air_temperature_h
                self.median_series = np.array(
                    list(
                        map(
                            np.median,
                            zip(
                                self.series_2019_2020,
                                self.series_2020_2021,
                                self.series_2021_2022,
                                self.series_2022_2023,
                            ),
                        )
                    )
                )
                self.chart_data = DataFrame(
                    {
                        "2019-2020": self.series_2019_2020,
                        "2020-2021": self.series_2020_2021,
                        "2021-2022": self.series_2021_2022,
                        "2022-2023": self.series_2022_2023,
                        "Median": self.median_series,
                    }
                )
                break

    def get_temperature_extremes(self):
        self.median_temperature = np.median(
            np.stack(
                [
                    self.series_2019_2020,
                    self.series_2020_2021,
                    self.series_2021_2022,
                    self.series_2022_2023,
                ],
                axis=0,
            )
        )
        self.average_temperature = np.mean(
            np.stack(
                [
                    self.series_2019_2020,
                    self.series_2020_2021,
                    self.series_2021_2022,
                    self.series_2022_2023,
                ],
                axis=0,
            )
        )
        self.max_temperature = np.max(
            np.stack(
                [
                    self.series_2019_2020,
                    self.series_2020_2021,
                    self.series_2021_2022,
                    self.series_2022_2023,
                ],
                axis=0,
            )
        )
        self.min_temperature = np.min(
            np.stack(
                [
                    self.series_2019_2020,
                    self.series_2020_2021,
                    self.series_2021_2022,
                    self.series_2022_2023,
                ],
                axis=0,
            )
        )


# ---------------------------------------------------------------------------------------------------------------#
class Timeserier:
    def __init__(self):
        self.df = DataFrame()

    def legg_inn_timeserie(self, timeserie, timeserie_navn):
        self.df[timeserie_navn] = timeserie


# ---------------------------------------------------------------------------------------------------------------#
# -- Hjelpefunksjoner PVGIS
class BaseValidationError(ValueError):
    pass


class RoofValueListOrienteringNotEqualLengthError(BaseValidationError):
    pass


class RoofValueListArealerNotEqualLengthError(BaseValidationError):
    pass


class InvalidMountingplaceValueError(BaseValidationError):
    pass


class Roof:
    def __init__(
        self, lat, lon, angle, aspect, footprint_area, loss=14, mountingplace="free"
    ):
        allowed_mountingplace = ["free", "building"]
        # if mountingplace not in allowed_mountingplace:
        # arcpy.AddMessage(f"""Mountingplace value {mountingplace}
        #                 is not valid. Must be equal to
        #                 {allowed_mountingplace[0]}
        #                 or {allowed_mountingplace[1]}""")
        # raise InvalidMountingplaceValueError(mountingplace)
        self.mountingplace = mountingplace
        self.lat = lat
        self.lon = lon
        self.angle = angle
        self.aspect = aspect
        self.kWp_panel = 0.4  # kWp/panel
        self.area_panel = 1.7  # area/panel
        self.area_loss_factor = 0.5  # amout of area not exploitable
        self.footprint_area = footprint_area
        self.surface_area = self._surface_area()
        self.area_exploitable = self.surface_area * self.area_loss_factor
        self.loss = loss
        self.kwp = self._kwp()
        self.main_url = "https://re.jrc.ec.europa.eu/api/v5_2/PVcalc?"
        self.payload = {
            "lat": lat,
            "lon": lon,
            "peakpower": self.kwp,
            "angle": self.angle,
            "aspect": self.aspect,
            "loss": self.loss,
            "mountingplace": self.mountingplace,
            "outputformat": "json",
        }
        self.r = get(url=self.main_url, params=self.payload)
        self.pvgisdata = self.r.json()

    def _pvgisdata(self):
        print(self.main_url)
        r = get(url=self.main_url, params=self.payload)
        return r.json()

    def _surface_area(self):
        angle_r = radians(self.angle)
        b = sqrt(self.footprint_area)
        hypotenus = b / cos(angle_r)
        surface_area = hypotenus * b
        return surface_area

    def _kwp(self):
        """
        se https://www.av-solkalkulator.no/calc
        :return: float, kilowattpeak
        """
        return 1

    def E_y(self):
        """
        Yearly PV energy production [kWh]
        :return: float, kilowatthours per square meter
        """
        # per kilowatt peak
        kWh_m2 = self.pvgisdata()["outputs"]["totals"]["fixed"]["E_y"]
        return kWh_m2

    def E_y_on_surface(self):
        """
        Yearly energy production kWh for exploitable surface area
        :return:
        """
        kWh_total = (
            self.pvgisdata["outputs"]["totals"]["fixed"]["E_y"]
            * self.area_exploitable
            / self.area_panel
            * self.kWp_panel
        )
        return kWh_total

    def Hi_y(self):
        """
        Average annual sum of global irradiation per square meter
        recieved by modules of the given system
        :return: float, kWh/m2/y
        """
        return self.pvgisdata["outputs"]["totals"]["fixed"]["H(i)_y"]

    def Hi_y_on_surface(self):
        """
        H(i)_y average per year for roof surface
        :return:
        """
        return self.pvgisdata["outputs"]["totals"]["fixed"]["H(i)_y"]


class Roof_hourly(Roof):
    """
    get hourly solar energy values from pv-gis for a given year.
    """

    def __init__(
        self,
        lat,
        lon,
        angle,
        aspect,
        footprint_area,
        loss=14,
        mountingplace="free",
        pvcalc=True,
        startyear=2019,
        endyear=2019,
    ):
        super().__init__(lat, lon, angle, aspect, footprint_area, loss, mountingplace)
        if pvcalc:
            pvcalc = 1
        else:
            pvcalc = 0
        self.main_url = "https://re.jrc.ec.europa.eu/api/v5_2/seriescalc?"
        self.startyear = startyear
        self.endyear = endyear
        self.payload = {
            "lat": lat,
            "lon": lon,
            "startyear": self.startyear,
            "endyear": self.endyear,
            "pvcalculation": pvcalc,
            "peakpower": self.kwp,
            "angle": self.angle,
            "aspect": self.aspect,
            "loss": self.loss,
            "mountingplace": self.mountingplace,
            "outputformat": "json",
        }
        self.r = get(self.main_url, params=self.payload)
        if self.r.status_code == 200:
            self.pvgisdata = self.r.json()
            hourly = self.pvgisdata["outputs"]["hourly"]
            self.hourly_df = DataFrame(hourly)
        else:
            raise ValueError("PVGIS error")

    def get_hourly_as_dataframe(self):
        return self.hourly_df

    def get_hourly_pivot(self):
        hourlydf = deepcopy(self.hourly_df)
        hourlydf["datetime"] = to_datetime(hourlydf["time"], format="%Y%m%d:%H%M")
        hourlydf["year"] = hourlydf["datetime"].dt.year
        piv = pivot(data=hourlydf, columns="year", values="P")
        return piv

    def normalize(self, E_y_on_surface):
        normalized = deepcopy(self.hourly_df)
        sum_year = normalized["P"].sum()
        normalized["normal"] = normalized.apply(
            lambda x: (x.P / sum_year), axis="columns"
        )
        normalized["p_normal"] = normalized.apply(
            lambda x: x.normal * E_y_on_surface, axis="columns"
        )
        return normalized

    def get_metadata(self):
        return self.pvgisdata["meta"]


# ---------------------------------------------------------------------------------------------------------------#
# -- Andre hjelpefunksjoner
def month_to_hour(monthly_array):
    hourly_array = np.zeros(8760)
    n, m = 0, 744
    hourly_array[n:m] = monthly_array[0] / (m - n)
    n, m = 744, 1416
    hourly_array[n:m] = monthly_array[0] / (m - n)
    n, m = 1416, 2160
    hourly_array[n:m] = monthly_array[0] / (m - n)
    n, m = 2160, 2880
    hourly_array[n:m] = monthly_array[0] / (m - n)
    n, m = 2880, 3624
    hourly_array[n:m] = monthly_array[0] / (m - n)
    n, m = 3624, 4344
    hourly_array[n:m] = monthly_array[0] / (m - n)
    n, m = 4344, 5088
    hourly_array[n:m] = monthly_array[0] / (m - n)
    n, m = 5088, 5832
    hourly_array[n:m] = monthly_array[0] / (m - n)
    n, m = 5832, 6552
    hourly_array[n:m] = monthly_array[0] / (m - n)
    n, m = 6552, 7296
    hourly_array[n:m] = monthly_array[0] / (m - n)
    n, m = 7296, 8016
    hourly_array[n:m] = monthly_array[0] / (m - n)
    n, m = 8016, 8760
    hourly_array[n:m] = monthly_array[0] / (m - n)
    # --
    return hourly_array


def hour_to_month(hourly_array):
    monthly_array = []
    summed = 0
    for i in range(0, len(hourly_array)):
        verdi = hourly_array[i]
        if np.isnan(verdi):
            verdi = 0
        summed = verdi + summed
        if (
            i == 744
            or i == 1416
            or i == 2160
            or i == 2880
            or i == 3624
            or i == 4344
            or i == 5088
            or i == 5832
            or i == 6552
            or i == 7296
            or i == 8016
            or i == 8759
        ):
            monthly_array.append(int(summed))
            summed = 0
    return monthly_array


def hour_to_month_max(hourly_array):
    monthly_array = []
    maksverdi = 0
    for i in range(0, len(hourly_array)):
        verdi = hourly_array[i]
        if not np.isnan(verdi):
            if maksverdi < verdi:
                maksverdi = verdi
        if (
            i == 744
            or i == 1416
            or i == 2160
            or i == 2880
            or i == 3624
            or i == 4344
            or i == 5088
            or i == 5832
            or i == 6552
            or i == 7296
            or i == 8016
            or i == 8759
        ):
            monthly_array.append(int(maksverdi))
            maksverdi = 0
    return monthly_array


def get_secret(filename):
    with open(filename) as file:
        secret = file.readline()
    return secret


def avrunding(tall):
    return int(round(tall, 2))


def dekningsberegning(DEKNINGSGRAD, timeserie, over_under="over"):
        if DEKNINGSGRAD == 100:
            return timeserie
        timeserie_sortert = np.sort(timeserie)
        timeserie_sum = np.sum(timeserie)
        timeserie_N = len(timeserie)
        startpunkt = timeserie_N // 2
        i = 0
        avvik = 0.0001
        pm = 2 + avvik
        while abs(pm - 1) > avvik:
            cutoff = timeserie_sortert[startpunkt]
            timeserie_tmp = np.where(timeserie > cutoff, cutoff, timeserie)
            beregnet_dekningsgrad = (np.sum(timeserie_tmp) / timeserie_sum) * 100
            pm = beregnet_dekningsgrad / DEKNINGSGRAD
            gammelt_startpunkt = startpunkt
            if pm < 1:
                startpunkt = startpunkt + timeserie_N // 2 ** (i + 2) - 1
            else:
                startpunkt = startpunkt - timeserie_N // 2 ** (i + 2) - 1
            if startpunkt == gammelt_startpunkt:
                break
            i += 1
            if i > 13:
                break
        return timeserie_tmp


# ---------------------------------------------------------------------------------------------------------------#
# -- Plottefunksjoner
def plot_temperatur(
    temperatur,
    objektid,
    filplassering,
    COLOR_1="#1d3c34",
    VARIGHETSKURVE=False,
    plot_navn="temperatur",
):
    if VARIGHETSKURVE == True:
        fig = go.Figure()
        x_arr = np.array(range(0, len(temperatur)))
        y_arr = np.sort(temperatur)[::-1]
        type_plot = "varighetskurve"
        xlabel = "Varighet [timer]"
        fig.update_xaxes(range=[0, 8760])
    else:
        fig = go.Figure()
        y_arr = temperatur
        type_plot = "timeplot"
        xlabel = "Datoer i ett år"
        start = datetime.datetime(2023, 1, 1, 0)  # Start from January 1, 2023, 00:00
        end = datetime.datetime(2023, 12, 31, 23)  # End on December 31, 2023, 23:00
        hours = int((end - start).total_seconds() / 3600) + 1
        x_arr = np.array([start + datetime.timedelta(hours=i) for i in range(hours)])
        fig.update_xaxes(range=[start, end])

    fig.add_trace(
        go.Scatter(
            x=x_arr,
            y=y_arr,
            stackgroup="one",
            fill="tonexty",
            line=dict(width=0, color=COLOR_1),
        )
    )
    fig.update_xaxes(
        # dtick="M1",
        tickformat="%d/%m"
    )
    fig["data"][0]["showlegend"] = True
    fig["data"][0][
        "name"
    ] = f"Gjennomsnittstemperatur: {float(round(np.average(y_arr),1)):,} °C <br>Høyeste temperatur: {float(round(np.max(y_arr),1)):,} °C <br>Laveste temperatur: {float(round(np.min(y_arr),1)):,} °C".replace(
        ",", " "
    )

    fig.update_layout(barmode="stack", margin=dict(l=20, r=20, t=20, b=20),
)
    fig.update_layout(
        legend=dict(
            yanchor="top", y=0.98, xanchor="left", x=0.01, bgcolor="rgba(0,0,0,0)"
        )
    )
    fig.update_layout(xaxis_title=xlabel, yaxis_title="Temperatur [°C]")
    #fig.update_layout(plot_bgcolor="#f0f4e3", paper_bgcolor="#f0f4e3")
    fig.update_xaxes(
        mirror=True,
        ticks="outside",
        showline=True,
        linecolor="black",
        gridcolor="lightgrey",
    )
    fig.update_yaxes(
        mirror=True,
        ticks="outside",
        showline=True,
        linecolor="black",
        gridcolor="lightgrey",
    )
    # fig.write_html(f"{filplassering}/{objektid}_{plot_navn}_{type_plot}.html")
    return fig


def plot_1_timeserie(
    timeserie_1,
    timeserie_1_navn,
    objektid,
    filplassering,
    COLOR_1="#1d3c34",
    VARIGHETSKURVE=False,
    plot_navn="energibehov",
    y_max=10,
    y_min=0,
):
    if VARIGHETSKURVE == True:
        y_arr = np.sort(timeserie_1)[::-1]
        type_plot = "varighetskurve"
        xlabel = "Varighet [timer]"
        x_arr = np.array(range(0, len(timeserie_1)))
        fig = go.Figure()
        fig.add_trace(
            go.Scatter(
                x=x_arr,
                y=y_arr,
                # stackgroup="one",
                line=dict(color=COLOR_1),
            )
        )
        fig.update_xaxes(range=[0, 8760])
        fig["data"][0]["showlegend"] = True
        fig["data"][0][
            "name"
        ] = f"{timeserie_1_navn}:<br>{int(round(np.sum(y_arr),-2)):,} kWh/år | {float(round(np.max(y_arr),1)):,} kW".replace(
            ",", " "
        ).replace(
            ".", ","
        )
    else:
        y_arr = timeserie_1
        type_plot = "timeplot"
        xlabel = "Datoer i ett år"
        start = datetime.datetime(2023, 1, 1, 0)  # Start from January 1, 2023, 00:00
        end = datetime.datetime(2023, 12, 31, 23)  # End on December 31, 2023, 23:00
        hours = int((end - start).total_seconds() / 3600) + 1
        x_arr = np.array([start + datetime.timedelta(hours=i) for i in range(hours)])
        if np.any(y_arr < 0):
            y_arr_negative = y_arr.copy()
            y_arr_positive = y_arr.copy()
            y_arr_negative[y_arr_negative > 0] = 0
            y_arr_positive[y_arr_positive < 0] = 0
            fig = go.Figure()
            fig.add_trace(
                go.Scatter(
                    x=x_arr,
                    y=y_arr_positive,
                    stackgroup="one",
                    name=f"Elektrisk import fra nett:<br>{int(round(np.sum(y_arr_positive),-2)):,} kWh/år | {float(round(np.max(y_arr_positive),1)):,} kW".replace(
                        ",", " "
                    ).replace(
                        ".", ","
                    ),
                    line=dict(width=0, color=COLOR_1),
                )
            )
            fig.add_trace(
                go.Scatter(
                    x=x_arr,
                    y=y_arr_negative,
                    stackgroup="one",
                    name=f"Elektrisk eksport til nett:<br>{-int(round(np.sum(y_arr_negative),-2)):,} kWh/år | {-float(round(np.min(y_arr_negative),1)):,} kW".replace(
                        ",", " "
                    ).replace(
                        ".", ","
                    ),
                    line=dict(width=0, color="black"),
                )
            )
        else:
            fig = go.Figure()
            fig.add_trace(
                go.Scatter(
                    x=x_arr,
                    y=y_arr,
                    stackgroup="one",
                    line=dict(width=0, color=COLOR_1),
                    name=f"{timeserie_1_navn}:<br>{int(round(np.sum(y_arr),-2)):,} kWh/år | {float(round(np.max(y_arr),1)):,} kW".replace(
                        ",", " "
                    ).replace(
                        ".", ","
                    ),
                )
            )
        fig["data"][0]["showlegend"] = True
        fig.update_xaxes(range=[start, end])
        fig.update_xaxes(
            # dtick="M1",
            tickformat="%d/%m"
        )
    #    fig["data"][0]["showlegend"] = True
    #    fig["data"][0][
    #        "name"
    #    ] = f"{timeserie_1_navn}:<br>{int(round(np.sum(y_arr),-2)):,} kWh/år | {float(round(np.max(y_arr),1)):,} kW".replace(
    #        ",", " "
    #    ).replace(
    #        ".", ","
    #    )
    fig.update_yaxes(range=[y_min, y_max])
    fig.update_layout(barmode="stack", margin=dict(l=20, r=20, t=20, b=20))
    fig.update_layout(
        legend=dict(
            yanchor="top",
            y=0.98,
            xanchor="left",
            x=0.01,
            bgcolor="rgba(0,0,0,0)",
        )
    )
    fig.update_layout(xaxis_title=xlabel, yaxis_title="Effekt [kW]")
    #fig.update_layout(plot_bgcolor="#f0f4e3", paper_bgcolor="#f0f4e3")
    date = datetime.datetime.now().strftime("%d.%m.%Y %H:%M")

    fig.update_xaxes(
        mirror=True,
        ticks="outside",
        showline=True,
        linecolor="black",
        gridcolor="lightgrey",
    )
    fig.update_yaxes(
        mirror=True,
        ticks="outside",
        showline=True,
        linecolor="black",
        gridcolor="lightgrey",
    )
    # fig.write_html(f"{filplassering}/{objektid}_{plot_navn}_{type_plot}.html")
    return fig


def plot_2_timeserie(
    timeserie_1,
    timeserie_1_navn,
    timeserie_2,
    timeserie_2_navn,
    objektid = 1,
    filplassering = 1,
    COLOR_1="#1d3c34",
    COLOR_2="#4d4b32",
    VARIGHETSKURVE=False,
    plot_navn="energibehov",
    y_max=10,
    y_min=0,
):
    if VARIGHETSKURVE == True:
        timeserie_sum_arr = timeserie_1 + timeserie_2
        timeserie_sortert = np.argsort(timeserie_sum_arr)[::-1]
        y_arr_1 = timeserie_1[timeserie_sortert]
        y_arr_2 = timeserie_2[timeserie_sortert]
        type_plot = "varighetskurve"
        xlabel = "Varighet [timer]"
    else:
        y_arr_1 = timeserie_1
        y_arr_2 = timeserie_2
        type_plot = "timeplot"
        xlabel = "Datoer i ett år"
    x_arr = np.array(range(0, len(timeserie_1)))
    start = datetime.datetime(2023, 1, 1, 0)  # Start from January 1, 2023, 00:00
    end = datetime.datetime(2023, 12, 31, 23)  # End on December 31, 2023, 23:00
    hours = int((end - start).total_seconds() / 3600) + 1
    x_arr = np.array([start + datetime.timedelta(hours=i) for i in range(hours)])
    fig = go.Figure()
    fig.update_xaxes(
        # dtick="M1",
        tickformat="%d/%m"
    )
    fig.add_trace(
        go.Scatter(
            x=x_arr,
            y=y_arr_1,
            stackgroup="one",
            fill="tonexty",
            line=dict(width=0, color=COLOR_1),
            name=f"{timeserie_1_navn}:<br>{int(round(np.sum(y_arr_1),-2)):,} kWh/år | {float(round(np.max(y_arr_1),1)):,} kW".replace(
                ",", " "
            ).replace(
                ".", ","
            ),
        )
    )
    fig.add_trace(
        go.Scatter(
            x=x_arr,
            y=y_arr_2,
            stackgroup="one",
            fill="tonexty",
            line=dict(width=0, color=COLOR_2),
            name=f"{timeserie_2_navn}:<br>{int(round(np.sum(y_arr_2),-2)):,} kWh/år | {float(round(np.max(y_arr_2),1)):,} kW".replace(
                ",", " "
            ).replace(
                ".", ","
            ),
        )
    )
    fig["data"][0]["showlegend"] = True
    fig.update_xaxes(range=[start, end])
    fig.update_yaxes(range=[y_min, y_max])
    fig.update_layout(barmode="stack", margin=dict(l=20, r=20, t=20, b=20),
)
    fig.update_layout(
        legend=dict(
            yanchor="top", y=0.98, xanchor="left", x=0.01, bgcolor="rgba(0,0,0,0)"
        )
    )
    fig.update_layout(xaxis_title=xlabel, yaxis_title="Effekt [kW]")
    #fig.update_layout(plot_bgcolor="#f0f4e3", paper_bgcolor="#f0f4e3")

    date = datetime.datetime.now().strftime("%d.%m.%Y %H:%M")

    fig.update_xaxes(
        mirror=True,
        ticks="outside",
        showline=True,
        linecolor="black",
        gridcolor="lightgrey",
    )
    fig.update_yaxes(
        mirror=True,
        ticks="outside",
        showline=True,
        linecolor="black",
        gridcolor="lightgrey",
    )
    # fig.write_html(f"{filplassering}/{objektid}_{plot_navn}_{type_plot}.html")
    return fig


def plot_3_timeserie(
    timeserie_1,
    timeserie_1_navn,
    timeserie_2,
    timeserie_2_navn,
    timeserie_3,
    timeserie_3_navn,
    objektid = 1,
    filplassering = 1,
    COLOR_1="#1d3c34",
    COLOR_2="#4d4b32",
    COLOR_3="#4da452",
    VARIGHETSKURVE=False,
    plot_navn="energibehov",
    y_max=10,
    y_min=0,
):
    if VARIGHETSKURVE == True:
        x_arr = np.array(range(0, len(timeserie_1)))
        timeserie_sum_arr = timeserie_1 + timeserie_2 + timeserie_3
        timeserie_sortert_samtidighet = np.sort(timeserie_sum_arr)[::-1]
        # timeserie_sortert = np.argsort(timeserie_sum_arr)[::-1]
        y_arr_1 = np.sort(timeserie_1)[::-1]
        y_arr_2 = np.sort(timeserie_2)[::-1]
        y_arr_3 = np.sort(timeserie_3)[::-1]
        type_plot = "varighetskurve"
        xlabel = "Varighet [timer]"
        x_arr = np.array(range(0, len(timeserie_1)))
        fig = go.Figure()
        # --
        fig.add_trace(
            go.Scatter(
                x=x_arr,
                y=y_arr_1,
                # stackgroup="one",
                # fill="tonexty",
                line=dict(color=COLOR_1),
                name=f"{timeserie_1_navn}:<br>{int(round(np.sum(y_arr_1),-2)):,} kWh/år | {float(round(np.max(y_arr_1),1)):,} kW".replace(
                    ",", " "
                ).replace(
                    ".", ","
                ),
            )
        )
        fig.add_trace(
            go.Scatter(
                x=x_arr,
                y=y_arr_2,
                # stackgroup="one",
                # fill="tonexty",
                line=dict(color=COLOR_2),
                name=f"{timeserie_2_navn}:<br>{int(round(np.sum(y_arr_2),-2)):,} kWh/år | {float(round(np.max(y_arr_2),1)):,} kW".replace(
                    ",", " "
                ).replace(
                    ".", ","
                ),
            )
        )
        fig.add_trace(
            go.Scatter(
                x=x_arr,
                y=y_arr_3,
                # stackgroup="one",
                # fill="tonexty",
                line=dict(color=COLOR_3),
                name=f"{timeserie_3_navn}:<br>{int(round(np.sum(y_arr_3),-2)):,} kWh/år | {float(round(np.max(y_arr_3),1)):,} kW".replace(
                    ",", " "
                ).replace(
                    ".", ","
                ),
            )
        )

        fig.add_trace(
            go.Scatter(
                x=x_arr,
                y=timeserie_sortert_samtidighet,
                mode="lines",
                visible="legendonly",
                # stackgroup="one",
                # fill="tonexty",
                line=dict(width=1, color="#1d3c34", dash="dash"),
                name=f"Sum (elspesifikt + varmtvann + oppvarming):<br>{int(round(np.sum(timeserie_sortert_samtidighet),-2)):,} kWh/år | {float(round(np.max(timeserie_sortert_samtidighet),1)):,} kW".replace(
                    ",", " "
                ).replace(
                    ".", ","
                ),
            )
        )
        fig.update_xaxes(range=[0, 8760])
    else:
        y_arr_1 = timeserie_1
        y_arr_2 = timeserie_2
        y_arr_3 = timeserie_3
        y_total = y_arr_1 + y_arr_2 + y_arr_3
        type_plot = "timeplot"
        xlabel = "Datoer i ett år"
        start = datetime.datetime(2023, 1, 1, 0)  # Start from January 1, 2023, 00:00
        end = datetime.datetime(2023, 12, 31, 23)  # End on December 31, 2023, 23:00
        hours = int((end - start).total_seconds() / 3600) + 1
        x_arr = np.array([start + datetime.timedelta(hours=i) for i in range(hours)])
        fig = go.Figure()
        # --
        fig.update_xaxes(
            # dtick="M1",
            tickformat="%d/%m"
        )
        fig.add_trace(
            go.Scatter(
                x=x_arr,
                y=y_total,
                mode="lines",
                visible="legendonly",
                # stackgroup="one",
                fill="tonexty",
                line=dict(width=0, color="black"),
                name=f"Sum (elspesifikt + varmtvann + oppvarming):<br>{int(round(np.sum(y_total),-2)):,} kWh/år | {float(round(np.max(y_total),1)):,} kW".replace(
                    ",", " "
                ).replace(
                    ".", ","
                ),
            )
        )
        # --
        fig.add_trace(
            go.Scatter(
                x=x_arr,
                y=y_arr_1,
                stackgroup="one",
                fill="tonexty",
                line=dict(width=0, color=COLOR_1),
                name=f"{timeserie_1_navn}:<br>{int(round(np.sum(y_arr_1),-2)):,} kWh/år | {float(round(np.max(y_arr_1),1)):,} kW".replace(
                    ",", " "
                ).replace(
                    ".", ","
                ),
            )
        )
        fig.add_trace(
            go.Scatter(
                x=x_arr,
                y=y_arr_2,
                stackgroup="one",
                fill="tonexty",
                line=dict(width=0, color=COLOR_2),
                name=f"{timeserie_2_navn}:<br>{int(round(np.sum(y_arr_2),-2)):,} kWh/år | {float(round(np.max(y_arr_2),1)):,} kW".replace(
                    ",", " "
                ).replace(
                    ".", ","
                ),
            )
        )
        fig.add_trace(
            go.Scatter(
                x=x_arr,
                y=y_arr_3,
                stackgroup="one",
                fill="tonexty",
                line=dict(width=0, color=COLOR_3),
                name=f"{timeserie_3_navn}:<br>{int(round(np.sum(y_arr_3),-2)):,} kWh/år | {float(round(np.max(y_arr_3),1)):,} kW".replace(
                    ",", " "
                ).replace(
                    ".", ","
                ),
            )
        )
        fig.update_layout(barmode="stack")
    fig["data"][0]["showlegend"] = True
    fig.update_yaxes(range=[y_min, y_max])
    # fig.update_xaxes(range=[start, end])
    fig.update_layout(
        legend=dict(
            yanchor="top", y=0.98, xanchor="left", x=0.01, bgcolor="rgba(0,0,0,0)"
        )
    )
    fig.update_layout(xaxis_title=xlabel, yaxis_title="Effekt [kW]", margin=dict(l=20, r=20, t=20, b=20))
    #fig.update_layout(plot_bgcolor="#f0f4e3", paper_bgcolor="#f0f4e3")

    date = datetime.datetime.now().strftime("%d.%m.%Y %H:%M")

    fig.update_xaxes(
        mirror=True,
        ticks="outside",
        showline=True,
        linecolor="black",
        gridcolor="lightgrey",
    )
    fig.update_yaxes(
        mirror=True,
        ticks="outside",
        showline=True,
        linecolor="black",
        gridcolor="lightgrey",
    )
    # fig.write_html(f"{filplassering}/{objektid}_{plot_navn}_{type_plot}.html")
    return fig


# Ikke riktig - Må endres
def plot_produksjon(
    df,
    objektid,
    filplassering,
    VARIGHETSKURVE=False,
    plot_navn="produksjon",
    y_max=10,
    y_min=0,
):
    y_sum_calc = 0
    y_max_calc = 0
    color_map = {
        "El_spesifiktbehov": "#b7dc8f",
        "R_omoppvarmingsbehov": "#1d3c34",
        "V_armtvannsbehov": "#FFC358",
        "R_fjernvarme": "#1d3c34",
        "V_fjernvarme": "#1d3c34",
        "T_fjernvarme": "#1d3c34",
        "R_grunnvarme": "#b7dc8f",
        "V_grunnvarme": "#b7dc8f",
        "T_grunnvarme": "#b7dc8f",
        "El_grunnvarme_kompressor": "#48a23f",
        "El_kjel": "#664e23",
        "R_luftluft": "#1d3c34",
        "El_luftluft_kompressor": "#48a23f",
        "El_luftluft_spisslast": "#FFC358",
        "El_solenergi": "#FFC358",
    }
    name_map = {
        "El_spesifiktbehov": "Elspesifiktbehov",
        "R_omoppvarmingsbehov": "Romoppvarmingsbehov",
        "V_armtvannsbehov": "Varmtvannsbehov",
        "R_fjernvarme": "Fjernvarmeproduksjon",
        "V_fjernvarme": "Fjernvarmeproduksjon",
        "T_fjernvarme": "Fjernvarmeproduksjon",
        "R_grunnvarme": "Levert fra varmepumpe (brønner + kompressor)",
        "V_grunnvarme": "Levert fra varmepumpe (brønner + kompressor)",
        "T_grunnvarme": "Levert fra varmepumpe (brønner + kompressor)",
        "El_grunnvarme_kompressor": "Kompressorenergi",
        "El_kjel": "Spisslast",
        "R_luftluft": "Levert fra luft",
        "El_luftluft_kompressor": "Levert fra varmepumpe (uteluft + kompressor)",
        "El_luftluft_spisslast": "Spisslast",
        "El_solenergi": "Solproduksjon",
    }
    if VARIGHETSKURVE == True:
        type_plot = "varighetskurve"
        xlabel = "Varighet [timer]"
        x_arr = np.array(range(0, len(df)))
        fig = go.Figure()
        for i in range(0, len(df.columns)):
            y_arr_navn = df.columns[i]
            if (
                y_arr_navn != "El_grunnvarme_kompressor"
                and y_arr_navn != "El_luftluft_kompressor"
            ):
                y_arr = (df.iloc[:, i])[::-1]
                y_arr_sum = np.sum(y_arr)
                if y_arr_sum < 0 and y_arr_navn != "El_solenergi":
                    y_arr = -y_arr
                elif y_arr_navn == "El_solenergi":
                    y_arr = -y_arr
                y_arr = np.sort(y_arr)[::-1]
                y_sum_calc = y_arr_sum + y_sum_calc
                y_max_calc = np.max(y_arr) + y_max_calc
                fig.add_trace(
                    go.Scatter(
                        x=x_arr,
                        y=y_arr,
                        stackgroup="one",
                        fill="tonexty",
                        line=dict(width=0, color=color_map[y_arr_navn]),
                        name=f"{name_map[y_arr_navn]}:<br>{int(round(np.sum(y_arr),-2)):,} kWh/år | {float(round(np.max(y_arr),1)):,} kW".replace(
                            ",", " "
                        ).replace(
                            ".", ","
                        ),
                    )
                )
    else:
        type_plot = "timeplot"
        xlabel = "Datoer i ett år"
        x_arr = np.array(range(0, len(df)))
        start = datetime.datetime(2023, 1, 1, 0)  # Start from January 1, 2023, 00:00
        end = datetime.datetime(2023, 12, 31, 23)  # End on December 31, 2023, 23:00
        hours = int((end - start).total_seconds() / 3600) + 1
        x_arr = np.array([start + datetime.timedelta(hours=i) for i in range(hours)])
        fig = go.Figure()
        fig.update_xaxes(
            # dtick="M1",
            tickformat="%d/%m"
        )
        for i in range(0, len(df.columns)):
            y_arr_navn = df.columns[i]
            if (
                y_arr_navn != "El_grunnvarme_kompressor"
                and y_arr_navn != "El_luftluft_kompressor"
            ):
                y_arr = (df.iloc[:, i])[::-1]
                y_arr_sum = np.sum(y_arr)
                if y_arr_sum < 0 and y_arr_navn != "El_solenergi":
                    y_arr = -y_arr
                elif y_arr_navn == "El_solenergi":
                    y_arr = -y_arr
                y_sum_calc = y_arr_sum + y_sum_calc
                y_max_calc = np.max(y_arr) - y_max_calc
                fig.add_trace(
                    go.Scatter(
                        x=x_arr,
                        y=y_arr,
                        stackgroup="one",
                        fill="tonexty",
                        line=dict(width=0, color=color_map[y_arr_navn]),
                        name=f"{name_map[y_arr_navn]}:<br>{int(round(np.sum(y_arr),-2)):,} kWh/år | {float(round(np.max(y_arr),1)):,} kW".replace(
                            ",", " "
                        ).replace(
                            ".", ","
                        ),
                    )
                )

    if len(df.columns) != 0:
        fig["data"][0]["showlegend"] = True
    fig.update_xaxes(range=[start, end])
    fig.update_yaxes(range=[y_min, y_max])
    fig.update_layout(barmode="stack", margin=dict(l=20, r=20, t=20, b=20),
)
    fig.update_layout(
        legend=dict(
            yanchor="top", y=0.98, xanchor="left", x=0.01, bgcolor="rgba(0,0,0,0)"
        )
    )
    fig.update_layout(xaxis_title=xlabel, yaxis_title="Effekt [kW]")
    #fig.update_layout(plot_bgcolor="#f0f4e3", paper_bgcolor="#f0f4e3")
    date = datetime.datetime.now().strftime("%d.%m.%Y %H:%M")

    fig.update_xaxes(
        mirror=True,
        ticks="outside",
        showline=True,
        linecolor="black",
        gridcolor="lightgrey",
    )
    fig.update_yaxes(
        mirror=True,
        ticks="outside",
        showline=True,
        linecolor="black",
        gridcolor="lightgrey",
    )
    # fig.write_html(f"{filplassering}/{objektid}_{plot_navn}_{type_plot}.html")
    return fig


# ---------------------------------------------------------------------------------------------------------------#
# -- Energibehovklasse som bruker PROFet API
class Energibehov:
    BYGNINGSTYPE = {
        "A": "Hou",
        "B": "Apt",
        "C": "Off",
        "D": "Shp",
        "E": "Htl",
        "F": "Kdg",
        "G": "Sch",
        "H": "Uni",
        "I": "CuS",
        "J": "Nsh",
        "K": "Hospital",
        "L": "Other",
    }
    BYGNINGSSTANDARD = {"X": "Reg", "Y": "Eff-E", "Z": "Vef"}

    def __init__(
        self,
        objektid=1,
        bygningstype="A",
        bygningsstandard="X",
        areal=250,
        temperatur_serie=None,
    ):
        self.MAKS_VARMEEFFEKT_FAKTOR = 1.0  # todo: finner vi pa noe lurt her? kan vi gange makseffekten med en faktor for a fa reell maksimal effekt basert pa utetemperatur feks?
        self.objektid = objektid
        self.bygningstype = bygningstype
        self.bygningsstandard = bygningsstandard
        self.areal = areal
        self.temperatur_serie = temperatur_serie
        # Profet API-et kan ikke kjøres med K
        if self.bygningstype == "K":
            self.bygningstype = "L"

    def _beregn_energibehov(self):
        oauth = OAuth2Session(client=BackendApplicationClient(client_id="profet_2023"))
        predict = OAuth2Session(
            token=oauth.fetch_token(
                token_url="https://identity.byggforsk.no/connect/token",
                client_id="profet_2023",
                client_secret=get_secret("src/csv/secret.txt"),
            )
        )
        valgt_standard = self.BYGNINGSSTANDARD[self.bygningsstandard]
        if valgt_standard == "Reg":
            regular_areal = self.areal
            efficient_areal = 0
            veryefficient_areal = 0
        if valgt_standard == "Eff-E":
            regular_areal = 0
            efficient_areal = self.areal
            veryefficient_areal = 0
        if valgt_standard == "Vef":
            regular_areal = 0
            efficient_areal = 0
            veryefficient_areal = self.areal
        # --
        if self.temperatur_serie is not None:
            request_data = {
                "StartDate": "2022-01-01",  # Initial date (influences weekday/weekend. N.B. In Shops and Culture_Sport, Saturday has a different profile than Sunday)
                "Areas": {  # Spesification of areas for building categories and efficiency levels
                    f"{self.BYGNINGSTYPE[self.bygningstype.upper()]}": {  # building category office, add sections for multiple categories. Available categories are ['Hou', 'Apt', 'Off', 'Shp', 'Htl', 'Kdg', 'Sch', 'Uni', 'CuS', 'Nsh', 'Hos', 'Other']
                        "Reg": regular_areal,  # Category regular. 'Regular' means average standard of buildings in the stock
                        "Eff-E": efficient_areal,  # Category Efficient Existing. 'Efficient' means at about TEK10 standard, representing an ambitious yet realistic target for energy efficient renovation
                        "Eff-N": 0,  # Category Efficient New. 'Efficient' means at about TEK10 standard. Gives same results as Eff-E
                        "Vef": veryefficient_areal,  # Category Very Efficient.'Very efficient' means at about passive house standard
                    },
                },
                "RetInd": False,  # Boolean, if True, individual profiles for each category and efficiency level are returned
                "Country": "Norway",  # Optional, possiblity to get automatic holiday flags from the python holiday library.
                "TimeSeries": {  # Time series input. If not used. 1 year standard Oslo climate is applied. If time series is included, prediction will be same length as input. Minimum 24 timesteps (hours)
                    "Tout": self.temperatur_serie.tolist()
                },
            }
        # --
        else:
            request_data = {
                "StartDate": "2022-01-01",  # Initial date (influences weekday/weekend. N.B. In Shops and Culture_Sport, Saturday has a different profile than Sunday)
                "Areas": {  # Spesification of areas for building categories and efficiency levels
                    f"{self.BYGNINGSTYPE[self.bygningstype.upper()]}": {  # building category office, add sections for multiple categories. Available categories are ['Hou', 'Apt', 'Off', 'Shp', 'Htl', 'Kdg', 'Sch', 'Uni', 'CuS', 'Nsh', 'Hos', 'Other']
                        "Reg": regular_areal,  # Category regular. 'Regular' means average standard of buildings in the stock
                        "Eff-E": efficient_areal,  # Category Efficient Existing. 'Efficient' means at about TEK10 standard, representing an ambitious yet realistic target for energy efficient renovation
                        "Eff-N": 0,  # Category Efficient New. 'Efficient' means at about TEK10 standard. Gives same results as Eff-E
                        "Vef": veryefficient_areal,  # Category Very Efficient.'Very efficient' means at about passive house standard
                    },
                },
                "RetInd": False,  # Boolean, if True, individual profiles for each category and efficiency level are returned
                "Country": "Norway",  # Optional, possiblity to get automatic holiday flags from the python holiday library.
            }
        r = predict.post(
            "https://flexibilitysuite.byggforsk.no/api/Profet", json=request_data
        )
        if r.status_code == 200:
            data = r.json()
            df = DataFrame.from_dict(data)
            df.reset_index(drop=True, inplace=True)
            self.df = df[["Electric", "DHW", "SpaceHeating"]]
            self.df.columns = [
                "Elspesifikt behov",
                "Tappevannsbehov",
                "Romoppvarmingsbehov",
            ]
            self.romoppvarming_arr = df["SpaceHeating"]
            self.tappevann_arr = df["DHW"]
            self.el_spesifikk_arr = df["Electric"]
            # --
            return True
        else:
            return False

    def _nokkeltall(self):
        el_spesifikt_aarlig = avrunding(np.sum(self.df["Elspesifikt behov"]))
        tappevann_aarlig = avrunding(np.sum(self.df["Tappevannsbehov"]))
        romoppvarming_aarlig = avrunding(np.sum(self.df["Romoppvarmingsbehov"]))
        el_spesifikt_makseffekt = avrunding(np.max(self.df["Elspesifikt behov"]))
        tappevann_makseffekt = (
            avrunding(np.max(self.df["Tappevannsbehov"])) * self.MAKS_VARMEEFFEKT_FAKTOR
        )
        romoppvarming_makseffekt = (
            avrunding(np.max(self.df["Romoppvarmingsbehov"]))
            * self.MAKS_VARMEEFFEKT_FAKTOR
        )
        termisk_aarlig = romoppvarming_aarlig + tappevann_aarlig
        termisk_makseffekt = romoppvarming_makseffekt + tappevann_makseffekt
        return (
            el_spesifikt_aarlig,
            tappevann_aarlig,
            romoppvarming_aarlig,
            termisk_aarlig,
            el_spesifikt_makseffekt,
            tappevann_makseffekt,
            romoppvarming_makseffekt,
            termisk_makseffekt,
        )

    def _visualisering(self):
        FILPLASSERING = r"C:\inetpub\wwwroot"
        EL_SPESIFIKK_FARGE = "#b7dc8f"
        ROMOPPVARMING_FARGE = "#1d3c34"
        TAPPEVANN_FARGE = "#FFC358"
        plot_1_timeserie(
            self.el_spesifikk_arr,
            "Elspesifikt behov",
            self.objektid,
            FILPLASSERING,
            COLOR=EL_SPESIFIKK_FARGE,
        )
        plot_1_timeserie(
            self.tappevann_arr,
            "Tappevannsbehov",
            self.objektid,
            FILPLASSERING,
            COLOR=TAPPEVANN_FARGE,
        )
        plot_1_timeserie(
            self.romoppvarming_arr,
            "Romoppvarmingsbehov",
            self.objektid,
            FILPLASSERING,
            COLOR=ROMOPPVARMING_FARGE,
        )
        plot_1_timeserie(
            self.el_spesifikk_arr,
            "Elspesifikt behov",
            self.objektid,
            FILPLASSERING,
            COLOR=TAPPEVANN_FARGE,
            VARIGHETSKURVE=True,
        )
        plot_1_timeserie(
            self.tappevann_arr,
            "Tappevannsbehov",
            self.objektid,
            FILPLASSERING,
            COLOR=TAPPEVANN_FARGE,
            VARIGHETSKURVE=True,
        )
        plot_1_timeserie(
            self.romoppvarming_arr,
            "Romoppvarmingsbehov",
            self.objektid,
            FILPLASSERING,
            COLOR=ROMOPPVARMING_FARGE,
            VARIGHETSKURVE=True,
        )
        # -- sammenstilte
        plot_2_timeserie(
            self.tappevann_arr,
            "Tappevannsbehov",
            self.romoppvarming_arr,
            "Romoppvarmingsbehov",
            self.objektid,
            FILPLASSERING,
            COLOR_1=TAPPEVANN_FARGE,
            COLOR_2=ROMOPPVARMING_FARGE,
        )
        plot_2_timeserie(
            self.tappevann_arr,
            "Tappevannsbehov",
            self.romoppvarming_arr,
            "Romoppvarmingsbehov",
            self.objektid,
            FILPLASSERING,
            COLOR_1=TAPPEVANN_FARGE,
            COLOR_2=ROMOPPVARMING_FARGE,
            VARIGHETSKURVE=True,
        )
        plot_3_timeserie(
            self.tappevann_arr,
            "Tappevannsbehov",
            self.el_spesifikk_arr,
            "Elspesifikt behov",
            self.romoppvarming_arr,
            "Romoppvarmingsbehov",
            self.objektid,
            FILPLASSERING,
            COLOR_1="#1d3c34",
            COLOR_2=EL_SPESIFIKK_FARGE,
            COLOR_3=ROMOPPVARMING_FARGE,
        )
        plot_3_timeserie(
            self.tappevann_arr,
            "Tappevannsbehov",
            self.el_spesifikk_arr,
            "Elspesifikt behov",
            self.romoppvarming_arr,
            "Romoppvarmingsbehov",
            self.objektid,
            FILPLASSERING,
            COLOR_1="#1d3c34",
            COLOR_2=EL_SPESIFIKK_FARGE,
            COLOR_3=ROMOPPVARMING_FARGE,
            VARIGHETSKURVE=True,
        )

    def _lagring(self, timeserier_obj):
        timeserier_obj.legg_inn_timeserie(
            timeserie=self.el_spesifikk_arr, timeserie_navn="El_spesifiktbehov"
        )
        timeserier_obj.legg_inn_timeserie(
            timeserie=self.romoppvarming_arr, timeserie_navn="R_omoppvarmingsbehov"
        )
        timeserier_obj.legg_inn_timeserie(
            timeserie=self.tappevann_arr, timeserie_navn="V_armtvannsbehov"
        )

    def standard_metode(self, lagring_obj):
        errorcount = 0
        while errorcount < 2:
            state = self._beregn_energibehov()
            if state == True:
                break
            else:
                time.sleep(1)
                errorcount = errorcount + 1
                # print(errorcount)
        if state == False:
            raise ValueError("PROfet API 500 error")
        # self._visualisering()
        self._lagring(lagring_obj)
        return self._nokkeltall()


# ---------------------------------------------------------------------------------------------------------------#
# -- Fjernvarmeklasse
class Fjernvarme:
    def __init__(
        self,
        objektid,
        DEKNINGSGRAD,
        behovstype,
        df,
        VIRKNINGSGRAD=100,
    ):
        self.objektid = objektid
        self.df = df
        self.DEKNINGSGRAD = DEKNINGSGRAD
        self.VIRKNINGSGRAD = VIRKNINGSGRAD / 100  # i prosent
        self.behovstype = behovstype
        if behovstype == "V":
            self.termisk_arr = dekningsberegning(
                DEKNINGSGRAD=self.DEKNINGSGRAD, timeserie=(df["Tappevannsbehov"])
            )
        if behovstype == "R":
            self.termisk_arr = dekningsberegning(
                DEKNINGSGRAD=self.DEKNINGSGRAD, timeserie=(df["Romoppvarmingsbehov"])
            )
        if behovstype == "T":
            self.termisk_arr = dekningsberegning(
                DEKNINGSGRAD=self.DEKNINGSGRAD,
                timeserie=(df["Romoppvarmingsbehov"] + df["Tappevannsbehov"]),
            )

    def _beregn_fjernvarme(self):
        self.fjernvarme_arr = (self.termisk_arr) * self.VIRKNINGSGRAD
        self.df["Fjernvarme"] = self.fjernvarme_arr

    def _visualisering(self):
        FILPLASSERING = r"C:\inetpub\wwwroot"
        FJERNVARME_FARGE = "#00FFFF"
        plot_1_timeserie(
            self.fjernvarme_arr,
            "Fjernvarmedekning",
            self.objektid,
            FILPLASSERING,
            COLOR=FJERNVARME_FARGE,
        )
        plot_1_timeserie(
            self.fjernvarme_arr,
            "Fjernvarmedekning",
            self.objektid,
            FILPLASSERING,
            COLOR=FJERNVARME_FARGE,
            VARIGHETSKURVE=True,
        )

    def _nokkeltall(self):
        self.fjernvarme_aarlig = avrunding(np.sum(self.fjernvarme_arr))
        self.fjernvarme_makseffekt = avrunding(np.max(self.fjernvarme_arr))
        return self.fjernvarme_aarlig, self.fjernvarme_makseffekt

    def _lagring(self, timeserie_obj):
        timeserie_obj.legg_inn_timeserie(
            timeserie=-self.fjernvarme_arr,
            timeserie_navn=f"{self.behovstype}_fjernvarme",
        )

    def standard_metode(self, lagring_obj):
        self._beregn_fjernvarme()
        # self._visualisering()
        self._lagring(timeserie_obj=lagring_obj)
        return self._nokkeltall()


# ---------------------------------------------------------------------------------------------------------------#
# -- Grunnvarmeklasse
class Grunnvarme:
    def __init__(self, objektid, behovstype, df, COP, DEKNINGSGRAD):
        self.objektid = objektid
        self.DEKNINGSRAD = DEKNINGSGRAD
        self.COP = COP
        self.behovstype = behovstype
        if behovstype == "V":
            self.termisk_arr = dekningsberegning(
                DEKNINGSGRAD=self.DEKNINGSRAD, timeserie=(df["Tappevannsbehov"])
            )
        if behovstype == "R":
            self.termisk_arr = dekningsberegning(
                DEKNINGSGRAD=self.DEKNINGSRAD, timeserie=(df["Romoppvarmingsbehov"])
            )
        if behovstype == "T":
            self.termisk_arr = dekningsberegning(
                DEKNINGSGRAD=self.DEKNINGSRAD,
                timeserie=(df["Romoppvarmingsbehov"] + df["Tappevannsbehov"]),
            )

    def _beregn_grunnvarme(self):
        self.varmepumpe_arr = dekningsberegning(
            DEKNINGSGRAD=self.DEKNINGSRAD, timeserie=(self.termisk_arr)
        )
        self.levert_fra_bronner_arr = (
            self.varmepumpe_arr - self.varmepumpe_arr / self.COP
        )  # todo : timevariert COP, da ma vi ogsa hente inn informasjon om utetemperatur
        self.kompressor_arr = self.varmepumpe_arr - self.levert_fra_bronner_arr
        self.spisslast_arr = self.termisk_arr - self.varmepumpe_arr

    def _visualisering(self):
        FILPLASSERING = r"C:\inetpub\wwwroot"
        KOMPRESSOR_FARGE = "#1d3c34"
        LEVERT_FRA_BRONNER_FARGE = "#b7dc8f"
        SPISSLAST_FARGE = "#FFC358"
        plot_3_timeserie(
            timeserie_1=self.kompressor_arr,
            timeserie_1_navn="Strom til varmepumpe",
            timeserie_2=self.levert_fra_bronner_arr,
            timeserie_2_navn="Levert fra bronner",
            timeserie_3=self.spisslast_arr,
            timeserie_3_navn="Spisslast",
            objektid=self.objektid,
            filplassering=FILPLASSERING,
            COLOR_1=KOMPRESSOR_FARGE,
            COLOR_2=LEVERT_FRA_BRONNER_FARGE,
            COLOR_3=SPISSLAST_FARGE,
        )
        plot_3_timeserie(
            timeserie_1=self.kompressor_arr,
            timeserie_1_navn="Strom til varmepumpe",
            timeserie_2=self.levert_fra_bronner_arr,
            timeserie_2_navn="Levert fra bronner",
            timeserie_3=self.spisslast_arr,
            timeserie_3_navn="Spisslast",
            objektid=self.objektid,
            filplassering=FILPLASSERING,
            COLOR_1=KOMPRESSOR_FARGE,
            COLOR_2=LEVERT_FRA_BRONNER_FARGE,
            COLOR_3=SPISSLAST_FARGE,
            VARIGHETSKURVE=True,
        )

    def _nokkeltall(self):
        kompressor_aarlig = avrunding(np.sum(self.kompressor_arr))
        levert_fra_bronner_aarlig = avrunding(np.sum(self.levert_fra_bronner_arr))
        spisslast_aarlig = avrunding(np.sum(self.spisslast_arr))
        kompressor_makseffekt = avrunding(np.max(self.kompressor_arr))
        levert_fra_bronner_makseffekt = avrunding(np.max(self.levert_fra_bronner_arr))
        spisslast_makseffekt = avrunding(np.max(self.spisslast_arr))
        return (
            kompressor_aarlig,
            levert_fra_bronner_aarlig,
            spisslast_aarlig,
            kompressor_makseffekt,
            levert_fra_bronner_makseffekt,
            spisslast_makseffekt,
        )

    def _lagring(self, timeserie_obj):
        timeserie_obj.legg_inn_timeserie(
            timeserie=-(self.levert_fra_bronner_arr + self.kompressor_arr),
            timeserie_navn=f"{self.behovstype}_grunnvarme",
        )
        timeserie_obj.legg_inn_timeserie(
            timeserie=self.kompressor_arr, timeserie_navn=f"El_grunnvarme_kompressor"
        )
        timeserie_obj.legg_inn_timeserie(
            timeserie=self.spisslast_arr, timeserie_navn=f"El_kjel"
        )

    def standard_metode(self, lagring_obj):
        self._beregn_grunnvarme()
        # self._visualisering()
        self._lagring(timeserie_obj=lagring_obj)
        return self._nokkeltall()


# ---------------------------------------------------------------------------------------------------------------#
# -- Luft-luft-varmepumpe
class LuftLuftVarmepumpe:
    def __init__(self, objektid, df, COP, DEKNINGSGRAD):
        self.objektid = objektid
        self.DEKNINGSRAD = DEKNINGSGRAD
        self.COP = COP
        self.termisk_arr = df["Romoppvarmingsbehov"]

    def _beregn_luft_luft_varmepumpe(self):
        self.varmepumpe_arr = dekningsberegning(
            DEKNINGSGRAD=self.DEKNINGSRAD, timeserie=(self.termisk_arr)
        )
        self.levert_fra_luft_arr = (
            self.varmepumpe_arr - self.varmepumpe_arr / self.COP
        )  # todo : timevariert COP, da ma vi ogsa hente inn informasjon om utetemperatur
        self.kompressor_arr = self.varmepumpe_arr - self.levert_fra_luft_arr
        self.spisslast_arr = self.termisk_arr - self.varmepumpe_arr

    def _visualisering(self):
        FILPLASSERING = r"C:\inetpub\wwwroot"
        KOMPRESSOR_FARGE = "#1d3c34"
        LEVERT_FRA_LUFT_FARGE = "#b7dc8f"
        SPISSLAST_FARGE = "#FFC358"
        plot_3_timeserie(
            timeserie_1=self.kompressor_arr,
            timeserie_1_navn="Strom til varmepumpe",
            timeserie_2=self.levert_fra_luft_arr,
            timeserie_2_navn="Levert fra luft",
            timeserie_3=self.spisslast_arr,
            timeserie_3_navn="Spisslast",
            objektid=self.objektid,
            filplassering=FILPLASSERING,
            COLOR_1=KOMPRESSOR_FARGE,
            COLOR_2=LEVERT_FRA_LUFT_FARGE,
            COLOR_3=SPISSLAST_FARGE,
        )
        plot_3_timeserie(
            timeserie_1=self.kompressor_arr,
            timeserie_1_navn="Strom til varmepumpe",
            timeserie_2=self.levert_fra_luft_arr,
            timeserie_2_navn="Levert fra luft",
            timeserie_3=self.spisslast_arr,
            timeserie_3_navn="Spisslast",
            objektid=self.objektid,
            filplassering=FILPLASSERING,
            COLOR_1=KOMPRESSOR_FARGE,
            COLOR_2=LEVERT_FRA_LUFT_FARGE,
            COLOR_3=SPISSLAST_FARGE,
            VARIGHETSKURVE=True,
        )

    def _nokkeltall(self):
        kompressor_aarlig = avrunding(np.sum(self.kompressor_arr))
        levert_fra_luft_aarlig = avrunding(np.sum(self.levert_fra_luft_arr))
        spisslast_aarlig = avrunding(np.sum(self.spisslast_arr))
        kompressor_makseffekt = avrunding(np.max(self.kompressor_arr))
        levert_fra_luft_makseffekt = avrunding(np.max(self.levert_fra_luft_arr))
        spisslast_makseffekt = avrunding(np.max(self.spisslast_arr))
        return (
            kompressor_aarlig,
            levert_fra_luft_aarlig,
            spisslast_aarlig,
            kompressor_makseffekt,
            levert_fra_luft_makseffekt,
            spisslast_makseffekt,
        )

    def _lagring(self, timeserie_obj):
        timeserie_obj.legg_inn_timeserie(
            timeserie=-(self.levert_fra_luft_arr + self.kompressor_arr),
            timeserie_navn=f"R_luftluft",
        )
        timeserie_obj.legg_inn_timeserie(
            timeserie=self.kompressor_arr, timeserie_navn=f"El_luftluft_kompressor"
        )
        timeserie_obj.legg_inn_timeserie(
            timeserie=self.spisslast_arr, timeserie_navn=f"El_luftluft_spisslast"
        )

    def standard_metode(self, lagring_obj):
        self._beregn_luft_luft_varmepumpe()
        # self._visualisering()
        self._lagring(timeserie_obj=lagring_obj)
        return self._nokkeltall()


# ---------------------------------------------------------------------------------------------------------------#
# -- Solproduksjon
class Solproduksjon:
    def __init__(
        self,
        objektid: int,
        lat: float,
        lon: float,
        takflate_navn: list,
        takflate_vinkel: int,
        takflate_arealer: list,
        takflate_orienteringer: list,
        loss=14,
        mountingplace="free",
        angle=None,
        startyear=2019,
        endyear=2019,
    ):
        """
        :param objektid: int - objektid for bygget
        :param lat: latidtude
        :param lon: longitude
        :param takflate_navn: list - liste med navn pa takflate  [A,B,C,D]. Standardisert i byggtabell
        :param takflate_vinkel: list - liste med vinkler tilhorende takflate_navn
        :param takflate_arealer: list - liste med arealer tilhorende takflate_navn
        :param takflate_orienteringer: list - liste med orientering tilhorende takflate_navn
        :param loss: int - tap (pvgis)
        :param mountingplace: str - free, building
        """
        self.objektid = objektid
        self.lat = lat
        self.lon = lon
        self.takflate_vinkel = takflate_vinkel
        self.takflate_navn = takflate_navn
        self.takflate_arealer = takflate_arealer
        self.takflate_orienteringer = takflate_orienteringer
        # unngå 0
        for i in range(0, len(self.takflate_orienteringer)):
            if takflate_orienteringer[i] == 0:
                takflate_orienteringer[i] = 0.0000001
        self._validate_lists_equal_lengt()
        self.loss = loss
        self.startyear = startyear
        self.endyear = endyear
        if not angle:
            self.angle = 25
        else:
            self.angle = angle
        self.mountingplace = mountingplace
        self.takflate_pv_objs = {}
        self._timeserier_dataframes = []

    def _calculate_pv_on_one_roof_part(self, takflate_navn, aspect, footprint_area):
        # returnere timeserier
        if aspect and footprint_area:
            roof = Roof(
                lat=self.lat,
                lon=self.lon,
                angle=self.angle,
                aspect=aspect,
                footprint_area=footprint_area,
                loss=self.loss,
                mountingplace=self.mountingplace,
            )
            roof_hourly = Roof_hourly(
                lat=self.lat,
                lon=self.lon,
                angle=self.angle,
                aspect=aspect,
                footprint_area=footprint_area,
                loss=self.loss,
                mountingplace=self.mountingplace,
                pvcalc=True,
                startyear=self.startyear,
                endyear=self.endyear,
            )
            normalized = roof_hourly.normalize(E_y_on_surface=roof.E_y_on_surface())
            self._timeserier_dataframes.append(normalized[["P", "normal", "p_normal"]])
            self.takflate_pv_objs[takflate_navn] = roof

    def _validate_lists_equal_lengt(self):
        takflater = len(self.takflate_navn)
        orienteringer = len(self.takflate_orienteringer)
        arealer = len(self.takflate_arealer)
        if orienteringer != takflater:
            raise RoofValueListOrienteringNotEqualLengthError(orienteringer)
        if arealer != takflater:
            raise RoofValueListArealerNotEqualLengthError(arealer)

    def _calculate_whole_roof(self):
        for takflatenavn, aspect, footprint_area in zip(
            self.takflate_navn, self.takflate_orienteringer, self.takflate_arealer
        ):
            self._calculate_pv_on_one_roof_part(
                takflate_navn=takflatenavn, aspect=aspect, footprint_area=footprint_area
            )

    def _timesserie(self):
        normalized_hourly_sum = sum(self._timeserier_dataframes)
        return normalized_hourly_sum.p_normal

    def _visualisering(self):
        FILPLASSERING = r"C:\inetpub\wwwroot"
        SOL_FARGE = "#b7dc8f"
        plot_1_timeserie(
            self._timesserie(),
            "Solproduksjon",
            self.objektid,
            FILPLASSERING,
            COLOR=SOL_FARGE,
        )

    def _nokkeltall(self):
        e_y_sum = sum(
            [
                takflate_pv_objs.E_y_on_surface()
                for takflate_pv_objs in self.takflate_pv_objs.values()
            ]
        )
        return self.takflate_pv_objs, e_y_sum

    def _lagring(self, timeserie_obj):
        timeserie_obj.legg_inn_timeserie(
            timeserie=-self._timesserie(), timeserie_navn=f"El_solenergi"
        )

    def standard_metode(self, lagring_obj):
        self._calculate_whole_roof()
        # self._visualisering()
        self._lagring(timeserie_obj=lagring_obj)
        return self._nokkeltall()


# ---------------------------------------------------------------------------------------------------------------#
# -- Hovedmodul som tar inn energimiks og bruker de andre klassene
class Energianalyse:
    def __init__(
        self,
        filplassering,
        objektid,
        energibehov_start_beregning: bool = True,
        energibehov_temperatur_serie=None,
        energibehov_bygningstype: str = "A",
        energibehov_bygningsstandard: str = "X",
        energibehov_areal: int = 250,
        grunnvarme_start_beregning: bool = False,
        grunnvarme_energibehov: str = "T",  # gyldige input er "T": termisk, "V": varmtvann og "R": romoppvarming
        grunnvarme_dekningsgrad: int = 90,  # tall fra 0 - 100
        grunnvarme_cop: float = 3.5,  # arsvarmefaktor,
        fjernvarme_start_beregning: bool = False,
        fjernvarme_energibehov: str = "T",  # gyldige input er "T": termisk, "V": varmtvann og "R": romoppvarming
        fjernvarme_dekningsgrad: int = 100,  # tall fra 0 - 100
        luft_luft_start_beregning: bool = False,
        luft_luft_cop: float = 2.8,  # arsvarmefaktor
        luft_luft_dekningsgrad: int = 80,  # tall fra 0 - 100
        solproduksjon_start_beregning: bool = False,
        solproduksjon_lat: int = 62,  # latitude
        solproduksjon_lon: int = 10,  # longitude
        solproduksjon_takflate_vinkel: int = 30,  # feks. 30
        solproduksjon_takflate_navn: list = ["A", "B"],  # feks. ["A", "B"]
        solproduksjon_takflate_arealer: list = [10, 10],  # feks. [10, 10]
        solproduksjon_takflate_orienteringer: list = [90, -90],  # feks. [90, -90]
        visualiser: bool = False,
    ):
        # -- Valider gyldige input for termisk
        self._valider_termisk_kombinasjon(
            grunnvarme_start_beregning,
            grunnvarme_energibehov,
            fjernvarme_start_beregning,
            fjernvarme_energibehov,
            luft_luft_start_beregning,
        )
        # -- Initialiser alle parametere
        self.objektid = objektid
        self.filplassering = filplassering
        # --
        self.energibehov_start_beregning = energibehov_start_beregning
        self.energibehov_temperatur_serie = energibehov_temperatur_serie
        self.energibehov_bygningstype = energibehov_bygningstype
        self.energibehov_bygningsstandard = energibehov_bygningsstandard
        self.energibehov_areal = energibehov_areal
        self.grunnvarme_start_beregning = grunnvarme_start_beregning
        self.grunnvarme_energibehov = grunnvarme_energibehov
        self.grunnvarme_dekningsgrad = grunnvarme_dekningsgrad
        self.grunnvarme_cop = grunnvarme_cop
        self.fjernvarme_start_beregning = fjernvarme_start_beregning
        self.fjernvarme_energibehov = fjernvarme_energibehov
        self.fjernvarme_dekningsgrad = fjernvarme_dekningsgrad
        self.luft_luft_start_beregning = luft_luft_start_beregning
        self.luft_luft_cop = luft_luft_cop
        self.luft_luft_dekningsgrad = luft_luft_dekningsgrad
        self.solproduksjon_start_beregning = solproduksjon_start_beregning
        self.solproduksjon_lat = solproduksjon_lat
        self.solproduksjon_lon = solproduksjon_lon
        self.solproduksjon_takflate_vinkel = solproduksjon_takflate_vinkel
        self.solproduksjon_takflate_navn = solproduksjon_takflate_navn
        self.solproduksjon_takflate_arealer = solproduksjon_takflate_arealer
        self.solproduksjon_takflate_orienteringer = solproduksjon_takflate_orienteringer
        self.visualiser = (visualiser,)
        # --
        self.timeserier_obj = Timeserier()
        if energibehov_start_beregning == True:
            self.energibehov_obj = Energibehov(
                objektid=objektid,
                temperatur_serie=energibehov_temperatur_serie,
                bygningstype=energibehov_bygningstype,
                bygningsstandard=energibehov_bygningsstandard,
                areal=energibehov_areal,
            )
            self.energibehov_obj.standard_metode(lagring_obj=self.timeserier_obj)
        if fjernvarme_start_beregning == True:
            self.fjernvarme_obj = Fjernvarme(
                objektid=objektid,
                DEKNINGSGRAD=fjernvarme_dekningsgrad,
                behovstype=fjernvarme_energibehov,
                df=self.energibehov_obj.df,
                VIRKNINGSGRAD=100,
            )
            self.fjernvarme_obj.standard_metode(lagring_obj=self.timeserier_obj)
        if grunnvarme_start_beregning == True:
            self.grunnvarme_obj = Grunnvarme(
                objektid=objektid,
                behovstype=grunnvarme_energibehov,
                df=self.energibehov_obj.df,
                COP=grunnvarme_cop,
                DEKNINGSGRAD=grunnvarme_dekningsgrad,
            )
            self.grunnvarme_obj.standard_metode(lagring_obj=self.timeserier_obj)
        if luft_luft_start_beregning == True:
            self.luft_luft_obj = LuftLuftVarmepumpe(
                objektid=objektid,
                df=self.energibehov_obj.df,
                COP=luft_luft_cop,
                DEKNINGSGRAD=luft_luft_dekningsgrad,
            )
            self.luft_luft_obj.standard_metode(lagring_obj=self.timeserier_obj)
        if solproduksjon_start_beregning == True:
            self.solproduksjon_obj = Solproduksjon(
                objektid=objektid,
                lat=solproduksjon_lat,
                lon=solproduksjon_lon,
                takflate_navn=solproduksjon_takflate_navn,
                takflate_vinkel=solproduksjon_takflate_vinkel,
                takflate_arealer=solproduksjon_takflate_arealer,
                takflate_orienteringer=solproduksjon_takflate_orienteringer,
            )
            self.solproduksjon_obj.standard_metode(lagring_obj=self.timeserier_obj)
        # --
        self._sammenstilling()
        if visualiser:
            self._visualisering()

    def _valider_termisk_kombinasjon(
        self,
        grunnvarme_start_beregning,
        grunnvarme_energibehov,
        fjernvarme_start_beregning,
        fjernvarme_energibehov,
        luft_luft_start_beregning,
    ):
        if grunnvarme_start_beregning == True and fjernvarme_start_beregning == True:
            if not (
                (grunnvarme_energibehov == "R" and fjernvarme_energibehov == "V")
                or (grunnvarme_energibehov == "V" and fjernvarme_energibehov == "R")
            ):
                raise ValueError("Ugyldig inndatakombinasjon: grunnvarme/fjernvarme")
        if grunnvarme_start_beregning == True and luft_luft_start_beregning == True:
            if not ((grunnvarme_energibehov == "V")):
                raise ValueError("Ugyldig inndatakombinasjon: grunnvarme/luft-luft")
        if fjernvarme_start_beregning == True and luft_luft_start_beregning == True:
            if not ((fjernvarme_energibehov == "V")):
                raise ValueError("Ugyldig inndatakombinasjon: fjernvarme/luft-luft")

    def _sammenstilling(self):
        def get_series_from_dataframe_if_exists(colname):
            try:
                series = df[colname].to_numpy()
            except KeyError:
                series = None
            return series

        df = self.timeserier_obj.df
        # df.to_csv("out.csv", index=False)
        # -- Energibehov
        self.romoppvarming_timeserie = df["R_omoppvarmingsbehov"].to_numpy()
        self.tappevann_timeserie = df["V_armtvannsbehov"].to_numpy()
        self.elspesifikt_timeserie = df["El_spesifiktbehov"].to_numpy()

        # -- Kun produksjon
        self.produksjon_df = df.drop(
            ["R_omoppvarmingsbehov", "V_armtvannsbehov", "El_spesifiktbehov"], axis=1
        )
        # -- Grunnvarme
        grunnvarmeproduksjon_timeserie = [
            get_series_from_dataframe_if_exists(col)
            for col in ["R_grunnvarme", "V_grunnvarme", "T_grunnvarme"]
            if type(get_series_from_dataframe_if_exists(col)) != type(None)
        ]
        self.grunnvarme_kompressor_timeserie = get_series_from_dataframe_if_exists(
            "El_grunnvarme_kompressor"
        )
        self.grunnvarme_elkjel_timesserie = get_series_from_dataframe_if_exists(
            "El_kjel"
        )
        # --
        self.grunnvarmeproduksjon_R_timeserie = get_series_from_dataframe_if_exists(
            "R_grunnvarme"
        )
        self.grunnvarmeproduksjon_V_timeserie = get_series_from_dataframe_if_exists(
            "V_grunnvarme"
        )
        self.grunnvarmeproduksjon_T_timeserie = get_series_from_dataframe_if_exists(
            "T_grunnvarme"
        )
        if grunnvarmeproduksjon_timeserie:
            self.grunnvarmeproduksjon_timeserie = (
                grunnvarmeproduksjon_timeserie[0] + self.grunnvarme_kompressor_timeserie
            )
        else:
            self.grunnvarmeproduksjon_timeserie = None
        # -- Fjernvarme
        fjernvarmeproduksjon_timeserie = [
            get_series_from_dataframe_if_exists(col)
            for col in ["R_fjernvarme", "V_fjernvarme", "T_fjernvarme"]
            if type(get_series_from_dataframe_if_exists(col)) != type(None)
        ]
        self.fjernvarmeproduksjon_R_timeserie = get_series_from_dataframe_if_exists(
            "R_fjernvarme"
        )
        self.fjernvarmeproduksjon_V_timeserie = get_series_from_dataframe_if_exists(
            "V_fjernvarme"
        )
        self.fjernvarmeproduksjon_T_timeserie = get_series_from_dataframe_if_exists(
            "T_fjernvarme"
        )
        if fjernvarmeproduksjon_timeserie:
            self.fjernvarmeproduksjon_timeserie = fjernvarmeproduksjon_timeserie[0]
        else:
            self.fjernvarmeproduksjon_timeserie = None
        # -- Luft-luft
        self.luftluftproduksjon_timeserie = get_series_from_dataframe_if_exists(
            "R_luftluft"
        )
        self.luftluft_kompressor_timeserie = get_series_from_dataframe_if_exists(
            "El_luftluft_kompressor"
        )
        self.luftluft_spisslast_timeserie = get_series_from_dataframe_if_exists(
            "El_luftluft_spisslast"
        )
        # -- Solproduksjon
        self.solenergi_timeserie = get_series_from_dataframe_if_exists("El_solenergi")

        # -- Sammenstilling, finne unike kategorier [El, T, R, V]
        grouped_cols = df.columns.str.split("_", expand=True)
        grouped_cols = [x[0] for x in grouped_cols]
        unique_groups = sorted(list(set(grouped_cols)))
        # -- Sammenstilling, trekke sammen unike kategorier -> new_df
        new_df = DataFrame()
        for group in unique_groups:
            cols = [col for col in df.columns if col.startswith(group)]
            new_df[group] = df[cols].sum(axis=1)
        # -- Sammenstilling, hvis "T"; trekke sammen
        if "T" in new_df.columns:
            new_df["T"] = new_df["V"] + new_df["R"] + new_df["T"]
            new_df.drop(["V", "R"], inplace=True, axis=1)
        # -- get_series_from_dataframe_if_exists
        df = new_df
        self.new_df = new_df
        # -- Timeserier før
        self.start_el = self.elspesifikt_timeserie
        self.start_termisk = self.romoppvarming_timeserie + self.tappevann_timeserie
        self.start_behov = self.start_termisk + self.start_el
        # -- Timeserier etter
        self.rest_el = get_series_from_dataframe_if_exists("El")
        if get_series_from_dataframe_if_exists("T") is None:
            self.rest_termisk = get_series_from_dataframe_if_exists(
                "V"
            ) + get_series_from_dataframe_if_exists("R")
        else:
            self.rest_termisk = get_series_from_dataframe_if_exists("T")
        self.rest_behov = self.rest_termisk + self.rest_el

    def _visualisering(self):
        FILPLASSERING = self.filplassering
        y_max = np.max(self.start_behov) * 1.1
        y_min = np.min(self.rest_behov)
        if y_min > 0:
            y_min = 0

        # -- behovsplot timeplot
        self.behovsplot_timeplot = plot_3_timeserie(
            timeserie_1=self.elspesifikt_timeserie,
            timeserie_1_navn="Elspesifikt behov",
            timeserie_2=self.tappevann_timeserie,
            timeserie_2_navn="Varmtvannsbehov",
            timeserie_3=self.romoppvarming_timeserie,
            timeserie_3_navn="Oppvarmingsbehov",
            objektid=self.objektid,
            filplassering=FILPLASSERING,
            COLOR_1="#8fb7dc",
            COLOR_2="#dc8fb7",
            COLOR_3="#b7dc8f",
            VARIGHETSKURVE=False,
            plot_navn="energibehov",
            y_max=y_max,
            y_min=y_min,
        )

        # -- behovsplot varighetskurve
        self.behovsplot_varighetskurve = plot_3_timeserie(
            timeserie_1=self.timeserier_obj.df["El_spesifiktbehov"],
            timeserie_1_navn="Elspesifikt behov",
            timeserie_2=self.timeserier_obj.df["V_armtvannsbehov"],
            timeserie_2_navn="Varmtvannsbehov",
            timeserie_3=self.timeserier_obj.df["R_omoppvarmingsbehov"],
            timeserie_3_navn="Oppvarmingsbehov",
            objektid=self.objektid,
            filplassering=FILPLASSERING,
            COLOR_1="#8fb7dc",
            COLOR_2="#dc8fb7",
            COLOR_3="#b7dc8f",
            VARIGHETSKURVE=True,
            plot_navn="energibehov",
            y_max=y_max,
            y_min=y_min,
        )

        # -- el/termisk start timeplot
        #        plot_2_timeserie(
        #            timeserie_1 = self.start_el,
        #            timeserie_1_navn = "Elspesifikt behov",
        #            timeserie_2 = self.start_termisk,
        #            timeserie_2_navn = "Termisk behov",
        #            objektid = self.objektid,
        #            filplassering = FILPLASSERING,
        #            COLOR_1="#8fb7dc",
        #            COLOR_2="#dc8f91",
        #            VARIGHETSKURVE=False,
        #            plot_navn="start",
        #            y_max = y_max,
        #            y_min = y_min
        #            )

        # -- el/termisk start varighetskurve
        #        plot_2_timeserie(
        #            timeserie_1 = self.start_el,
        #            timeserie_1_navn = "Elspesifikt behov",
        #            timeserie_2 = self.start_termisk,
        #            timeserie_2_navn = "Termisk behov",
        #            objektid = self.objektid,
        #            filplassering = FILPLASSERING,
        #            COLOR_1="#8fb7dc",
        #            COLOR_2="#dc8f91",
        #            VARIGHETSKURVE=True,
        #            plot_navn="start",
        #            y_max = y_max
        #            y_min = y_min
        #            )

        # -- el/termisk rest timeplot
        self.nettutveksling_timeplot = plot_1_timeserie(
            timeserie_1=self.rest_behov,
            timeserie_1_navn="Elektrisk energiutveksling mot nett",
            objektid=self.objektid,
            filplassering=FILPLASSERING,
            COLOR_1="#8fb7dc",
            VARIGHETSKURVE=False,
            plot_navn="rest",
            y_max=y_max,
            y_min=y_min,
        )

        # -- el/termisk rest timeplot
        self.nettutveksling_varighetskurve = plot_1_timeserie(
            timeserie_1=self.rest_behov,
            timeserie_1_navn="Elektrisk energiutveksling mot nett",
            objektid=self.objektid,
            filplassering=FILPLASSERING,
            COLOR_1="#8fb7dc",
            VARIGHETSKURVE=True,
            plot_navn="rest",
            y_max=y_max,
            y_min=y_min,
        )
        """
        # -- el/termisk rest timeplot
        plot_2_timeserie(
            timeserie_1=self.rest_el,
            timeserie_1_navn="Elektrisk energiutveksling",
            timeserie_2=self.rest_termisk,
            timeserie_2_navn="Termisk energiutveksling",
            objektid=self.objektid,
            filplassering=FILPLASSERING,
            COLOR_1="#8fb7dc",
            COLOR_2="#dc8f91",
            VARIGHETSKURVE=False,
            plot_navn="rest",
            y_max=y_max,
            y_min=y_min,
        )

        # -- el/termisk rest varighetskurve
        plot_2_timeserie(
            timeserie_1=self.rest_el,
            timeserie_1_navn="Elektrisk behov",
            timeserie_2=self.rest_termisk,
            timeserie_2_navn="Termisk behov",
            objektid=self.objektid,
            filplassering=FILPLASSERING,
            COLOR_1="#8fb7dc",
            COLOR_2="#dc8f91",
            VARIGHETSKURVE=True,
            plot_navn="rest",
            y_max=y_max,
            y_min=y_min,
        )
        """
        # -- totalt behov start timeplot

        #        plot_1_timeserie(
        #            timeserie_1 = self.start_behov,
        #            timeserie_1_navn = "Energibehov (elspesifikt + termisk)",
        #            objektid = self.objektid,
        #            filplassering = FILPLASSERING,
        #            COLOR_1="#1d3c34",
        #            VARIGHETSKURVE=False,
        #            plot_navn="startbehov",
        #            y_max = y_max,
        #            y_min = y_min
        #            )

        # -- totalt behov start varighetskurve
        #        plot_1_timeserie(
        #            timeserie_1 = self.start_behov,
        #            timeserie_1_navn = "Energibehov (elspesifikt + termisk)",
        #            objektid = self.objektid,
        #            filplassering = FILPLASSERING,
        #            COLOR_1="#1d3c34",
        #            VARIGHETSKURVE=True,
        #            plot_navn="startbehov",
        #            y_max = y_max,
        #            y_min = y_min
        #            )

        # -- totalt behov start timeplot
        #        plot_1_timeserie(
        #            timeserie_1 = self.rest_behov,
        #            timeserie_1_navn = "Energibehov (elspesifikt + termisk)",
        #            objektid = self.objektid,
        #            filplassering = FILPLASSERING,
        #            COLOR_1="#1d3c34",
        #            VARIGHETSKURVE=False,
        #            plot_navn="restbehov",
        #            y_max = y_max,
        #            y_min = y_min
        #            )

        # -- totalt behov start varighetskurve
        #        plot_1_timeserie(
        #            timeserie_1 = self.rest_behov,
        #            timeserie_1_navn = "Energibehov (elspesifikt + termisk)",
        #            objektid = self.objektid,
        #            filplassering = FILPLASSERING,
        #            COLOR_1="#1d3c34",
        #            VARIGHETSKURVE=True,
        #            plot_navn="restbehov",
        #            y_max = y_max,
        #            y_min = y_min
        #            )

        # -- ny type plot --
        # -- temperatur
        if self.energibehov_temperatur_serie is not None:
            self.temperaturplot = plot_temperatur(
                temperatur=self.energibehov_temperatur_serie,
                objektid=self.objektid,
                filplassering=FILPLASSERING,
                COLOR_1="#1d3c34",
                VARIGHETSKURVE=False,
                plot_navn="temperatur",
            )

        # -- behovsplot timeplot

    #        plot_produksjon(
    #            df=self.produksjon_df,
    #            objektid=self.objektid,
    #            filplassering=FILPLASSERING,
    #            VARIGHETSKURVE=False,
    #            plot_navn="produksjon",
    #            y_max=y_max,
    #            y_min=0,
    #        )

    # -- behovsplot varighetskurve
    #        plot_produksjon(
    #            df=self.produksjon_df,
    #            objektid=self.objektid,
    #            filplassering=FILPLASSERING,
    #            VARIGHETSKURVE=True,
    #            plot_navn="produksjon",
    #            y_max=y_max,
    #            y_min=0,
    #        )

    def _nokkeltall(self):
        pass

    def _lagring(self, objektid):
        # skriver de ut de relevante timeseriene til tabell
        pass

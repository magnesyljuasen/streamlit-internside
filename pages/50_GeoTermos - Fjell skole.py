import streamlit as st
import pandas as pd
import numpy as np
import datetime
import matplotlib.pyplot as plt
import matplotlib
#from datetime import datetime, timedelta
from streamlit_extras.chart_container import chart_container

from helpscripts._utils import month_to_hour, hour_to_month, hour_to_week, hour_to_month_max

class Kostnadsanalyse:
    def __init__(
        self,
        el_timeserie,
        spotpris,
        leap_year = False
    ):
        self.el_start_timeserie = el_timeserie
        self.spotpris = spotpris
        self.leap_year = leap_year
        self.kostnad_start_timeserie = self._beregn_kostnad(self.el_start_timeserie)
        # --
        self.kostnad_start = int(round(np.sum(self.kostnad_start_timeserie), -2))

    def _beregn_kostnad(self, el_timeserie):
        if np.sum(el_timeserie) == 0:
            return np.zeros(len(el_timeserie))
        #fast_gebyr_arr = np.zeros(8760)
        #elspot_arr = np.zeros(8760)
        #pslag_arr = np.zeros(8760)
        #forbruksavgift_arr = np.zeros(8760)
        #enova_avgift_arr = np.zeros(8760)
        #kapasitetsledd_arr = np.zeros(8760)
        #energiledd_arr = np.zeros(8760)
        
        elspot_arr = el_timeserie * self.spotpris  # kr
        kapasitetsledd_arr_monthly, energiledd_arr = self._beregn_nettleie(el_timeserie)
        # hvis FEIL
        #kapasitetsledd_arr_monthly.append(0)
        #kapasitetsledd_arr_monthly.append(0)
        kapasitetsledd_arr = month_to_hour(kapasitetsledd_arr_monthly, leap_year=self.leap_year)  # kr
        #pslag_arr = el_timeserie * (1 / 100)  # kr
        forbruksavgift_arr = el_timeserie * (16.13 / 100)  # kr
        #enova_avgift_arr = el_timeserie * (1 / 100)  # kr
        indexes = np.where(el_timeserie > 0)[0]
        fast_gebyr_sats = 6000 / len(indexes)
        fast_gebyr_arr = []
        for i in range(0, len(el_timeserie)):
            if el_timeserie[i] != 0:
                fast_gebyr_arr.append(fast_gebyr_sats)
            else:
                fast_gebyr_arr.append(0)
        #df = pd.DataFrame({"Fast gebyr" : np.sum(fast_gebyr_arr),
        #                   "Spotpris" : np.sum(elspot_arr),
        #                   "Forbruksavgift" : np.sum(forbruksavgift_arr),
        #                   "Energiledd" : np.sum(energiledd_arr),
        #                   "Kapasitetsledd" : np.sum(kapasitetsledd_arr)})
        #st.bar_chart(df)
        #st.write(f"Fast gebyr: {int(np.sum(fast_gebyr_arr))}")
        #st.write(f"Spotpris: {int(np.sum(elspot_arr))}")
        #st.write(f"Forbruksavgift: {int(np.sum(forbruksavgift_arr))}")
        #st.write(f"Energiledd: {int(np.sum(energiledd_arr))}")
        #st.write(f"Kapasitetsledd: {int(np.sum(kapasitetsledd_arr))}")
        #st.write(f"Sum : {int(np.sum(fast_gebyr_arr)) + int(np.sum(elspot_arr)) + int(np.sum(forbruksavgift_arr)) + int(np.sum(energiledd_arr)) + int(np.sum(kapasitetsledd_arr))}")
        #st.markdown("---")
        #st.stop()
        #st.bar_chart(df)
        return (
            fast_gebyr_arr
            + elspot_arr
            #+ pslag_arr
            + forbruksavgift_arr
            #+ enova_avgift_arr
            + kapasitetsledd_arr
            + energiledd_arr
        )
        
    def _beregn_nettleie(self, el_timeserie):
        if self.leap_year == True:
            days_in_feb = 29
        else:
            days_in_feb = 28
        max_value = 0
        max_value_list = []
        day = 0
        energiledd_day_winter = 9.84 / 100  # kr/kWh
        energliedd_night_winter = 9.84 / 100  # kr/kWh
        energiledd_summer = 15.84 / 100 # kr/kWh
        kap_winter = 90
        kap_summer = 30
        state = "night"
        energiledd_arr = []
        for i, new_max_value in enumerate(el_timeserie):
            season = self._sesong(day)
            # finne state
            if (i % 6) == 0:
                state = "day"
            if (i % 22) == 0:
                state = "night"
            # energiledd
            if state == "night" and season == "winter":
                energiledd_arr.append(new_max_value * energliedd_night_winter)
            elif state == "helg" and season == "winter":
                energiledd_arr.append(new_max_value * energliedd_night_winter)
            elif state == "day" and season == "winter":
                energiledd_arr.append(new_max_value * energiledd_day_winter)
            elif season == "summer":
                energiledd_arr.append(new_max_value * energiledd_summer)
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
                if day == 31 + days_in_feb:
                    max_feb = float(
                        round(np.mean(np.sort(max_value_list)[::-1][:3]), 2)
                    )
                    max_value_list = []
                if day == 31 + days_in_feb + 31:
                    max_mar = float(
                        round(np.mean(np.sort(max_value_list)[::-1][:3]), 2)
                    )
                    max_value_list = []
                if day == 31 + days_in_feb + 31 + 30:
                    max_apr = float(
                        round(np.mean(np.sort(max_value_list)[::-1][:3]), 2)
                    )
                    max_value_list = []
                if day == 31 + days_in_feb + 31 + 30 + 31:
                    max_may = float(
                        round(np.mean(np.sort(max_value_list)[::-1][:3]), 2)
                    )
                    max_value_list = []
                if day == 31 + days_in_feb + 31 + 30 + 31 + 30:
                    max_jun = float(
                        round(np.mean(np.sort(max_value_list)[::-1][:3]), 2)
                    )
                    max_value_list = []
                if day == 31 + days_in_feb + 31 + 30 + 31 + 30 + 31:
                    max_jul = float(
                        round(np.mean(np.sort(max_value_list)[::-1][:3]), 2)
                    )
                    max_value_list = []
                if day == 31 + days_in_feb + 31 + 30 + 31 + 30 + 31 + 31:
                    max_aug = float(
                        round(np.mean(np.sort(max_value_list)[::-1][:3]), 2)
                    )
                    max_value_list = []
                if day == 31 + days_in_feb + 31 + 30 + 31 + 30 + 31 + 31 + 30:
                    max_sep = float(
                        round(np.mean(np.sort(max_value_list)[::-1][:3]), 2)
                    )
                    max_value_list = []
                if day == 31 + days_in_feb + 31 + 30 + 31 + 30 + 31 + 31 + 30 + 31:
                    max_oct = float(
                        round(np.mean(np.sort(max_value_list)[::-1][:3]), 2)
                    )
                    max_value_list = []
                if day == 31 + days_in_feb + 31 + 30 + 31 + 30 + 31 + 31 + 30 + 31 + 30:
                    max_nov = float(
                        round(np.mean(np.sort(max_value_list)[::-1][:3]), 2)
                    )
                    max_value_list = []
                if day == 31 + days_in_feb + 31 + 30 + 31 + 30 + 31 + 31 + 30 + 31 + 30 + 31:
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
            month = i + 1
            if month >= 4 and month <= 12:
                kapasitestledd_arr.append(mnd_max * kap_summer)
            else:
                kapasitestledd_arr.append(mnd_max * kap_winter)
        return kapasitestledd_arr, energiledd_arr

    def _beregn_nettleie_2(self, el_timeserie):
        if self.leap_year == True:
            days_in_feb = 29
        else:
            days_in_feb = 28
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
        max_jan = 0
        max_feb = 0
        max_mar = 0
        max_apr = 0
        max_may = 0
        max_jun = 0
        max_jul = 0
        max_aug = 0
        max_sep = 0
        max_oct = 0
        max_nov = 0
        max_dec = 0
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
                if day == 31 + days_in_feb:
                    max_feb = float(
                        round(np.mean(np.sort(max_value_list)[::-1][:3]), 2)
                    )
                    max_value_list = []
                if day == 31 + days_in_feb + 31:
                    max_mar = float(
                        round(np.mean(np.sort(max_value_list)[::-1][:3]), 2)
                    )
                    max_value_list = []
                if day == 31 + days_in_feb + 31 + 30:
                    max_apr = float(
                        round(np.mean(np.sort(max_value_list)[::-1][:3]), 2)
                    )
                    max_value_list = []
                if day == 31 + days_in_feb + 31 + 30 + 31:
                    max_may = float(
                        round(np.mean(np.sort(max_value_list)[::-1][:3]), 2)
                    )
                    max_value_list = []
                if day == 31 + days_in_feb + 31 + 30 + 31 + 30:
                    max_jun = float(
                        round(np.mean(np.sort(max_value_list)[::-1][:3]), 2)
                    )
                    max_value_list = []
                if day == 31 + days_in_feb + 31 + 30 + 31 + 30 + 31:
                    max_jul = float(
                        round(np.mean(np.sort(max_value_list)[::-1][:3]), 2)
                    )
                    max_value_list = []
                if day == 31 + days_in_feb + 31 + 30 + 31 + 30 + 31 + 31:
                    max_aug = float(
                        round(np.mean(np.sort(max_value_list)[::-1][:3]), 2)
                    )
                    max_value_list = []
                if day == 31 + days_in_feb + 31 + 30 + 31 + 30 + 31 + 31 + 30:
                    max_sep = float(
                        round(np.mean(np.sort(max_value_list)[::-1][:3]), 2)
                    )
                    max_value_list = []
                if day == 31 + days_in_feb + 31 + 30 + 31 + 30 + 31 + 31 + 30 + 31:
                    max_oct = float(
                        round(np.mean(np.sort(max_value_list)[::-1][:3]), 2)
                    )
                    max_value_list = []
                if day == 31 + days_in_feb + 31 + 30 + 31 + 30 + 31 + 31 + 30 + 31 + 30:
                    max_nov = float(
                        round(np.mean(np.sort(max_value_list)[::-1][:3]), 2)
                    )
                    max_value_list = []
                if day == 31 + days_in_feb + 31 + 30 + 31 + 30 + 31 + 31 + 30 + 31 + 30 + 31:
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
            if mnd_max == 0:
                kapasitestledd_arr.append(0)
            if mnd_max > 0 and mnd_max < 2:
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
    
    def _sesong(self, dag_nummer):
        # Convert day number to a date object
        year = datetime.datetime.now().year  # Get the current year
        dato = datetime.datetime(year, 1, 1) + datetime.timedelta(dag_nummer - 1)

        # Check if the date is a weekend (Saturday or Sunday)
        if 10 <= dato.month <= 12 or 1 <= dato.month <= 3:
            return "winter"
        else:
            return "summer"


st.set_page_config(
    page_title="Grunnvarme",
    page_icon="🏔️",
    layout="wide"
)

with open("styles/main.css") as f:
    st.markdown("<style>{}</style>".format(f.read()), unsafe_allow_html=True)
    
def last_nonzero_index(array):
    nonzero_indices = np.where(array > 0)[0]
    if len(nonzero_indices) > 0:
        last_nonzero_index = nonzero_indices[-1]
        return last_nonzero_index
    else:
        return 0

def timeplot(enhet, navn, color, timeserie_2020_2021, timeserie_2021_2022, timeserie_2022_2023, timeserie_2023_2024, year = 2020, utetemperatur_2020_2021 = None, utetemperatur_2021_2022 = None, utetemperatur_2022_2023 = None, utetemperatur_2023_2024 = None):
    #t = np.arange(datetime(2020,1,1), datetime(2021,1,1), timedelta(days=1)).astype(datetime)
    fig, axs = plt.subplots(1, 4, figsize=(16, 6), sharey=True)
    axs[0].plot(np.arange(8784), timeserie_2020_2021, label = f"{int(np.sum(timeserie_2020_2021)):,} {enhet}/år".replace(",", " "), color = color)
    axs[0].set_title('2020')
    axs[1].plot(np.arange(8760), timeserie_2021_2022, label = f"{int(np.sum(timeserie_2021_2022)):,} {enhet}/år".replace(",", " "), color = color)
    axs[1].set_title('2021')
    axs[2].plot(np.arange(8760), timeserie_2022_2023, label = f"{int(np.sum(timeserie_2022_2023)):,} {enhet}/år".replace(",", " "), color = color)
    axs[2].set_title('2022')
    axs[3].plot(np.arange(8760), timeserie_2023_2024, label = f"{int(np.sum(timeserie_2023_2024)):,} {enhet}/år".replace(",", " "), color = color)
    axs[3].set_title('2023')
    if year == 2023:
        axs[3].axvline(x=last_nonzero_index(timeserie_2023_2024), color='red', linestyle='--', label='Rapportdato')
    #--
    if utetemperatur_2020_2021 is not None and utetemperatur_2021_2022 is not None and utetemperatur_2022_2023 is not None and utetemperatur_2023_2024 is not None:
        TEMPERATURE_COLOR = "grey"
        ax2_0 = axs[0].twinx()
        ax2_0.set_ylim(-30, 60)
        ax2_0.set_ylabel("Utetemperatur [°C]", fontsize=14, labelpad=25)
        ax2_1 = axs[1].twinx()
        ax2_1.set_ylim(-30, 60)
        ax2_0.set_ylabel("Utetemperatur [°C]", fontsize=14, labelpad=25)
        ax2_2 = axs[2].twinx()
        ax2_2.set_ylim(-30, 60)
        ax2_0.set_ylabel("Utetemperatur [°C]", fontsize=14, labelpad=25)
        ax2_3 = axs[3].twinx()
        ax2_3.set_ylim(-30, 60)
        ax2_0.set_ylabel("Utetemperatur [°C]", fontsize=14, labelpad=25)
        ax2_0.plot(np.arange(8784), utetemperatur_2020_2021, label = f"{int(np.average(utetemperatur_2020_2021)):,} °C".replace(",", " "), color = TEMPERATURE_COLOR, alpha=0.4)
        ax2_1.plot(np.arange(8760), utetemperatur_2021_2022, label = f"{int(np.average(utetemperatur_2021_2022)):,} °C".replace(",", " "), color = TEMPERATURE_COLOR, alpha=0.4)
        ax2_2.plot(np.arange(8760), utetemperatur_2022_2023, label = f"{int(np.average(utetemperatur_2022_2023)):,} °C".replace(",", " "), color = TEMPERATURE_COLOR, alpha=0.4)
        ax2_3.plot(np.arange(8760), utetemperatur_2023_2024, label = f"{int(np.average(utetemperatur_2023_2024)):,} °C".replace(",", " "), color = TEMPERATURE_COLOR, alpha=0.4)
    fig.add_subplot(111, frameon=False)
    plt.tick_params(labelcolor='none', which='both', top=False, bottom=False, left=False, right=False)
    plt.xlabel("Timer i ett år", fontsize=14, labelpad=30)
    plt.ylabel(navn, fontsize=14, labelpad=25)

    for ax in axs.flat:
        ax.legend()
        ax.get_xaxis().set_major_formatter(
        matplotlib.ticker.FuncFormatter(lambda x, p: format(int(x), ',').replace(",", " ")))
        ax.get_yaxis().set_major_formatter(
        matplotlib.ticker.FuncFormatter(lambda x, p: format(int(x), ',').replace(",", " ")))
        ax.grid(True)
        ax.set_xlim([0,8760])
        ax.set_ylim([0, None])
    plt.tight_layout()
    st.pyplot(plt)
    plt.close()
    
def mndplot(enhet, navn, color, timeserie_2020_2021, timeserie_2021_2022, timeserie_2022_2023, timeserie_2023_2024, year = 2020):
    mnd = ["jan", "feb", "mar", "apr", "mai", "jun", "jul", "aug", "sep", "okt", "nov", "des"]
    fig, axs = plt.subplots(1, 4, figsize=(16, 6), sharey=True)
    axs[0].bar(mnd, hour_to_month(timeserie_2020_2021), label = f"{int(np.sum(timeserie_2020_2021)):,} {enhet}/år".replace(",", " "), color = color)
    axs[0].set_title('2020')
    axs[1].bar(mnd, hour_to_month(timeserie_2021_2022), label = f"{int(np.sum(timeserie_2021_2022)):,} {enhet}/år".replace(",", " "), color = color)
    axs[1].set_title('2021')
    axs[2].bar(mnd, hour_to_month(timeserie_2022_2023), label = f"{int(np.sum(timeserie_2022_2023)):,} {enhet}/år".replace(",", " "), color = color)
    axs[2].set_title('2022')
    axs[3].bar(mnd, hour_to_month(timeserie_2023_2024), label = f"{int(np.sum(timeserie_2023_2024)):,} {enhet}/år".replace(",", " "), color = color)
    axs[3].set_title('2023')
    if year == 2023:
        axs[3].axvline(x=last_nonzero_index(np.array(hour_to_month(timeserie_2023_2024))), color='red', linestyle='--', label='Rapportdato')
    fig.add_subplot(111, frameon=False)
    plt.tick_params(labelcolor='none', which='both', top=False, bottom=False, left=False, right=False)
    plt.ylabel(navn, fontsize=14, labelpad=30)
    plt.xlabel("Måneder", fontsize=14, labelpad=30)

    for ax in axs.flat:
        ax.legend()
        ax.get_yaxis().set_major_formatter(
        matplotlib.ticker.FuncFormatter(lambda x, p: format(int(x), ',').replace(",", " ")))
        plt.setp(ax.get_xticklabels(), 
        rotation = 90)
        ax.grid(True)
        ax.set_ylim([0, None])
    plt.tight_layout()
    st.pyplot(plt)
    plt.close()
    
def mndplot_max(enhet, navn, color, timeserie_2020_2021, timeserie_2021_2022, timeserie_2022_2023, timeserie_2023_2024, year = 2020):
    mnd = ["jan", "feb", "mar", "apr", "mai", "jun", "jul", "aug", "sep", "okt", "nov", "des"]
    fig, axs = plt.subplots(1, 4, figsize=(16, 6), sharey=True)
    axs[0].bar(mnd, hour_to_month_max(timeserie_2020_2021), label = f"{int(np.max(timeserie_2020_2021)):,} {enhet}/år".replace(",", " "), color = color)
    axs[0].set_title('2020')
    axs[1].bar(mnd, hour_to_month_max(timeserie_2021_2022), label = f"{int(np.max(timeserie_2021_2022)):,} {enhet}/år".replace(",", " "), color = color)
    axs[1].set_title('2021')
    axs[2].bar(mnd, hour_to_month_max(timeserie_2022_2023), label = f"{int(np.max(timeserie_2022_2023)):,} {enhet}/år".replace(",", " "), color = color)
    axs[2].set_title('2022')
    axs[3].bar(mnd, hour_to_month_max(timeserie_2023_2024), label = f"{int(np.max(timeserie_2023_2024)):,} {enhet}/år".replace(",", " "), color = color)
    axs[3].set_title('2023')
    if year == 2023:
        axs[3].axvline(x=last_nonzero_index(np.array(hour_to_month_max(timeserie_2023_2024))), color='red', linestyle='--', label='Rapportdato')
    fig.add_subplot(111, frameon=False)
    plt.tick_params(labelcolor='none', which='both', top=False, bottom=False, left=False, right=False)
    plt.ylabel(navn, fontsize=14, labelpad=30)
    plt.xlabel("Måneder", fontsize=14, labelpad=30)

    for ax in axs.flat:
        ax.legend()
        ax.get_yaxis().set_major_formatter(
        matplotlib.ticker.FuncFormatter(lambda x, p: format(int(x), ',').replace(",", " ")))
        plt.setp(ax.get_xticklabels(), 
        rotation = 90)
        ax.grid(True)
        ax.set_ylim([0, None])
    plt.tight_layout()
    st.pyplot(plt)
    plt.close()
    
def ukeplot(enhet, navn, color, timeserie_2020_2021, timeserie_2021_2022, timeserie_2022_2023, timeserie_2023_2024, year = 2020):
    #-- Alt 1
    uke = np.arange(1, 53)
    #fig, axs = plt.subplots(2, 2, sharex=True, sharey=True, figsize=(10,8))
    fig, axs = plt.subplots(1, 4, figsize=(16, 6), sharey=True)
    axs[0].bar(uke, hour_to_week(timeserie_2020_2021), label = f"{int(np.sum(timeserie_2020_2021)):,} {enhet}/år".replace(",", " "), color = color)
    axs[0].set_title('2020')
    axs[1].bar(uke, hour_to_week(timeserie_2021_2022), label = f"{int(np.sum(timeserie_2021_2022)):,} {enhet}/år".replace(",", " "), color = color)
    axs[1].set_title('2021')
    axs[2].bar(uke, hour_to_week(timeserie_2022_2023), label = f"{int(np.sum(timeserie_2022_2023)):,} {enhet}/år".replace(",", " "), color = color)
    axs[2].set_title('2022')
    axs[3].bar(uke, hour_to_week(timeserie_2023_2024), label = f"{int(np.sum(timeserie_2023_2024)):,} {enhet}/år".replace(",", " "), color = color)
    axs[3].set_title('2023')
    if year == 2023:
        axs[3].axvline(x=last_nonzero_index(np.array(hour_to_week(timeserie_2023_2024))), color='red', linestyle='--', label='Rapportdato')
    
    fig.add_subplot(111, frameon=False)
    plt.tick_params(labelcolor='none', which='both', top=False, bottom=False, left=False, right=False)
    plt.ylabel(navn, fontsize=14, labelpad=30)
    plt.xlabel("Uker", fontsize=14, labelpad=30)

    for ax in axs.flat:
        ax.legend()
        ax.get_yaxis().set_major_formatter(
        matplotlib.ticker.FuncFormatter(lambda x, p: format(int(x), ',').replace(",", " ")))
        ax.grid(True)
        ax.set_ylim([0, None])
    plt.tight_layout()
    st.pyplot(plt)
    plt.close()
    
def plot_serie(serie, df, visualiser = True):
    st.header(serie)
    #--
    timeserie_2020_2021 = df[serie].head(8784).to_numpy()
    utetemperatur_2020_2021 = df["Utetemperatur"].head(8784).to_numpy()
    spotpris_2020_2021 = df["Spotpris"].head(8784).to_numpy()
    #--
    timeserie_2021_2022 = df[serie].iloc[8784:(8784+8760)].to_numpy()
    utetemperatur_2021_2022 = df["Utetemperatur"].iloc[8784:(8784+8760)].to_numpy()
    spotpris_2021_2022 = df["Spotpris"].iloc[8784:(8784+8760)].to_numpy()
    #--
    timeserie_2022_2023 = df[serie].iloc[(8784+8760):(8784+8760+8760)].to_numpy()
    utetemperatur_2022_2023 = df["Utetemperatur"].iloc[(8784+8760):(8784+8760+8760)].to_numpy()
    spotpris_2022_2023 = df["Spotpris"].iloc[(8784+8760):(8784+8760+8760)].to_numpy()
    #--
    timeserie_2023_2024 = df[serie].iloc[(8784+8760+8760):(8784+8760+8760+8760)].to_numpy()
    utetemperatur_2023_2024 = df["Utetemperatur"].iloc[(8784+8760+8760):(8784+8760+8760+8760)].to_numpy()
    spotpris_2023_2024 = df["Spotpris"].iloc[(8784+8760+8760):(8784+8760+8760+8760)].to_numpy()
    
    #-- plot timeseries
    #     #c1, c2, c3 = st.columns(3)
    
    #with c1:
    st.write("**Time (kW)**")
    zeros = np.zeros(24)
    df = pd.DataFrame({f"{serie} 2020" : timeserie_2020_2021, f"{serie} 2021" : np.append(timeserie_2021_2022, zeros), f"{serie} 2022" : np.append(timeserie_2022_2023, zeros), f"{serie} 2023" : np.append(timeserie_2023_2024, zeros)})
    with chart_container(df, export_formats=["CSV"]):
        pass
    if visualiser == True:
        timeplot("kWh", f"{serie} [kW]", "#1d3c34", timeserie_2020_2021, timeserie_2021_2022, timeserie_2022_2023, timeserie_2023_2024, 2023, utetemperatur_2020_2021, utetemperatur_2021_2022, utetemperatur_2022_2023, utetemperatur_2023_2024)
    #with c2:
    st.write("**Måned (kWh)**")
    df = pd.DataFrame({f"{serie} 2020" : hour_to_month(timeserie_2020_2021), f"{serie} 2021" : hour_to_month(timeserie_2021_2022), f"{serie} 2022" : hour_to_month(timeserie_2022_2023), f"{serie} 2023" : hour_to_month(timeserie_2023_2024)})
    with chart_container(df, export_formats=["CSV"]):
        pass 
    if visualiser == True:
        mndplot("kWh", f"{serie} [kWh]", "#1d3c34", timeserie_2020_2021, timeserie_2021_2022, timeserie_2022_2023, timeserie_2023_2024, year=2023)
    #with c4:
    st.write("**Måned (kW)**")
    df = pd.DataFrame({"2020" : hour_to_month_max(timeserie_2020_2021), f"{serie} 2021" : hour_to_month_max(timeserie_2021_2022), f"{serie} 2022" : hour_to_month_max(timeserie_2022_2023), f"{serie} 2023" : hour_to_month_max(timeserie_2023_2024)})
    with chart_container(df, export_formats=["CSV"]):
        pass 
    if visualiser == True:
        mndplot_max("kW", f"{serie} [kW]", "#1d3c34", timeserie_2020_2021, timeserie_2021_2022, timeserie_2022_2023, timeserie_2023_2024, year=2023)
    #with c3:
    st.write("**Uke (kWh)**")
    df = pd.DataFrame({f"{serie} 2020" : hour_to_week(timeserie_2020_2021), f"{serie} 2021" : hour_to_week(timeserie_2021_2022), f"{serie} 2022" : hour_to_week(timeserie_2022_2023), "2023" : hour_to_week(timeserie_2023_2024)})
    with chart_container(df, export_formats=["CSV"]):
        pass 
    if visualiser == True:
        ukeplot("kWh", f"{serie} [kWh]", "#1d3c34", timeserie_2020_2021, timeserie_2021_2022, timeserie_2022_2023, timeserie_2023_2024, year=2023)
    
    #--
    st.write("**Verdi | Kostnader**")
    #c1, c2, c3 = st.columns(3)
    kostnad_2020_2021 = Kostnadsanalyse(timeserie_2020_2021, spotpris_2020_2021, leap_year=True).kostnad_start_timeserie
    kostnad_2021_2022 = Kostnadsanalyse(timeserie_2021_2022, spotpris_2021_2022, leap_year=False).kostnad_start_timeserie
    kostnad_2022_2023 = Kostnadsanalyse(timeserie_2022_2023, spotpris_2022_2023, leap_year=False).kostnad_start_timeserie
    kostnad_2023_2024 = Kostnadsanalyse(timeserie_2023_2024, spotpris_2023_2024, leap_year=False).kostnad_start_timeserie


    #-- plot kostnadsseries
    #with c1:
    st.markdown("**Time (kr)**")
    zeros = np.zeros(24)
    df = pd.DataFrame({f"{serie} 2020" : kostnad_2020_2021, f"{serie} 2021" : np.append(kostnad_2021_2022, zeros), f"{serie} 2022" : np.append(kostnad_2022_2023, zeros), f"{serie} 2023" : np.append(kostnad_2023_2024, zeros)})
    with chart_container(df, export_formats=["CSV"]):
        if visualiser == True:
            timeplot("kr", f"{serie} [kr]", "#FFC358", kostnad_2020_2021, kostnad_2021_2022, kostnad_2022_2023, kostnad_2023_2024)
        #with c2:
    st.write("**Måned (kr)**")
    df = pd.DataFrame({f"{serie} 2020" : hour_to_month(kostnad_2020_2021), f"{serie} 2021" : hour_to_month(kostnad_2021_2022), f"{serie} 2022" : hour_to_month(kostnad_2022_2023), f"{serie} 2023" : hour_to_month(kostnad_2023_2024)})
    st.write(f"2021: {int(np.sum(hour_to_month(kostnad_2021_2022)))}")
    st.write(f"2022: {int(np.sum(hour_to_month(kostnad_2022_2023)))}")
    with chart_container(df, export_formats=["CSV"]):
        pass
    if visualiser == True:
        mndplot("kr", f"{serie} [kr]", "#FFC358", kostnad_2020_2021, kostnad_2021_2022, kostnad_2022_2023, kostnad_2023_2024)
        #with c3:
    st.write("**Uke (kr)**")
    df = pd.DataFrame({f"{serie} 2020" : hour_to_week(kostnad_2020_2021), f"{serie} 2021" : hour_to_week(kostnad_2021_2022), f"{serie} 2022" : hour_to_week(kostnad_2022_2023), f"{serie} 2023" : hour_to_week(kostnad_2023_2024)})
    with chart_container(df, export_formats=["CSV"]):
        pass 
    if visualiser == True:
        ukeplot("kr", f"{serie} [kr]", "#FFC358", kostnad_2020_2021, kostnad_2021_2022, kostnad_2022_2023, kostnad_2023_2024)
    st.markdown("---")
    
def plot_alt(df):
    plot_serie("Geotermos", df)
    plot_serie("VP_levert", df)
    plot_serie("El_til_VP", df)
    plot_serie("Solceller", df)
    try:
        plot_serie("Solfanger", df)
    except:
        pass 
    plot_serie("Frikjøling", df)
    plot_serie("Fra luft, geotermos og brønner til VP", df)
    plot_serie("Behov for kjøpt el til VP", df)
    plot_serie("Overskudd solstrøm for salg", df)
    plot_serie("Varme levert til skolen", df)
    
def sorter_dataframe(selected_mode, df):
    if selected_mode != "Usortert":
        if selected_mode == "Lading":
            mode_1 = 0
            mode_2 = 2
        elif selected_mode == "Hvile":
            mode_1 = 0
            mode_2 = 1
        elif selected_mode == "Uttak":
            mode_1 = 1
            mode_2 = 2
        df.loc[df['Modus'] == mode_1] = 0
        df.loc[df['Modus'] == mode_2] = 0
    return df

def sorter_fyringssesong(selected_mode, df):
    if selected_mode == "Fyringssesong 2021/2022":
        mode_1 = 0
        mode_2 = 2
    elif selected_mode == "Fyringssesong 2022/2023":
        mode_1 = 0
        mode_2 = 1
    df.loc[df['Modus'] == mode_1] = 0
    df.loc[df['Modus'] == mode_2] = 0
    return df  
#--
@st.cache_resource(show_spinner=False)
def import_excel():
    return pd.read_excel("src/data/input/GeoTermos_Drammen_19.06.2023.xlsx")

st.title("Analyse GeoTermos")
df_original = import_excel()
df_original["Fra luft, geotermos og brønner til VP"] = np.where(df_original["VP_levert"] > 0, df_original["VP_levert"] - df_original["El_til_VP"], 0)
df_original["Behov for kjøpt el til VP"] = np.where((df_original["Fra luft, geotermos og brønner til VP"] > 0) & (df_original["El_til_VP"] > df_original["Solceller"]), df_original["El_til_VP"] - df_original["Solceller"], 0)
df_original["Overskudd solstrøm for salg"] = np.where((df_original["El_til_VP"] - df_original["Solceller"]) < 0, abs(df_original["El_til_VP"] - df_original["Solceller"]), 0)
df_original["Varme levert til skolen"] = df_original["Geotermos"] + df_original["El_til_VP"] + df_original["Solfanger"]
df_original.loc[df_original['VP_levert'] == 0, 'El_til_VP'] = 0

df_original_1 = df_original.copy()
df_original_2 = df_original.copy()
df_original_3 = df_original.copy()
df_original_4 = df_original.copy()

with st.expander("Data"):
    st.write(df_original)
    

if st.checkbox("Se alle serier"):
    with st.spinner("Lager plot ..."):  
        tab1, tab2, tab3, tab4 = st.tabs(["Uttak", "Lading", "Hvile", "Usortert"])
        with tab1:
            df = sorter_dataframe("Uttak", df_original_1)
            plot_alt(df)
        with tab2:
            df = sorter_dataframe("Lading", df_original_2)
            plot_alt(df)
        with tab3:
            df = sorter_dataframe("Hvile", df_original_3)
            plot_alt(df)
        with tab4:
            df = sorter_dataframe("Usortert", df_original_4)
            plot_alt(df)
#--
if st.checkbox("Se på en serie"):
    selected_serie = st.selectbox("Velg serie", options = df_original.columns, index = 3)
    tab1, tab2, tab3, tab4 = st.tabs(["Uttak", "Lading", "Hvile", "Usortert"])
    with tab1:
        df = sorter_dataframe("Uttak", df_original_1)
        plot_serie(selected_serie, df_original_1)
    with tab2:
        df = sorter_dataframe("Lading", df_original_2)
        plot_serie(selected_serie, df_original_2)
    with tab3:
        df = sorter_dataframe("Hvile", df_original_3)
        plot_serie(selected_serie, df_original_3)
    with tab4:
        df = sorter_dataframe("Usortert", df_original_4)
        plot_serie(selected_serie, df_original_4)
#--
if st.checkbox("Last ned data"):
    selected_serie = st.selectbox("Velg serie", options = df_original.columns, index = 3)
    tab1, tab2, tab3, tab4 = st.tabs(["Uttak", "Lading", "Hvile", "Usortert"])
    with tab1:
        df = sorter_dataframe("Uttak", df_original_1)
        plot_serie(selected_serie, df_original_1, False)
    with tab2:
        df = sorter_dataframe("Lading", df_original_2)
        plot_serie(selected_serie, df_original_2, False)
    with tab3:
        df = sorter_dataframe("Hvile", df_original_3)
        plot_serie(selected_serie, df_original_3, False)
    with tab4:
        df = sorter_dataframe("Usortert", df_original_4)
        plot_serie(selected_serie, df_original_4, False)

    
            
        #--
        #a = np.concatenate((kostnad_2020_2021, kostnad_2021_2022, kostnad_2022_2023, kostnad_2023_2024), axis=None)
        #st.bar_chart(a)

        #--
        #a = np.concatenate((hour_to_month(kostnad_2020_2021), hour_to_month(kostnad_2021_2022), hour_to_month(kostnad_2022_2023), hour_to_month(kostnad_2023_2024)), axis=None)
        #st.bar_chart(a)





        
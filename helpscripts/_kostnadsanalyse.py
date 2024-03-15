import numpy as np
import datetime

from _utils import month_to_hour

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
        this_location = pathlib.Path(__file__)
        df = pd.read_excel(this_location.parent /"spotpriser.xlsx", sheet_name=str(self.year))
        return df[self.region].to_numpy() / 1.25

    def _beregn_nettleie(self, el_timeserie):
        max_value = 0
        max_value_list = []
        day = 0
        kapasitetsledd_mapping = {
            1: 174.67,
            2: 202.67,
            3: 298.67,
            4: 546.67,
            5: 690.67,
            6: 850.67,
            7: 1282.67,
            8: 1986.67,
            9: 2626.67,
            10: 4226.67,
        }
        energiledd_day = 36.60 / 100  # kr/kWh
        energliedd_night = -9.60 / 100  # kr/kWh
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
import numpy as np

class EnergyCoverage:
    def __init__(self, energy_arr):
        self._energy_arr = energy_arr
        self.COVERAGE = 90
        self.COP = 3.5

    def _coverage_calculation(self):
        coverage = self.COVERAGE
        energy_arr = self._energy_arr
        energy_sum = np.sum(energy_arr)
        heat_pump_size = max(energy_arr)
        reduction = heat_pump_size / 600
        calculated_coverage = 100.5
        if coverage != 100:
            while (calculated_coverage / coverage) > 1:
                tmp_list = np.zeros (8760)
                for i, effect in enumerate(energy_arr):
                    if effect > heat_pump_size:
                        tmp_list[i] = heat_pump_size
                    else:
                        tmp_list[i] = effect
                calculated_coverage = (sum(tmp_list) / energy_sum) * 100
                heat_pump_size -= reduction
        else:
            tmp_list = energy_arr
            heat_pump_size = max(energy_arr)
        self.covered_arr = np.array(tmp_list)
        self.heat_pump_size = float("{:.1f}".format(heat_pump_size))
        self.non_covered_arr = energy_arr - self.covered_arr

    def _geoenergy_cop_calculation(self):
        self.gshp_delivered_arr = self.covered_arr - self.covered_arr / self.COP
        self.gshp_compressor_arr = self.covered_arr - self.gshp_delivered_arr



    

    


import streamlit as st 
import numpy as np
import numpy_financial as npf
import altair as alt
import pandas as pd
from old_helpscripts._utils import hour_to_month, render_svg
from old_helpscripts._energy_coverage import EnergyCoverage

class Costs():
    def __init__(self):
        self.METERS = 500
        self.ELPRICE = 1
        self.LIFETIME = 25
        self.DISKONTERINGSRENTE = 0.06
        self.gshp_compressor_arr = np.zeros(8760)
        self.non_covered_arr = np.zeros(8760)
        self.demand_arr = np.zeros(8760)
        self.heat_pump_size = 20
        self.maintenance_cost = 10000

    def _run_cost_calculation(self):
        self._calculate_energy_cost()
        self._calculate_investment_cost()
        self._calculate_operation_cost()

        self._npv()

    def _calculate_investment_cost(self):
        #-- Veldig enkelt
        PRICE_PER_METER = 329.19
        HEAT_PUMP_CONSTANT_COST = 12927
        self.investment_heat_pump = int(round((self.heat_pump_size * HEAT_PUMP_CONSTANT_COST),0))
        self.investment_well = int(round((PRICE_PER_METER * self.METERS)/0.6,2))
        self.investment_cost = int(round(self.investment_well + self.investment_heat_pump,0))  
        #-- 

    def _calculate_energy_cost(self):
        self.energy_cost = int(round(np.sum(self.demand_arr * self.ELPRICE,0)))

    def _calculate_operation_cost(self):
        self.operation_cost = int(round(np.sum(((self.gshp_compressor_arr + self.non_covered_arr) * self.ELPRICE)),0))


    def _npv(self):
        self.npv_maintenance = -npf.pv(self.DISKONTERINGSRENTE, self.LIFETIME, self.maintenance_cost)
        self.npv_operation = -npf.pv(self.DISKONTERINGSRENTE, self.LIFETIME, self.operation_cost)
        self.npv_energy = -npf.pv(self.DISKONTERINGSRENTE, self.LIFETIME, self.energy_cost)

        self.LCOE = round(((self.npv_maintenance + self.npv_operation + self.npv_energy) / self.investment_cost),2)




class Costs1:
    def __init__(self, meters):
        self.METER = meters
        self.PRICE_PER_METER = 365
        self.INVESTMENT = (self.METER * self.PRICE_PER_METER) / 0.6
        self.INTEREST = 1.0
        self.ELPRICE_ARR = 1.0
        self.PAYMENT_TIME = 20
        self.YEARS = 20

    def _calculate_monthly_costs(self, demand_arr, compressor_arr, peak_arr, INVESTMENT):
        instalment = 0
        if INVESTMENT != 0:
            NUMBER_OF_MONTHS = self.PAYMENT_TIME * 12
            MONTHLY_INTEREST = (self.INTEREST/100) / 12
            if MONTHLY_INTEREST > 0:
                instalment = INVESTMENT / ((1 - (1 / (1 + MONTHLY_INTEREST) ** NUMBER_OF_MONTHS)) / MONTHLY_INTEREST)
            else:
                instalment = INVESTMENT / NUMBER_OF_MONTHS
        el_cost_hourly = demand_arr * self.ELPRICE_ARR
        gshp_cost_hourly = (compressor_arr + peak_arr) * self.ELPRICE_ARR
        self.el_cost_monthly = np.array(hour_to_month(el_cost_hourly))
        self.gshp_cost_monthly = np.array(hour_to_month(gshp_cost_hourly)) + instalment
        self.el_cost_sum = np.sum(self.el_cost_monthly)
        self.gshp_cost_sum = np.sum(self.gshp_cost_monthly)
        self.savings_sum = self.el_cost_sum - self.gshp_cost_sum

    def _show_operation_costs(self):
        investment = int(round(self.INVESTMENT, -1))
        operation_saving = int(round(self.savings_sum, -1))
        total_saving = int(round(self.savings_sum * self.YEARS - self.INVESTMENT,-1))
        self.total_saving = total_saving
        c1, c2, c3 = st.columns(3)
        with c1:
            svg = """ <svg width="26" height="35" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" overflow="hidden"><defs><clipPath id="clip0"><rect x="369" y="79" width="26" height="27"/></clipPath></defs><g clip-path="url(#clip0)" transform="translate(-369 -79)"><path d="M25.4011 12.9974C25.4011 19.8478 19.8478 25.4011 12.9974 25.4011 6.14699 25.4011 0.593654 19.8478 0.593654 12.9974 0.593654 6.14699 6.14699 0.593654 12.9974 0.593654 19.8478 0.593654 25.4011 6.14699 25.4011 12.9974Z" stroke="#1E3D35" stroke-width="0.757136" stroke-miterlimit="10" fill="#FBFDF6" transform="matrix(1 0 0 1.03846 369 79)"/><path d="M16.7905 6.98727 11.8101 19.0075 11.6997 19.0075 9.20954 12.9974" stroke="#1E3D35" stroke-width="0.757136" stroke-linejoin="round" fill="none" transform="matrix(1 0 0 1.03846 369 79)"/></g></svg>"""
            render_svg(svg)
            st.metric(label="Estimert investeringskostnad", value= f"{investment:,} kr".replace(',', ' '))
        with c2:
            svg = """ <svg width="29" height="35" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" overflow="hidden"><defs><clipPath id="clip0"><rect x="323" y="79" width="29" height="27"/></clipPath></defs><g clip-path="url(#clip0)" transform="translate(-323 -79)"><path d="M102.292 91.6051C102.292 91.6051 102.831 89.8359 111.221 89.8359 120.549 89.8359 120.01 91.6051 120.01 91.6051L120.01 107.574C120.01 107.574 120.523 109.349 111.221 109.349 102.831 109.349 102.292 107.574 102.292 107.574Z" stroke="#1E3D35" stroke-width="0.512821" stroke-miterlimit="10" fill="#F0F3E3" transform="matrix(1 0 0 1.02056 231.728 -12.3976)"/><path d="M102.292 94.7128C102.292 94.7128 102.831 96.4872 111.221 96.4872 120.549 96.4872 120.01 94.7128 120.01 94.7128" stroke="#1E3D35" stroke-width="0.512821" stroke-miterlimit="10" fill="#F0F3E3" transform="matrix(1 0 0 1.02056 231.728 -12.3976)"/><path d="M102.292 97.9487C102.292 97.9487 102.831 99.718 111.221 99.718 120.549 99.718 120 97.9487 120 97.9487" stroke="#1E3D35" stroke-width="0.512821" stroke-miterlimit="10" fill="#F0F3E3" transform="matrix(1 0 0 1.02056 231.728 -12.3976)"/><path d="M102.292 101.19C102.292 101.19 102.831 102.964 111.221 102.964 120.549 102.964 120.01 101.19 120.01 101.19" stroke="#1E3D35" stroke-width="0.512821" stroke-miterlimit="10" fill="#F0F3E3" transform="matrix(1 0 0 1.02056 231.728 -12.3976)"/><path d="M102.292 104.385C102.292 104.385 102.831 106.154 111.221 106.154 120.549 106.154 120.01 104.385 120.01 104.385" stroke="#1E3D35" stroke-width="0.512821" stroke-miterlimit="10" fill="#F0F3E3" transform="matrix(1 0 0 1.02056 231.728 -12.3976)"/><path d="M120 91.6051C120 91.6051 120.513 93.3795 111.21 93.3795 102.821 93.3795 102.282 91.6051 102.282 91.6051" stroke="#1E3D35" stroke-width="0.512821" stroke-miterlimit="10" fill="#F0F3E3" transform="matrix(1 0 0 1.02056 231.728 -12.3976)"/><path d="M19.0769 16.7436C19.0769 21.9407 14.8638 26.1538 9.66667 26.1538 4.46953 26.1538 0.25641 21.9407 0.25641 16.7436 0.25641 11.5465 4.46953 7.33333 9.66667 7.33333 14.8638 7.33333 19.0769 11.5464 19.0769 16.7436Z" stroke="#1E3D35" stroke-width="0.512821" stroke-miterlimit="10" fill="#F0F3E3" transform="matrix(1 0 0 1.02056 323 79.0234)"/><path d="M9.66667 11.6 11.4564 15.9231 15.1487 14.5744 14.4513 19.3231 4.88205 19.3231 4.18462 14.5744 7.87692 15.9231 9.66667 11.6Z" stroke="#1E3D35" stroke-width="0.512821" stroke-linecap="round" stroke-linejoin="round" fill="#F0F3E3" transform="matrix(1 0 0 1.02056 323 79.0234)"/><path d="M4.86667 20.3846 14.5231 20.3846" stroke="#1E3D35" stroke-width="0.512821" stroke-linecap="round" stroke-linejoin="round" fill="none" transform="matrix(1 0 0 1.02056 323 79.0234)"/></g></svg>"""
            render_svg(svg)
            st.metric(label="Reduserte utgifter til oppvarming", value= f"{operation_saving:,} kr/år".replace(',', ' '))
        with c3:
            svg = """ <svg width="29" height="35" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" overflow="hidden"><defs><clipPath id="clip0"><rect x="323" y="79" width="29" height="27"/></clipPath></defs><g clip-path="url(#clip0)" transform="translate(-323 -79)"><path d="M102.292 91.6051C102.292 91.6051 102.831 89.8359 111.221 89.8359 120.549 89.8359 120.01 91.6051 120.01 91.6051L120.01 107.574C120.01 107.574 120.523 109.349 111.221 109.349 102.831 109.349 102.292 107.574 102.292 107.574Z" stroke="#1E3D35" stroke-width="0.512821" stroke-miterlimit="10" fill="#F0F3E3" transform="matrix(1 0 0 1.02056 231.728 -12.3976)"/><path d="M102.292 94.7128C102.292 94.7128 102.831 96.4872 111.221 96.4872 120.549 96.4872 120.01 94.7128 120.01 94.7128" stroke="#1E3D35" stroke-width="0.512821" stroke-miterlimit="10" fill="#F0F3E3" transform="matrix(1 0 0 1.02056 231.728 -12.3976)"/><path d="M102.292 97.9487C102.292 97.9487 102.831 99.718 111.221 99.718 120.549 99.718 120 97.9487 120 97.9487" stroke="#1E3D35" stroke-width="0.512821" stroke-miterlimit="10" fill="#F0F3E3" transform="matrix(1 0 0 1.02056 231.728 -12.3976)"/><path d="M102.292 101.19C102.292 101.19 102.831 102.964 111.221 102.964 120.549 102.964 120.01 101.19 120.01 101.19" stroke="#1E3D35" stroke-width="0.512821" stroke-miterlimit="10" fill="#F0F3E3" transform="matrix(1 0 0 1.02056 231.728 -12.3976)"/><path d="M102.292 104.385C102.292 104.385 102.831 106.154 111.221 106.154 120.549 106.154 120.01 104.385 120.01 104.385" stroke="#1E3D35" stroke-width="0.512821" stroke-miterlimit="10" fill="#F0F3E3" transform="matrix(1 0 0 1.02056 231.728 -12.3976)"/><path d="M120 91.6051C120 91.6051 120.513 93.3795 111.21 93.3795 102.821 93.3795 102.282 91.6051 102.282 91.6051" stroke="#1E3D35" stroke-width="0.512821" stroke-miterlimit="10" fill="#F0F3E3" transform="matrix(1 0 0 1.02056 231.728 -12.3976)"/><path d="M19.0769 16.7436C19.0769 21.9407 14.8638 26.1538 9.66667 26.1538 4.46953 26.1538 0.25641 21.9407 0.25641 16.7436 0.25641 11.5465 4.46953 7.33333 9.66667 7.33333 14.8638 7.33333 19.0769 11.5464 19.0769 16.7436Z" stroke="#1E3D35" stroke-width="0.512821" stroke-miterlimit="10" fill="#F0F3E3" transform="matrix(1 0 0 1.02056 323 79.0234)"/><path d="M9.66667 11.6 11.4564 15.9231 15.1487 14.5744 14.4513 19.3231 4.88205 19.3231 4.18462 14.5744 7.87692 15.9231 9.66667 11.6Z" stroke="#1E3D35" stroke-width="0.512821" stroke-linecap="round" stroke-linejoin="round" fill="#F0F3E3" transform="matrix(1 0 0 1.02056 323 79.0234)"/><path d="M4.86667 20.3846 14.5231 20.3846" stroke="#1E3D35" stroke-width="0.512821" stroke-linecap="round" stroke-linejoin="round" fill="none" transform="matrix(1 0 0 1.02056 323 79.0234)"/></g></svg>"""
            render_svg(svg)
            st.metric(label="Samlet besparelse etter 20 år", value = f"{total_saving:,} kr".replace(',', ' '))

    def _show_operation_and_investment_costs(self):
        investment = int(round(self.INVESTMENT, -1))
        savings1 = int(round(self.savings_sum, -1))
        savings2 = int(round(self.savings_sum * self.YEARS, -1))
        c1, c2, c3 = st.columns(3)
        with c1:
            svg = """ <svg width="26" height="35" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" overflow="hidden"><defs><clipPath id="clip0"><rect x="369" y="79" width="26" height="27"/></clipPath></defs><g clip-path="url(#clip0)" transform="translate(-369 -79)"><path d="M25.4011 12.9974C25.4011 19.8478 19.8478 25.4011 12.9974 25.4011 6.14699 25.4011 0.593654 19.8478 0.593654 12.9974 0.593654 6.14699 6.14699 0.593654 12.9974 0.593654 19.8478 0.593654 25.4011 6.14699 25.4011 12.9974Z" stroke="#1E3D35" stroke-width="0.757136" stroke-miterlimit="10" fill="#FBFDF6" transform="matrix(1 0 0 1.03846 369 79)"/><path d="M16.7905 6.98727 11.8101 19.0075 11.6997 19.0075 9.20954 12.9974" stroke="#1E3D35" stroke-width="0.757136" stroke-linejoin="round" fill="none" transform="matrix(1 0 0 1.03846 369 79)"/></g></svg>"""
            render_svg(svg)
            st.metric(label="Investeringskostnad", value= f"{0:,} kr".replace(',', ' '))
        with c2:
            svg = """ <svg width="29" height="35" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" overflow="hidden"><defs><clipPath id="clip0"><rect x="323" y="79" width="29" height="27"/></clipPath></defs><g clip-path="url(#clip0)" transform="translate(-323 -79)"><path d="M102.292 91.6051C102.292 91.6051 102.831 89.8359 111.221 89.8359 120.549 89.8359 120.01 91.6051 120.01 91.6051L120.01 107.574C120.01 107.574 120.523 109.349 111.221 109.349 102.831 109.349 102.292 107.574 102.292 107.574Z" stroke="#1E3D35" stroke-width="0.512821" stroke-miterlimit="10" fill="#F0F3E3" transform="matrix(1 0 0 1.02056 231.728 -12.3976)"/><path d="M102.292 94.7128C102.292 94.7128 102.831 96.4872 111.221 96.4872 120.549 96.4872 120.01 94.7128 120.01 94.7128" stroke="#1E3D35" stroke-width="0.512821" stroke-miterlimit="10" fill="#F0F3E3" transform="matrix(1 0 0 1.02056 231.728 -12.3976)"/><path d="M102.292 97.9487C102.292 97.9487 102.831 99.718 111.221 99.718 120.549 99.718 120 97.9487 120 97.9487" stroke="#1E3D35" stroke-width="0.512821" stroke-miterlimit="10" fill="#F0F3E3" transform="matrix(1 0 0 1.02056 231.728 -12.3976)"/><path d="M102.292 101.19C102.292 101.19 102.831 102.964 111.221 102.964 120.549 102.964 120.01 101.19 120.01 101.19" stroke="#1E3D35" stroke-width="0.512821" stroke-miterlimit="10" fill="#F0F3E3" transform="matrix(1 0 0 1.02056 231.728 -12.3976)"/><path d="M102.292 104.385C102.292 104.385 102.831 106.154 111.221 106.154 120.549 106.154 120.01 104.385 120.01 104.385" stroke="#1E3D35" stroke-width="0.512821" stroke-miterlimit="10" fill="#F0F3E3" transform="matrix(1 0 0 1.02056 231.728 -12.3976)"/><path d="M120 91.6051C120 91.6051 120.513 93.3795 111.21 93.3795 102.821 93.3795 102.282 91.6051 102.282 91.6051" stroke="#1E3D35" stroke-width="0.512821" stroke-miterlimit="10" fill="#F0F3E3" transform="matrix(1 0 0 1.02056 231.728 -12.3976)"/><path d="M19.0769 16.7436C19.0769 21.9407 14.8638 26.1538 9.66667 26.1538 4.46953 26.1538 0.25641 21.9407 0.25641 16.7436 0.25641 11.5465 4.46953 7.33333 9.66667 7.33333 14.8638 7.33333 19.0769 11.5464 19.0769 16.7436Z" stroke="#1E3D35" stroke-width="0.512821" stroke-miterlimit="10" fill="#F0F3E3" transform="matrix(1 0 0 1.02056 323 79.0234)"/><path d="M9.66667 11.6 11.4564 15.9231 15.1487 14.5744 14.4513 19.3231 4.88205 19.3231 4.18462 14.5744 7.87692 15.9231 9.66667 11.6Z" stroke="#1E3D35" stroke-width="0.512821" stroke-linecap="round" stroke-linejoin="round" fill="#F0F3E3" transform="matrix(1 0 0 1.02056 323 79.0234)"/><path d="M4.86667 20.3846 14.5231 20.3846" stroke="#1E3D35" stroke-width="0.512821" stroke-linecap="round" stroke-linejoin="round" fill="none" transform="matrix(1 0 0 1.02056 323 79.0234)"/></g></svg>"""
            render_svg(svg)
            st.metric(label="Reduserte utgifter til oppvarming", value= f"{savings1:,} kr/år".replace(',', ' '))
        with c3:
            svg = """ <svg width="29" height="35" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" overflow="hidden"><defs><clipPath id="clip0"><rect x="323" y="79" width="29" height="27"/></clipPath></defs><g clip-path="url(#clip0)" transform="translate(-323 -79)"><path d="M102.292 91.6051C102.292 91.6051 102.831 89.8359 111.221 89.8359 120.549 89.8359 120.01 91.6051 120.01 91.6051L120.01 107.574C120.01 107.574 120.523 109.349 111.221 109.349 102.831 109.349 102.292 107.574 102.292 107.574Z" stroke="#1E3D35" stroke-width="0.512821" stroke-miterlimit="10" fill="#F0F3E3" transform="matrix(1 0 0 1.02056 231.728 -12.3976)"/><path d="M102.292 94.7128C102.292 94.7128 102.831 96.4872 111.221 96.4872 120.549 96.4872 120.01 94.7128 120.01 94.7128" stroke="#1E3D35" stroke-width="0.512821" stroke-miterlimit="10" fill="#F0F3E3" transform="matrix(1 0 0 1.02056 231.728 -12.3976)"/><path d="M102.292 97.9487C102.292 97.9487 102.831 99.718 111.221 99.718 120.549 99.718 120 97.9487 120 97.9487" stroke="#1E3D35" stroke-width="0.512821" stroke-miterlimit="10" fill="#F0F3E3" transform="matrix(1 0 0 1.02056 231.728 -12.3976)"/><path d="M102.292 101.19C102.292 101.19 102.831 102.964 111.221 102.964 120.549 102.964 120.01 101.19 120.01 101.19" stroke="#1E3D35" stroke-width="0.512821" stroke-miterlimit="10" fill="#F0F3E3" transform="matrix(1 0 0 1.02056 231.728 -12.3976)"/><path d="M102.292 104.385C102.292 104.385 102.831 106.154 111.221 106.154 120.549 106.154 120.01 104.385 120.01 104.385" stroke="#1E3D35" stroke-width="0.512821" stroke-miterlimit="10" fill="#F0F3E3" transform="matrix(1 0 0 1.02056 231.728 -12.3976)"/><path d="M120 91.6051C120 91.6051 120.513 93.3795 111.21 93.3795 102.821 93.3795 102.282 91.6051 102.282 91.6051" stroke="#1E3D35" stroke-width="0.512821" stroke-miterlimit="10" fill="#F0F3E3" transform="matrix(1 0 0 1.02056 231.728 -12.3976)"/><path d="M19.0769 16.7436C19.0769 21.9407 14.8638 26.1538 9.66667 26.1538 4.46953 26.1538 0.25641 21.9407 0.25641 16.7436 0.25641 11.5465 4.46953 7.33333 9.66667 7.33333 14.8638 7.33333 19.0769 11.5464 19.0769 16.7436Z" stroke="#1E3D35" stroke-width="0.512821" stroke-miterlimit="10" fill="#F0F3E3" transform="matrix(1 0 0 1.02056 323 79.0234)"/><path d="M9.66667 11.6 11.4564 15.9231 15.1487 14.5744 14.4513 19.3231 4.88205 19.3231 4.18462 14.5744 7.87692 15.9231 9.66667 11.6Z" stroke="#1E3D35" stroke-width="0.512821" stroke-linecap="round" stroke-linejoin="round" fill="#F0F3E3" transform="matrix(1 0 0 1.02056 323 79.0234)"/><path d="M4.86667 20.3846 14.5231 20.3846" stroke="#1E3D35" stroke-width="0.512821" stroke-linecap="round" stroke-linejoin="round" fill="none" transform="matrix(1 0 0 1.02056 323 79.0234)"/></g></svg>"""
            render_svg(svg)
            st.metric(label="Samlet besparelse etter 20 år", value = f"{savings2:,} kr".replace(',', ' '))

    def plot(self, kostnad):
        gshp_text_1 = "Bergvarme"        
        gshp_text_2 = f"{kostnad}: " + str(int(round(self.gshp_cost_sum, -1))) + " kr/år"
        el_text_1 = "Elektrisk oppvarming"
        el_text_2 = f"{kostnad}: " + str(int(round(self.el_cost_sum, -1))) + " kr/år"
        
        months = ['jan', 'feb', 'mar', 'apr', 'mai', 'jun', 'jul', 'aug', 'sep', 'okt', 'nov', 'des']
        wide_form = pd.DataFrame({
            'Måneder' : months,
            gshp_text_1 : self.gshp_cost_monthly, 
            el_text_1 : self.el_cost_monthly})

        c1 = alt.Chart(wide_form).transform_fold(
            [gshp_text_1, el_text_1],
            as_=['key', 'Kostnader (kr)']).mark_bar(opacity=1).encode(
                x=alt.X('Måneder:N', sort=months, title=None),
                y=alt.Y('Kostnader (kr):Q',stack=None),
                color=alt.Color('key:N', scale=alt.Scale(domain=[gshp_text_1], 
                range=['#48a23f']), legend=alt.Legend(orient='top', 
                direction='vertical', title=gshp_text_2))).configure_view(strokeWidth=0)

        c2 = alt.Chart(wide_form).transform_fold(
            [gshp_text_1, el_text_1],
            as_=['key', 'Kostnader (kr)']).mark_bar(opacity=1).encode(
                x=alt.X('Måneder:N', sort=months, title=None),
                y=alt.Y('Kostnader (kr):Q',stack=None, title=None),
                color=alt.Color('key:N', scale=alt.Scale(domain=[el_text_1], 
                range=['#880808']), legend=alt.Legend(orient='top', 
                direction='vertical', title=el_text_2))).configure_view(strokeWidth=0)

        col1, col2 = st.columns(2)
        with col1:
            st.altair_chart(c1, use_container_width=True)  
        with col2:
            st.altair_chart(c2, use_container_width=True) 
             
    def operation_and_investment_show(self):
        investment = int(round(self.investment, -1))
        savings1 = int(round(self.savings_sum, -1))
        savings2 = int(round(self.savings_sum*20, -1))
        c1, c2, c3 = st.columns(3)
        with c1:
            svg = """ <svg width="26" height="35" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" overflow="hidden"><defs><clipPath id="clip0"><rect x="369" y="79" width="26" height="27"/></clipPath></defs><g clip-path="url(#clip0)" transform="translate(-369 -79)"><path d="M25.4011 12.9974C25.4011 19.8478 19.8478 25.4011 12.9974 25.4011 6.14699 25.4011 0.593654 19.8478 0.593654 12.9974 0.593654 6.14699 6.14699 0.593654 12.9974 0.593654 19.8478 0.593654 25.4011 6.14699 25.4011 12.9974Z" stroke="#1E3D35" stroke-width="0.757136" stroke-miterlimit="10" fill="#FBFDF6" transform="matrix(1 0 0 1.03846 369 79)"/><path d="M16.7905 6.98727 11.8101 19.0075 11.6997 19.0075 9.20954 12.9974" stroke="#1E3D35" stroke-width="0.757136" stroke-linejoin="round" fill="none" transform="matrix(1 0 0 1.03846 369 79)"/></g></svg>"""
            render_svg(svg)
            st.metric(label="Investeringskostnad", value= f"{0:,} kr".replace(',', ' '))
        with c2:
            svg = """ <svg width="29" height="35" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" overflow="hidden"><defs><clipPath id="clip0"><rect x="323" y="79" width="29" height="27"/></clipPath></defs><g clip-path="url(#clip0)" transform="translate(-323 -79)"><path d="M102.292 91.6051C102.292 91.6051 102.831 89.8359 111.221 89.8359 120.549 89.8359 120.01 91.6051 120.01 91.6051L120.01 107.574C120.01 107.574 120.523 109.349 111.221 109.349 102.831 109.349 102.292 107.574 102.292 107.574Z" stroke="#1E3D35" stroke-width="0.512821" stroke-miterlimit="10" fill="#F0F3E3" transform="matrix(1 0 0 1.02056 231.728 -12.3976)"/><path d="M102.292 94.7128C102.292 94.7128 102.831 96.4872 111.221 96.4872 120.549 96.4872 120.01 94.7128 120.01 94.7128" stroke="#1E3D35" stroke-width="0.512821" stroke-miterlimit="10" fill="#F0F3E3" transform="matrix(1 0 0 1.02056 231.728 -12.3976)"/><path d="M102.292 97.9487C102.292 97.9487 102.831 99.718 111.221 99.718 120.549 99.718 120 97.9487 120 97.9487" stroke="#1E3D35" stroke-width="0.512821" stroke-miterlimit="10" fill="#F0F3E3" transform="matrix(1 0 0 1.02056 231.728 -12.3976)"/><path d="M102.292 101.19C102.292 101.19 102.831 102.964 111.221 102.964 120.549 102.964 120.01 101.19 120.01 101.19" stroke="#1E3D35" stroke-width="0.512821" stroke-miterlimit="10" fill="#F0F3E3" transform="matrix(1 0 0 1.02056 231.728 -12.3976)"/><path d="M102.292 104.385C102.292 104.385 102.831 106.154 111.221 106.154 120.549 106.154 120.01 104.385 120.01 104.385" stroke="#1E3D35" stroke-width="0.512821" stroke-miterlimit="10" fill="#F0F3E3" transform="matrix(1 0 0 1.02056 231.728 -12.3976)"/><path d="M120 91.6051C120 91.6051 120.513 93.3795 111.21 93.3795 102.821 93.3795 102.282 91.6051 102.282 91.6051" stroke="#1E3D35" stroke-width="0.512821" stroke-miterlimit="10" fill="#F0F3E3" transform="matrix(1 0 0 1.02056 231.728 -12.3976)"/><path d="M19.0769 16.7436C19.0769 21.9407 14.8638 26.1538 9.66667 26.1538 4.46953 26.1538 0.25641 21.9407 0.25641 16.7436 0.25641 11.5465 4.46953 7.33333 9.66667 7.33333 14.8638 7.33333 19.0769 11.5464 19.0769 16.7436Z" stroke="#1E3D35" stroke-width="0.512821" stroke-miterlimit="10" fill="#F0F3E3" transform="matrix(1 0 0 1.02056 323 79.0234)"/><path d="M9.66667 11.6 11.4564 15.9231 15.1487 14.5744 14.4513 19.3231 4.88205 19.3231 4.18462 14.5744 7.87692 15.9231 9.66667 11.6Z" stroke="#1E3D35" stroke-width="0.512821" stroke-linecap="round" stroke-linejoin="round" fill="#F0F3E3" transform="matrix(1 0 0 1.02056 323 79.0234)"/><path d="M4.86667 20.3846 14.5231 20.3846" stroke="#1E3D35" stroke-width="0.512821" stroke-linecap="round" stroke-linejoin="round" fill="none" transform="matrix(1 0 0 1.02056 323 79.0234)"/></g></svg>"""
            render_svg(svg)
            st.metric(label="Reduserte utgifter til oppvarming", value= f"{savings1:,} kr/år".replace(',', ' '))
        with c3:
            svg = """ <svg width="29" height="35" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" overflow="hidden"><defs><clipPath id="clip0"><rect x="323" y="79" width="29" height="27"/></clipPath></defs><g clip-path="url(#clip0)" transform="translate(-323 -79)"><path d="M102.292 91.6051C102.292 91.6051 102.831 89.8359 111.221 89.8359 120.549 89.8359 120.01 91.6051 120.01 91.6051L120.01 107.574C120.01 107.574 120.523 109.349 111.221 109.349 102.831 109.349 102.292 107.574 102.292 107.574Z" stroke="#1E3D35" stroke-width="0.512821" stroke-miterlimit="10" fill="#F0F3E3" transform="matrix(1 0 0 1.02056 231.728 -12.3976)"/><path d="M102.292 94.7128C102.292 94.7128 102.831 96.4872 111.221 96.4872 120.549 96.4872 120.01 94.7128 120.01 94.7128" stroke="#1E3D35" stroke-width="0.512821" stroke-miterlimit="10" fill="#F0F3E3" transform="matrix(1 0 0 1.02056 231.728 -12.3976)"/><path d="M102.292 97.9487C102.292 97.9487 102.831 99.718 111.221 99.718 120.549 99.718 120 97.9487 120 97.9487" stroke="#1E3D35" stroke-width="0.512821" stroke-miterlimit="10" fill="#F0F3E3" transform="matrix(1 0 0 1.02056 231.728 -12.3976)"/><path d="M102.292 101.19C102.292 101.19 102.831 102.964 111.221 102.964 120.549 102.964 120.01 101.19 120.01 101.19" stroke="#1E3D35" stroke-width="0.512821" stroke-miterlimit="10" fill="#F0F3E3" transform="matrix(1 0 0 1.02056 231.728 -12.3976)"/><path d="M102.292 104.385C102.292 104.385 102.831 106.154 111.221 106.154 120.549 106.154 120.01 104.385 120.01 104.385" stroke="#1E3D35" stroke-width="0.512821" stroke-miterlimit="10" fill="#F0F3E3" transform="matrix(1 0 0 1.02056 231.728 -12.3976)"/><path d="M120 91.6051C120 91.6051 120.513 93.3795 111.21 93.3795 102.821 93.3795 102.282 91.6051 102.282 91.6051" stroke="#1E3D35" stroke-width="0.512821" stroke-miterlimit="10" fill="#F0F3E3" transform="matrix(1 0 0 1.02056 231.728 -12.3976)"/><path d="M19.0769 16.7436C19.0769 21.9407 14.8638 26.1538 9.66667 26.1538 4.46953 26.1538 0.25641 21.9407 0.25641 16.7436 0.25641 11.5465 4.46953 7.33333 9.66667 7.33333 14.8638 7.33333 19.0769 11.5464 19.0769 16.7436Z" stroke="#1E3D35" stroke-width="0.512821" stroke-miterlimit="10" fill="#F0F3E3" transform="matrix(1 0 0 1.02056 323 79.0234)"/><path d="M9.66667 11.6 11.4564 15.9231 15.1487 14.5744 14.4513 19.3231 4.88205 19.3231 4.18462 14.5744 7.87692 15.9231 9.66667 11.6Z" stroke="#1E3D35" stroke-width="0.512821" stroke-linecap="round" stroke-linejoin="round" fill="#F0F3E3" transform="matrix(1 0 0 1.02056 323 79.0234)"/><path d="M4.86667 20.3846 14.5231 20.3846" stroke="#1E3D35" stroke-width="0.512821" stroke-linecap="round" stroke-linejoin="round" fill="none" transform="matrix(1 0 0 1.02056 323 79.0234)"/></g></svg>"""
            render_svg(svg)
            st.metric(label="Samlet besparelse etter 20 år", value = f"{savings2:,} kr".replace(',', ' '))

    def operation_and_investment_after(self):

        st.write(f""" Mange banker har begynt å tilby billigere boliglån hvis boligen regnes som miljøvennlig; et såkalt grønt boliglån. 
        En oppgradering til bergvarme kan kvalifisere boligen din til et slikt lån. """)

        st.write(f""" Søylediagrammene viser årlige kostnader til oppvarming hvis investeringen finansieres 
        av et grønt lån. Her har vi forutsatt at investeringen nedbetales i 
        løpet av {self.payment_time} år med effektiv rente på {round(self.interest,2)} %. Du kan endre betingelsene for lånet 
        i menyen til venstre.""")

    def investment_show(self):
        st.subheader("Investeringskostnad") 
        st.write(""" Investeringskostnaden omfatter en komplett installsjon av 
        bergvarme inkl. varmepumpe, montering og energibrønn. 
        Merk at dette er et estimat, og endelig pris må fastsettes av forhandler. """)
        st.metric(label="Investeringskostnad", value=(str(int(round(self.investment, -1))) + " kr"))

    def profitibality_operation_and_investment(self):
        if self.savings_sum < 0:
            st.warning("Bergvarme er ikke lønnsomt etter 20 år med valgte betingelser for lånefinansiering.", icon="⚠️")
            #st.stop()

    def profitibality_operation(self):
        if self.total_saving < 0:
            st.warning("Bergvarme er ikke lønnsomt etter 20 år med valgte forutsetninger for direkte kjøp.", icon="⚠️")
            st.stop()
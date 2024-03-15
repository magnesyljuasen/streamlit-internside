import requests
import streamlit.components.v1 as components
import streamlit as st
import requests
from datetime import date
import numpy as np
import pandas as pd
import altair as alt
import base64
from deta import Deta
from matplotlib.ticker import StrMethodFormatter, FuncFormatter


import matplotlib.pyplot as plt
import matplotlib as mpl
from cycler import cycler
import matplotlib.dates as mdates
plt.rcParams["figure.figsize"] = (10,5)

#  Sum av negative tall i en liste
def negative_sum(array):
    sum_value = 0
    max_value = 0
    for index, value in enumerate(array):
        if value < 0:
            sum_value += (-value)
        if (-value) > max_value:
            max_value = (-value)
    return int(round(sum_value,0)), int(round(max_value,0))

#  Hjelpefunksjon - Render SVG
def render_svg(svg):
    b64 = base64.b64encode(svg.encode('utf-8')).decode("utf-8")
    html = r'<img src="data:image/svg+xml;base64,%s"/>' % b64
    st.write(html, unsafe_allow_html=True)


#  Hjelpefunksjon - Fra timeserie til månedlig
def hour_to_month(hourly_array):
    monthly_array = []
    summed = 0
    for i in range(0, len(hourly_array)):
        verdi = hourly_array[i]
        if np.isnan(verdi):
            verdi = 0
        summed = verdi + summed
        if i == 744 or i == 1416 or i == 2160 or i == 2880 \
                or i == 3624 or i == 4344 or i == 5088 or i == 5832 \
                or i == 6552 or i == 7296 or i == 8016 or i == 8759:
            monthly_array.append(int(summed))
            summed = 0
    return monthly_array 


#  Hjelpefunksjon - Load Lottie
def load_lottie(url: str):
    r = requests.get(url)
    if r.status_code!= 200:
        return None
    return r.json()


#  Hjelpeklasse - Twitter
class Tweet(object):
    def __init__(self, s, embed_str=False):
        if not embed_str:
            # Use Twitter's oEmbed API
            # https://dev.twitter.com/web/embedded-tweets
            api = "https://publish.twitter.com/oembed?url={}".format(s)
            response = requests.get(api)
            self.text = response.json()["html"]
        else:
            self.text = s#

    def _repr_html_(self):
        return self.text

    def component(self):
        return components.html(self.text, height=400)


#  Hjelpefunksjon - dagens strømpris
def elspot_today():
    url = "https://norway-power.ffail.win/" 
    url = "https://playground-norway-power.ffail.win" #bruk denne for testing
    today = date.today()
    zones = ["NO1", "NO2", "NO3", "NO4", "NO5"]
    prize_zone_array = []
    for i, zone in enumerate(zones):
        r = requests.get(f"{url}/?zone={zone}&date={today}&key=b0235f2e-7ddc-4bf1-a054-5dffb4ec037a")
        if r.status_code == 200:
            price_array = []
            for i in range(0, 24):
                NOK_per_kWh = list(r.json().values())[i]["NOK_per_kWh"]
                price_array.append(NOK_per_kWh)
            prize_zone_array.append(price_array)
    options = ["NO1", "NO2", "NO3", "NO4", "NO5"]
    selected_region = st.selectbox("Velg strømregion", options)
    df = {
        "NO1" : 0,
        "NO2" : 1,
        "NO3" : 2,
        "NO4" : 3,
        "NO5" : 4
    }
    chart_data = pd.DataFrame({selected_region: prize_zone_array[df[selected_region]],}).to_numpy().flatten()
    Plotting().xy_plot(np.arange(0, len(chart_data), 1), 0, 24, f"Timer i ett døgn, {today}", chart_data, 0, max(chart_data), "Elspotpris [kr]", Plotting().FOREST_GREEN)
    st.metric(label = "Gjennomsnittlig strømpris", value = f"{round(np.mean(price_array), 2)} kr")

#  Hjelpefunksjon - dagens strømpris
def elspot_today_data():
    url = "https://norway-power.ffail.win/" 
    #url = "https://playground-norway-power.ffail.win" #bruk denne for testing
    today = date.today()
    zones = ["NO1", "NO2", "NO3", "NO4", "NO5"]
    prize_zone_array = []
    for i, zone in enumerate(zones):
        r = requests.get(f"{url}/?zone={zone}&date={today}&key=b0235f2e-7ddc-4bf1-a054-5dffb4ec037a")
        if r.status_code == 200:
            price_array = []
            for i in range(0, 24):
                NOK_per_kWh = list(r.json().values())[i]["NOK_per_kWh"]
                price_array.append(NOK_per_kWh)
            prize_zone_array.append(price_array)
    return prize_zone_array

def electricity_database():
    headers = {'auth-token': '1BuQzNfLDfUy4RksWFTwJvBypnl5qBwi'}
    params = {'countryCode': 'NO'}
    response = requests.get('https://api.co2signal.com/v1/latest', params=params, headers=headers)
    deta = Deta("a0558p23_tjZdBJdbLTwWfajJU4x86NQzsYjv5ECS")
    db = deta.Base("Intensitet")
    if response.status_code == 200:
        prize_zone_array = elspot_today_data()
        today = date.today().strftime("%d.%m.%Y")
        data = response.json()
        carbon_intensity = data["data"]["carbonIntensity"]
        fossil_fuel_percentage = data["data"]["fossilFuelPercentage"]
        if prize_zone_array != []:
            db.put({
                "key" : today,
                "carbon_intensity" : carbon_intensity,
                'fossil_fuel_percentage' : fossil_fuel_percentage,
                "no1_price" : prize_zone_array[0],
                "no2_price" : prize_zone_array[1],
                "no3_price" : prize_zone_array[2],
                "no4_price" : prize_zone_array[3],
                "no5_price" : prize_zone_array[4]
            })
    res = db.fetch().items
    date_list = []
    carbon_intensity_list = []
    fossil_fuel_percentage_list = []
    no1_price_list = []
    no2_price_list = []
    no3_price_list = []
    no4_price_list = []
    no5_price_list = []
    for i in range(0, len(res)):
        res_i = res[i]
        date_list.append(res_i["key"])
        carbon_intensity_list.append(res_i["carbon_intensity"])
        fossil_fuel_percentage_list.append(res_i["fossil_fuel_percentage"])
        no1_price_list.append(res_i["no1_price"])
        no2_price_list.append(res_i["no2_price"])
        no3_price_list.append(res_i["no3_price"])
        no4_price_list.append(res_i["no4_price"])
        no5_price_list.append(res_i["no5_price"])

    df = pd.DataFrame({
        "Dato" : date_list,
        "carbon_intensity" : carbon_intensity_list,
        "fossil_fuel_percentage" : fossil_fuel_percentage_list,
        "NO1" : no1_price_list,
        "NO2" : no2_price_list,
        "NO3" : no3_price_list,
        "NO4" : no4_price_list,
        "NO5" : no5_price_list, 
    })
    options = df["Dato"]
    selected_date_index = st.selectbox("Velg region", range(len(options)), format_func=lambda x: options[x])
    selected_region = st.selectbox("Velg region", options=["NO1", "NO2", "NO3", "NO4", "NO5"])
    y = df[selected_region][selected_date_index]
    Plotting().xy_plot(np.arange(0, 24, 1), 0, 23, f"Timer i ett døgn, {options[selected_date_index]}", y, 0, max(y), "Spotpris [kr]", Plotting().FOREST_GREEN)
    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric(label = "Gjennomsnittlig strømpris", value = f"{round(np.mean(y), 2)} kr")
    with c2:
        st.metric(label = "Maksimum strømpris", value = f"{round(np.max(y), 2)} kr")
    with c3:
        st.metric(label = "Minimum strømpris", value = f"{round(np.min(y), 2)} kr")
    with st.expander("Historiske data etter 18/01/2023"):
        st.dataframe(df)  

#  Hjelpklasse - Plotting
class Plotting:
    def __init__(self):
        self.GRASS_GREEN = "#48a23f"
        self.GRASS_BLUE = "#3f48a2"
        self.GRASS_RED = "#a23f48"
        self.GRASS_PINK = "#a23f7a"
        self.GRASS_PURPLE = "#683fa2"

        self.SPRING_GREEN = "#b7dc8f"
        self.SPRING_BLUE = "#8fb7dc"
        self.SPRING_PINK = "#dc8fb7"

        self.FOREST_GREEN = "#1d3c34"
        self.FOREST_BROWN = "#3c341d"
        self.FOREST_DARK_BROWN = "#3c251d"
        self.FOREST_PURPLE = "#341d3c"
        self.FOREST_DARK_PURPLE = "#3c1d35"

        self.SUN_YELLOW = "#FFC358"
        self.SUN_PINK = "#c358ff"
        self.SUN_GREEN = "#58ffc3"

    def xy_plot(self, x, xmin, xmax, xlabel, y, ymin, ymax, ylabel, COLOR):
        source = pd.DataFrame({"x": x, "y": y})
        c = alt.Chart(source).mark_line().encode(
            x=alt.X("x", scale=alt.Scale(domain=[xmin, xmax]), title=xlabel),
            y=alt.Y("y", scale=alt.Scale(domain=[ymin, ymax], reverse=True), title=ylabel),
            color = alt.value(COLOR))
        st.altair_chart(c, use_container_width=True)

    def xy_plot_reversed(self, x, y, groundwater_table = None, area_divider = None):
        plt.scatter(x, y)
        if groundwater_table != None and area_divider != None:
            plt.axhline(y = groundwater_table, color = 'b', linestyle = '--', label = f"Grunnvannstand: {groundwater_table} m")
            plt.vlines(x = area_divider, ymin = groundwater_table, ymax = max(y), color = 'r', linestyle = '--', label = f"Uforstyrret temperatur: {round(area_divider,-3)} °C")
        plt.plot(x,y, '--')
        plt.legend(loc='best')
        plt.ylabel("Dybde [m]")
        plt.ylim(0, max(y)*1.1)
        plt.grid(color='black', linestyle='--', linewidth=0.1)
        plt.gca().invert_yaxis()
        plt.rcParams['xtick.top'] = plt.rcParams['xtick.labeltop'] = False
        plt.rcParams['xtick.bottom'] = plt.rcParams['xtick.labelbottom'] = True
        st.pyplot(plt)
        plt.close()        

    def xy_bar_plot(self, x, xmin, xmax, xlabel, y, ymin, ymax, ylabel, COLOR):
        source = pd.DataFrame({"x": x, "y": y})
        c = alt.Chart(source).mark_bar(width=0.5).encode(
            x=alt.X("x", scale=alt.Scale(domain=[xmin, xmax]), title=xlabel),
            y=alt.Y("y", scale=alt.Scale(domain=[ymin, ymax]), title=ylabel),
            color = alt.value(COLOR))
        st.altair_chart(c, use_container_width=True)

    def xy_bar_thick_plot(self, x, xmin, xmax, xlabel, y, ymin, ymax, ylabel, COLOR):
        source = pd.DataFrame({"x": x, "y": y})
        c = alt.Chart(source).mark_bar().encode(
            x=alt.X("x", scale=alt.Scale(domain=[xmin, xmax]), title=xlabel),
            y=alt.Y("y", scale=alt.Scale(domain=[ymin, ymax]), title=ylabel),
            color = alt.value(COLOR))
        st.altair_chart(c, use_container_width=True)

    def hourly_stack_plot(self, y1 , y2, y1label, y2label, y1color, y2color, winterweek=0):
        max_index = 8623
        x = np.arange(0, 8760)
        plt.xlim(0, 8760)
        if winterweek == True:
            plt.xlim(max_index - 24, max_index + 24)
        plt.stackplot(x, y1, y2, labels=[f'{y1label}: {int(round((np.sum(y1)),0)):,} kWh | {int(max(y1)):,} kW'.replace(',', ' '),f'{y2label}: {int(round((np.sum(y2)),0)):,} kWh | {int(max(y2)):,} kW'.replace(',', ' ')], colors=[y1color,y2color])
        #plt.stackplot(x, y1, y2, labels=[f'{y1label}: {int(round((np.sum(y1)),0)):,} kWh'.replace(',', ' '),f'{y2label}: {int(round((np.sum(y2)),0)):,} kWh'.replace(',', ' ')], colors=[y1color,y2color])        
        plt.legend(loc='best')
        plt.ylabel("Timesmidlet effekt [kWh/h]")
        plt.xlabel("Timer i ett år")
        plt.grid(color='black', linestyle='--', linewidth=0.1)
        st.pyplot(plt)
        plt.close()

    def hourly_stack_plot_negative(self, y1 , y2, y3, y1label, y2label, y1color, y2color, y3color, winterweek=0):
        max_index = 8623
        x = np.arange(0, 8760)
        plt.xlim(0, 8760)
        if winterweek == True:
            plt.xlim(max_index - 24, max_index + 24)
        plt.stackplot(x, y1, y2, labels=[f'{y1label}: {int(round((np.sum(y1)),0)):,} kWh | {int(max(y1)):,} kW'.replace(',', ' '),f'{y2label}: {int(round((np.sum(y2)),0)):,} kWh | {int(max(y2)):,} kW'.replace(',', ' ')], colors=[y1color,y2color])
        plt.stackplot(x, y3, labels=[f'Lading: {int(round((np.sum(y3)),0)):,} kWh | -{int(max(y3)):,} kW'.replace(',', ' '),f'{y2label}: {int(round((np.sum(y2)),0)):,} kWh | {int(max(y2)):,} kW'.replace(',', ' ')], colors=[y3color])
        #plt.stackplot(x, y1, y2, labels=[f'{y1label}: {int(round((np.sum(y1)),0)):,} kWh'.replace(',', ' '),f'{y2label}: {int(round((np.sum(y2)),0)):,} kWh'.replace(',', ' ')], colors=[y1color,y2color])        
        plt.legend(loc='best')
        plt.ylabel("Timesmidlet effekt [kWh/h]")
        plt.xlabel("Timer i ett år")
        plt.grid(color='black', linestyle='--', linewidth=0.1)
        st.pyplot(plt)
        plt.close()

    def hourly_stack_plot_quad_negative(self, y1 , y2, y3, y4, y1label, y2label, y4label, y1color, y2color, y3color, y4color, winterweek=0):
        max_index = 8623
        x = np.arange(0, 8760)
        plt.xlim(0, 8760)
        if winterweek == True:
            plt.xlim(max_index - 24, max_index + 24)
        plt.stackplot(x, y1, y2, y4, labels=[f'{y1label}: {int(round((np.sum(y1)),0)):,} kWh | {int(max(y1)):,} kW'.replace(',', ' '),f'{y2label}: {int(round((np.sum(y2)),0)):,} kWh | {int(max(y2)):,} kW'.replace(',', ' '),f'{y4label}: {int(round((np.sum(y4)),0)):,} kWh | {int(max(y4)):,} kW'.replace(',', ' ')], colors=[y1color,y2color,y4color])
        plt.stackplot(x, y3, labels=[f'Lading: {int(round((np.sum(y3)),0)):,} kWh | -{int(min(y3)):,} kW'.replace(',', ' '),f'{y2label}: {int(round((np.sum(y2)),0)):,} kWh | {int(max(y2)):,} kW'.replace(',', ' ')], colors=[y3color])
        #plt.stackplot(x, y1, y2, labels=[f'{y1label}: {int(round((np.sum(y1)),0)):,} kWh'.replace(',', ' '),f'{y2label}: {int(round((np.sum(y2)),0)):,} kWh'.replace(',', ' ')], colors=[y1color,y2color])        
        plt.legend(loc='best')
        #plt.ylim(bottom=-100)
        plt.ylabel("Timesmidlet effekt [kWh/h]")
        plt.xlabel("Timer i ett år")
        plt.grid(color='black', linestyle='--', linewidth=0.1)
        st.pyplot(plt)
        plt.close()

    def hourly_double_plot(self, y1 , y2, y1label, y2label, y1color, y2color, winterweek=0, hours=24, max_index = 8623):
        x = np.arange(0, 8760)
        plt.xlim(0, 8760)
        plt.ylim(0, max(y1)*1.1)
        if winterweek == True:
            plt.xlim(max_index - hours, max_index + hours)
        plt.plot(x, y1, label=y1label, color=y1color)
        plt.plot(x, y2, label=y2label, color=y2color, linestyle='--')
        plt.legend(loc='best')
        plt.ylabel("Timesmidlet effekt [kWh/h]")
        plt.xlabel("Timer i ett år")
        plt.grid(color='black', linestyle='--', linewidth=0.1)
        st.pyplot(plt)
        plt.close()

    def hourly_triple_stack_plot(self, y1 , y2, y3, y1label, y2label, y3label, y1color, y2color, y3color):
        x = np.arange(0, 8760)
        plt.stackplot(x, y1, y2, y3, labels=[
        f'{y1label}: {int(round((np.sum(y1)),0)):,} kWh | {int(max(y1)):,} kW'.replace(',', ' '),
        f'{y2label}: {int(round((np.sum(y2)),0)):,} kWh | {int(max(y2)):,} kW'.replace(',', ' '),
        f'{y3label}: {int(round((np.sum(y3)),0)):,} kWh | {int(max(y3)):,} kW'.replace(',', ' ')], colors=[y1color, y2color, y3color])
        #plt.stackplot(x, y1, y2, y3, labels=[
        #f'{y1label}: {int(round((np.sum(y1)),0)):,} kWh'.replace(',', ' '),
        #f'{y2label}: {int(round((np.sum(y2)),0)):,} kWh'.replace(',', ' '),
        #f'{y3label}: {int(round((np.sum(y3)),0)):,} kWh'.replace(',', ' ')], colors=[y1color, y2color, y3color])
        plt.legend(loc='best')
        plt.ylabel("Timesmidlet effekt [kWh/h]")
        plt.xlabel("Timer i ett år")
        plt.grid(color='black', linestyle='--', linewidth=0.1)
        plt.xlim(0, 8760)
        st.pyplot(plt)
        plt.close()

    def hourly_triple_stack_plot_negative(self, y1 , y2, y3, y4, y1label, y2label, y3label, y1color, y2color, y3color, y4color):
        x = np.arange(0, 8760)
        plt.stackplot(x, y1, y2, y3, labels=[
        f'{y1label}: {int(round((np.sum(y1)),0)):,} kWh | {int(max(y1)):,} kW'.replace(',', ' '),
        f'{y2label}: {int(round((np.sum(y2)),0)):,} kWh | {int(max(y2)):,} kW'.replace(',', ' '),
        f'{y3label}: {int(round((np.sum(y3)),0)):,} kWh | {int(max(y3)):,} kW'.replace(',', ' ')], colors=[y1color, y2color, y3color])
        plt.stackplot(x, y4, labels=[f'Lading: {int(round((np.sum(y4)),0)):,} kWh | {int(min(y4)):,} kW'.replace(',', ' ')], colors=[y4color])
        #plt.stackplot(x, y1, y2, y3, labels=[
        #f'{y1label}: {int(round((np.sum(y1)),0)):,} kWh'.replace(',', ' '),
        #f'{y2label}: {int(round((np.sum(y2)),0)):,} kWh'.replace(',', ' '),
        #f'{y3label}: {int(round((np.sum(y3)),0)):,} kWh'.replace(',', ' ')], colors=[y1color, y2color, y3color])
        plt.legend(loc='best')
        plt.ylabel("Timesmidlet effekt [kWh/h]")
        plt.xlabel("Timer i ett år")
        plt.grid(color='black', linestyle='--', linewidth=0.1)
        plt.xlim(0, 8760)
        st.pyplot(plt)
        plt.close()

    def hourly_quad_stack_plot_negative(self, y1, y2, y3, y4, y5, y1label, y2label, y3label, y4label, y1color, y2color, y3color, y4color, y5color):
        x = np.arange(0, 8760)
        plt.stackplot(x, y1, y2, y3, y4, labels=[
        f'{y1label}: {int(round((np.sum(y1)),0)):,} kWh | {int(max(y1)):,} kW'.replace(',', ' '),
        f'{y2label}: {int(round((np.sum(y2)),0)):,} kWh | {int(max(y2)):,} kW'.replace(',', ' '),
        f'{y3label}: {int(round((np.sum(y3)),0)):,} kWh | {int(max(y3)):,} kW'.replace(',', ' '),
        f'{y4label}: {int(round((np.sum(y4)),0)):,} kWh | {int(max(y4)):,} kW'.replace(',', ' ')], colors=[y1color, y2color, y3color, y4color])
        plt.stackplot(x, y5, labels=[f'Lading: {int(round((np.sum(y5)),0)):,} kWh | {int(min(y5)):,} kW'.replace(',', ' ')], colors=[y5color])
        #plt.stackplot(x, y1, y2, y3, labels=[
        #f'{y1label}: {int(round((np.sum(y1)),0)):,} kWh'.replace(',', ' '),
        #f'{y2label}: {int(round((np.sum(y2)),0)):,} kWh'.replace(',', ' '),
        #f'{y3label}: {int(round((np.sum(y3)),0)):,} kWh'.replace(',', ' ')], colors=[y1color, y2color, y3color])
        plt.legend(loc='best')
        plt.ylabel("Timesmidlet effekt [kWh/h]")
        plt.xlabel("Timer i ett år")
        plt.grid(color='black', linestyle='--', linewidth=0.1)
        plt.xlim(0, 8760)
        st.pyplot(plt)
        plt.close()

    def hourly_quad_stack_plot(self, y1 , y2, y3, y4, y1label, y2label, y3label, y4label, y1color, y2color, y3color, y4color):
        x = np.arange(0, 8760)
        plt.stackplot(x, y1, y2, y3, y4, labels=[
        f'{y1label}: {int(round((np.sum(y1)),0)):,} kWh | {int(max(y1)):,} kW'.replace(',', ' '),
        f'{y2label}: {int(round((np.sum(y2)),0)):,} kWh | {int(max(y2)):,} kW'.replace(',', ' '),
        f'{y3label}: {int(round((np.sum(y3)),0)):,} kWh | {int(max(y3)):,} kW'.replace(',', ' '),
        f'{y4label}: {int(round((np.sum(y4)),0)):,} kWh | {int(max(y4)):,} kW'.replace(',', ' ')], colors=[y1color, y2color, y3color, y4color])
        plt.legend(loc='best')
        plt.ylabel("Timesmidlet effekt [kWh/h]")
        plt.xlabel("Timer i ett år")
        plt.grid(color='black', linestyle='--', linewidth=0.1)
        plt.xlim(0, 8760)
        st.pyplot(plt)
        plt.close()

    def hourly_plot(self, y1, y1label, y1color, ymin = None, ymax = None, hline_value=0, winterweek = 0, max_index = 8623):
        x = np.arange(0, 8760)
        plt.xlim(0, 8760)
        if winterweek == True:
            plt.xlim(max_index - 24, max_index + 24)
            #date_1, date_2 = np.datetime64("2021-01-01T00"), np.datetime64("2022-01-01T00")
            #x = np.arange(date_1, date_2, dtype='datetime64')
            #myFmt = mdates.DateFormatter('%d.%b')
            #plt.gca().xaxis.set_major_formatter(myFmt)
        plt.stackplot(x, y1, labels=[f'{y1label}: {int(round((np.sum(y1)),0)):,} kWh | {int(max(y1)):,} kW'.replace(',', ' ')], colors=y1color)
        #plt.stackplot(x, y1, labels=[f'{y1label}: {int(round((np.sum(y1)),0)):,} kWh'.replace(',', ' ')], colors=y1color)
        plt.legend(loc='best')
        plt.ylabel("Timesmidlet effekt [kWh/h]")
        plt.xlabel("Timer i ett år")
        plt.ylim((ymin, ymax))
        plt.axhline(y = hline_value, color = 'black', linestyle = '-.', linewidth=0.5)        
        plt.grid(color='black', linestyle='--', linewidth=0.1)
        st.pyplot(plt)
        plt.close()
    
    def hourly_plot_with_negative(self, y1, y2, y1label, y1color, y2color, ymin = None, ymax = None, hline_value=0, winterweek = 0, max_index = 8623):
        x = np.arange(0, 8760)
        plt.xlim(0, 8760)
        if winterweek == True:
            plt.xlim(max_index - 24, max_index + 24)
            #date_1, date_2 = np.datetime64("2021-01-01T00"), np.datetime64("2022-01-01T00")
            #x = np.arange(date_1, date_2, dtype='datetime64')
            #myFmt = mdates.DateFormatter('%d.%b')
            #plt.gca().xaxis.set_major_formatter(myFmt)
        plt.stackplot(x, y1, labels=[f'{y1label}: {int(round((np.sum(y1)),0)):,} kWh | {int(max(y1)):,} kW'.replace(',', ' ')], colors=y1color)
        plt.stackplot(x, -y2, labels=[f'Lading: {int(round((np.sum(y2)),0)):,} kWh | {int(min(y2)):,} kW'.replace(',', ' ')], colors=y2color)
        #plt.stackplot(x, y1, labels=[f'{y1label}: {int(round((np.sum(y1)),0)):,} kWh'.replace(',', ' ')], colors=y1color)
        plt.legend(loc='best')
        plt.ylabel("Timesmidlet effekt [kWh/h]")
        plt.xlabel("Timer i ett år")
        plt.ylim((ymin, ymax))
        plt.axhline(y = hline_value, color = 'black', linestyle = '-.', linewidth=0.5)        
        plt.grid(color='black', linestyle='--', linewidth=0.1)
        st.pyplot(plt)
        plt.close()

    def hourly_price_plot(self, y1, y1label, y1color, ymin = None, ymax = None, hline_value=0, winterweek = 0, max_index = 8623):
        x = np.arange(0, 8760)
        plt.xlim(0, 8760)
        plt.ylim(0, 5)
        if winterweek == True:
            plt.xlim(max_index - 24, max_index + 24)
            #date_1, date_2 = np.datetime64("2021-01-01T00"), np.datetime64("2022-01-01T00")
            #x = np.arange(date_1, date_2, dtype='datetime64')
            #myFmt = mdates.DateFormatter('%d.%b')
            #plt.gca().xaxis.set_major_formatter(myFmt)
        plt.stackplot(x, y1, labels=[f'Gjennomsnittspris: {round(float(np.mean(y1)),-3):,} kr/kWh | Makspris: {round(float(max(y1)),-3):,} kr'.replace(',', ' ')], colors=y1color)
        #plt.stackplot(x, y1, labels=[f'{y1label}: {int(round((np.sum(y1)),0)):,} kWh'.replace(',', ' ')], colors=y1color)
        plt.legend(loc='best')
        plt.ylabel("Kroner")
        plt.xlabel("Timer i ett år")
        plt.ylim((ymin, ymax))
        plt.axhline(y = hline_value, color = 'black', linestyle = '-.', linewidth=0.5)        
        plt.grid(color='black', linestyle='--', linewidth=0.1)
        st.pyplot(plt)
        plt.close()

    def hourly_negative_plot(self, y1, y1label, y1color, ymin = None, ymax = None, hline_value=0, winterweek = 0, max_index = 8623):
        x = np.arange(0, 8760)
        plt.xlim(0, 8760)
        solar_production, solar_effect = negative_sum(y1)
        if winterweek == True:
            plt.xlim(max_index - 24, max_index + 24)
        plt.stackplot(x, y1, labels=[f'{y1label}: {int(round((np.sum(y1)),0)):,} kWh | {int(max(y1)):,} kW \nOverskuddsproduksjon: {round(solar_production,-3):,} kWh | {solar_effect:,} kW'.replace(',', ' ')], colors=y1color)
        plt.legend(loc='best')
        plt.ylabel("Timesmidlet effekt [kWh/h]")
        plt.xlabel("Timer i ett år")
        plt.ylim((ymin, ymax))
        plt.axhline(y = hline_value, color = 'black', linestyle = '-.', linewidth=0.5)        
        plt.grid(color='black', linestyle='--', linewidth=0.1)
        st.pyplot(plt)
        plt.close()

    def hourly_duration_plot(self, y1, y1label, y1color, ymin = None, ymax = None, hline_value=0):
        x = np.arange(0, len(y1))
        plt.stackplot(x, np.sort(y1)[::-1], labels=[f'{y1label}: {int(round((np.sum(y1)),0)):,} kWh | {int(max(y1)):,} kW'.replace(',', ' ')], colors=y1color)
        #plt.stackplot(x, np.sort(y1)[::-1], labels=[f'{y1label}: {int(round((np.sum(y1)),0)):,} kWh'.replace(',', ' ')], colors=y1color)
        plt.legend(loc='best')
        plt.ylabel("Timesmidlet effekt [kWh/h]")
        plt.ylim((ymin, ymax))
        plt.axhline(y = hline_value, color = 'black', linestyle = '-.', linewidth=0.5)        
        plt.grid(color='black', linestyle='--', linewidth=0.1)
        plt.xlim(0, 8760)
        plt.xlabel("Varighet [timer]")
        st.pyplot(plt)
        plt.close()

    def xy_plot(self, x, xmin, xmax, x_label, y, ymin, ymax, y_label, COLOR):
        fig, ax = plt.subplots()
        mpl.rcParams['axes.prop_cycle'] = cycler(color=[COLOR])
        ax.plot(x, y, linewidth=2.0)
        ax.grid(color='black', linestyle='--', linewidth=0.1)
        ax.set(xlim=(xmin, xmax), ylim=(ymin, ymax), xlabel=(x_label), ylabel=(y_label))
        st.pyplot(plt)
        plt.close()

    def xy_plot_bar(self, x, x_label, y, ymin, ymax, y_label, COLOR, hline_value=0):
        fig, ax = plt.subplots()
        mpl.rcParams['axes.prop_cycle'] = cycler(color=[COLOR])
        ax.bar(x, y)
        ax.grid(color='black', linestyle='--', linewidth=0.1)
        #ax.set(ylim=(ymin, ymax), xlabel=(x_label), ylabel=(y_label))
        ax.set(xlabel=(x_label), ylabel=(y_label))
        if hline_value != 0:
            ax.axhline(y = hline_value, color = 'black', linestyle = '--', linewidth=0.3)
        st.pyplot(plt)
        plt.close()

    def xy_plot_bar_stacked(self, x, x_label, y1, y2, y1label, y2label, ymin, ymax, y_label, COLOR1, COLOR2):
        #plt.rcParams["figure.figsize"] = (3,20)
        fig, ax = plt.subplots(figsize=(10,3))
        plt.gca().yaxis.set_major_formatter(FuncFormatter(lambda x, p: format(int(x), ',').replace(",", " ")))
        #plt.ticklabel_format(style='plain')
        ax.bar(x, y1, label = y1label, color = COLOR1)
        ax.bar(x, y2, bottom=y1, label = y2label, color = COLOR2)
        ax.legend()
        ax.grid(color='black', linestyle='--', linewidth=0.1)
        ax.set(xlabel=(x_label), ylabel=(y_label))
        ax.set(ylim=(ymin, ymax), xlabel=(x_label), ylabel=(y_label))
        st.pyplot(plt)
        plt.close()

    def xy_simulation_plot(self, x, xmin, xmax, x_label, y1, y2, y_label, y_legend1, y_legend2, COLOR1, COLOR2, ymin = -3, ymax = 12):
        fig, ax = plt.subplots()
        x = x/12
        ax.plot(x, y1, linewidth=2.0, color=COLOR1, label=y_legend1)
        ax.plot(x, y2, linewidth=2.0, color=COLOR2, label=y_legend2)
        ax.axhline(y = 1, color = 'black', linestyle = '--', linewidth=0.3)
        ax.axhline(y = 0, color = 'black', linestyle = '-.', linewidth=0.3)        
        ax.legend()
        ax.grid(color='black', linestyle='--', linewidth=0.1)
        ax.set(xlim=(xmin, xmax), xlabel=(x_label), ylabel=(y_label), yticks=(np.arange(ymin, ymax, 1)))
        st.pyplot(plt)

    def xy_simulation_pygf_plot(self, x, y1, COLOR1):
        fig, ax = plt.subplots()
        ax.plot(x, y1, linewidth=0.05, color=COLOR1)
        ax.axhline(y = 1, color = 'black', linestyle = '--', linewidth=0.3)
        ax.axhline(y = 0, color = 'black', linestyle = '-.', linewidth=0.3)        
        ax.legend()
        ax.set(xlabel=("Timer"), ylabel=("Gjennomsnittlig kollektorvæsketemperatur [°C]"), xlim=(0, len(x)), ylim=(-3,12))
        ax.grid(color='black', linestyle='--', linewidth=0.1)
        st.pyplot(plt)

    def plot_clustered_stacked(self, dfall, labels=None,  H="/", **kwargs):
        """Given a list of dataframes, with identical columns and index, create a clustered stacked bar plot. 
    labels is a list of the names of the dataframe, used for the legend
    title is a string for the title of the plot
    H is the hatch used for identification of the different dataframe"""

        n_df = len(dfall)
        n_col = len(dfall[0].columns) 
        n_ind = len(dfall[0].index)
        axe = plt.subplot(111)

        for df in dfall : # for each data frame
            axe = df.plot(kind="bar",
                        linewidth=0,
                        stacked=True,
                        ax=axe,
                        legend=False,
                        grid=False,
                        **kwargs)  # make bar plots

        h,l = axe.get_legend_handles_labels() # get the handles we want to modify
        for i in range(0, n_df * n_col, n_col): # len(h) = n_col * n_df
            for j, pa in enumerate(h[i:i+n_col]):
                for rect in pa.patches: # for each index
                    rect.set_x(rect.get_x() + 1 / float(n_df + 1) * i / float(n_col))
                    rect.set_hatch(H * int(i / n_col)) #edited part     
                    rect.set_width(1 / float(n_df + 1))

        axe.set_xticks((np.arange(0, 2 * n_ind, 2) + 1 / float(n_df + 1)) / 2.)
        axe.set_xticklabels(df.index, rotation = 0)

        # Add invisible data to add another legend
        n=[]        
        for i in range(n_df):
            n.append(axe.bar(0, 0, color="gray", hatch=H * i))

        l1 = axe.legend(h[:n_col], l[:n_col])
        if labels is not None:
            l2 = plt.legend(n, labels) 
        axe.add_artist(l1)
        st.pyplot(plt)
        return axe






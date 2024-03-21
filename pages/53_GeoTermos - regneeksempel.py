import streamlit as st 
import pandas as pd
import streamlit.components.v1 as components
import numpy as np
import plotly.graph_objects as go
from helpscripts._elprice import CalculateCosts

START_INDEX_SUMMER = 2183
END_INDEX_SUMMER = 6832

def hour_to_month(hourly_array, aggregation='sum'):
    result_array = []
    temp_value = 0 if aggregation in ['sum', 'max'] else []
    count = 0 if aggregation == 'average' else None
    for index, value in enumerate(hourly_array):
        if np.isnan(value):
            value = 0
        if aggregation == 'sum':
            temp_value += value
        elif aggregation == 'average':
            temp_value.append(value)
            count += 1
        elif aggregation == 'max' and value > temp_value:
            temp_value = value
        if index in [744, 1416, 2160, 2880, 3624, 4344, 5088, 5832, 6552, 7296, 8016, 8759]:
            if aggregation == 'average':
                if count != 0:
                    result_array.append(sum(temp_value) / count)
                else:
                    result_array.append(0)
                temp_value = []
                count = 0
            else:
                result_array.append(temp_value)
                temp_value = 0 if aggregation in ['sum', 'max'] else []
    return result_array

def conditional_sum(array, mode = 'above'):
    new_array = []
    if mode == 'above':
        for index, value in enumerate(array):
            if value > 0:
                new_array.append(value)
            else:
                new_array.append(0)
    else:
        for index, value in enumerate(array):
            if value < 0:
                new_array.append(value)
            else:
                new_array.append(0)
    return round(int(sum(new_array)),-3)

st.cache_resource(show_spinner=False)
def read_df(sheet_name="Sheet1"):
    df = pd.read_excel("src/data/geotermos_profil/GeoTermosEksempel.xlsx", sheet_name=sheet_name)
    return df

def show_simple_plot(df, name, color='#1d3c34', ymin=0, ymax=1000, mode='hourly', type='positive'):
    array = df[name].to_numpy()
    if mode == 'hourly':
        fig = go.Figure()
        fig.add_trace(go.Bar(x=df.index, y=array, name='Values'))
        fig.update_traces(marker_color=color)
        fig.update_layout(
            yaxis_range=[ymin, ymax],
            margin=dict(l=10, r=10, t=0, b=0),
            yaxis_ticksuffix=" kW",
            separators="* .*",
            height=300,
            xaxis = dict(
                tickmode = 'array', 
                tickvals = [0, 24 * (31), 24 * (31 + 28), 24 * (31 + 28 + 31), 24 * (31 + 28 + 31 + 30), 24 * (31 + 28 + 31 + 30 + 31), 24 * (31 + 28 + 31 + 30 + 31 + 30), 24 * (31 + 28 + 31 + 30 + 31 + 30 + 31), 24 * (31 + 28 + 31 + 30 + 31 + 30 + 31 + 31), 24 * (31 + 28 + 31 + 30 + 31 + 30 + 31 + 31 + 30), 24 * (31 + 28 + 31 + 30 + 31 + 30 + 31 + 31 + 30 + 31), 24 * (31 + 28 + 31 + 30 + 31 + 30 + 31 + 31 + 30 + 31 + 30), 24 * (31 + 28 + 31 + 30 + 31 + 30 + 31 + 31 + 30 + 31 + 30 + 31)], 
                ticktext = ["1.jan", "", "1.mar", "", "1.mai", "", "1.jul", "", "1.sep", "", "1.nov", "", "1.jan"],
                title=None,
                ))
        st.plotly_chart(fig, use_container_width=True, config = {'displayModeBar': False, 'staticPlot': True})
    else:
        array = hour_to_month(array)
        fig = go.Figure()
        months = ['jan', 'feb', 'mar', 'apr', 'mai', 'jun', 'jul', 'aug', 'sep', 'okt', 'nov', 'des']
        fig.add_trace(go.Bar(x=months, y=array, name='Values'))
        fig.update_traces(marker_color=color)
        fig.update_layout(
            yaxis=dict(tickformat=',d'),
            yaxis_range=[ymin, ymax],
            margin=dict(l=10, r=10, t=0, b=0),
            yaxis_ticksuffix=" kW",
            separators="* .*",
            height=300,)
        st.plotly_chart(fig, use_container_width=True, config = {'displayModeBar': False, 'staticPlot': True})
    above_sum = conditional_sum(array=array, mode='above')
    below_sum = -conditional_sum(array=array, mode='below')
    if type == 'positive':
        st.metric(label="Kjøpt elektrisk energi", value=f"{above_sum:,} kWh".replace(",", " "))
    else:
        st.metric(label="Overskudd solstrømproduksjon", value=f"{below_sum:,} kWh".replace(",", " "))
    st.markdown("---")
    #st.metric(label="Balanse", value=f"{above_sum - below_sum:,} kWh".replace(",", " "))
    return fig

def show_costs_plot(calculate_costs_object, df, name, color='#1d3c34', ymin=0, ymax=1000, type='positive', nettleie_mode=True):  
    calculate_costs_object.spotpris()
    calculate_costs_object.ekstra_nettleie_storre_naring()
    calculate_costs_object.hele_nettleie()
    calculate_costs_object.totaler()

    if calculate_costs_object.type_kunde != "Større næringskunde":
        fastledd_time = np.zeros(8760)
        fond_avgift_time = np.zeros(8760)
    else:
        fastledd_time = calculate_costs_object.fastledd_time
        fond_avgift_time = calculate_costs_object.fond_avgift_time

    nettleie = calculate_costs_object.energiledd_time + calculate_costs_object.kapledd_time + calculate_costs_object.offentlig_time + fastledd_time + fond_avgift_time
    if nettleie_mode == True:
        df = pd.DataFrame({
            'Nettleie': nettleie, 
            'Spotpris' : calculate_costs_object.spot_time
            })
    else:
        df = pd.DataFrame({
            'Spotpris' : calculate_costs_object.spot_time
            })
    fig = go.Figure()
    for col in df.columns[:-1]:
        fig.add_trace(go.Bar(x=df.index, y=df[col], name=col))
    fig.add_trace(go.Bar(x=df.index, y=df['Spotpris'], name='Spotpris'))
    fig.update_layout(
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        barmode='stack',
        #xaxis_title='Timer i ett år',
        yaxis_ticksuffix=" kr",
        separators="* .*",
        yaxis_range=[ymin, ymax],
        margin=dict(l=10, r=10, t=0, b=0),
        xaxis = dict(
            tickmode = 'array', 
            tickvals = [0, 24 * (31), 24 * (31 + 28), 24 * (31 + 28 + 31), 24 * (31 + 28 + 31 + 30), 24 * (31 + 28 + 31 + 30 + 31), 24 * (31 + 28 + 31 + 30 + 31 + 30), 24 * (31 + 28 + 31 + 30 + 31 + 30 + 31), 24 * (31 + 28 + 31 + 30 + 31 + 30 + 31 + 31), 24 * (31 + 28 + 31 + 30 + 31 + 30 + 31 + 31 + 30), 24 * (31 + 28 + 31 + 30 + 31 + 30 + 31 + 31 + 30 + 31), 24 * (31 + 28 + 31 + 30 + 31 + 30 + 31 + 31 + 30 + 31 + 30), 24 * (31 + 28 + 31 + 30 + 31 + 30 + 31 + 31 + 30 + 31 + 30 + 31)], 
            ticktext = ["1.jan", "", "1.mar", "", "1.mai", "", "1.jul", "", "1.sep", "", "1.nov", "", "1.jan"],
            title=None,
            #showgrid=True
            ),
        height=300)
    st.plotly_chart(fig, use_container_width=True, config = {'displayModeBar': False, 'staticPlot': True})
    if nettleie_mode == True:
        total_array = df['Nettleie'] + df['Spotpris']
    else:
        total_array = df['Spotpris']
    above_sum = conditional_sum(array=total_array, mode='above')
    below_sum = -conditional_sum(array=total_array, mode='below')
    if type == 'positive':
        st.metric(label="Kjøpt energi", value=f"{above_sum:,} kr".replace(",", " "))
    else:
        st.metric(label="Salg av solstrøm", value=f"{below_sum:,} kr".replace(",", " "))
    st.markdown("---")
    #st.metric(label="Balanse", value=f"{above_sum - below_sum:,} kr".replace(",", " "))


st.set_page_config(
    page_title="GeoTermos",
    layout="wide"
)

with open("styles/with_columns.css") as f:
    st.markdown("<style>{}</style>".format(f.read()), unsafe_allow_html=True)

st.title("GeoTermos - regneeksempel")

df = read_df()
df_positive = df.copy()
df_positive[df_positive < 0] = 0
df2 = read_df(sheet_name="Sheet2")
#######################################
#######################################
calculate_costs_object = CalculateCosts(energy_demand = df['Elkjel'])
calculate_costs_object.streamlit_input()
calculate_costs_object.bestem_prissatser()
calculate_costs_object.dager_i_hver_mnd()
calculate_costs_object.energiledd()
calculate_costs_object.kapasitetsledd()
calculate_costs_object.offentlige_avgifter()
#######################################
#######################################
ymax_hourly = df['Elkjel'].max() * 1.1
ymin_hourly = df['Elkjel'].min() * 1.1
monthly_array = hour_to_month(df['Elkjel'].to_numpy())
ymax_monthly = np.max(monthly_array) * 1.1
ymin_monthly = np.min(monthly_array) * 1.1
mode = 'hourly'
#if st.toggle("Månedsplot"):
#    mode='måned'
#else:
#    mode='hourly'
c1, c2, c3 = st.columns(3)
with c1:
    name = 'Elkjel'
    color = '#1d3c34'
    st.caption("Alt 1)")
    st.write(f"**Elkjel og sol**")
    if mode == 'hourly':
        show_simple_plot(df, name, color, ymin=0, ymax=ymax_hourly, mode=mode)
        show_simple_plot(df2, name, color, ymin=ymin_hourly, ymax=0, mode=mode, type='negative')
    else:
        show_simple_plot(df, name, color, ymin=0, ymax=ymax_monthly, mode=mode)
        show_simple_plot(df2, name, color, ymin=ymin_hourly, ymax=0, mode=mode, type='negative')
with c2:
    st.caption("Alt 2)")
    st.write(f"**Energibrønner og sol**")
    name = 'Energibrønner'
    color = '#b7dc8f'
    if mode == 'hourly':
        show_simple_plot(df, name, color, ymin=0, ymax=ymax_hourly, mode=mode)
        show_simple_plot(df2, name, color, ymin=ymin_hourly, ymax=0, mode=mode, type='negative')
    else:
        show_simple_plot(df, name, color, ymin=0, ymax=ymax_monthly, mode=mode)
        show_simple_plot(df2, name, color, ymin=ymin_hourly, ymax=0, mode=mode, type='negative')
with c3:
    st.caption("Alt 3)")
    st.write(f"**Termos og sol**")
    #st.caption("Varme fra tørrkjøler eller PVT")
    name = 'Termos og sol'
    color = '#48a23f'
    if mode == 'hourly':
        show_simple_plot(df, name, color, ymin=0, ymax=ymax_hourly, mode=mode)
        show_simple_plot(df2, name, color, ymin=ymin_hourly, ymax=0, mode=mode, type='negative')
    else:
        show_simple_plot(df, name, color, ymin=0, ymax=ymax_monthly, mode=mode)
        show_simple_plot(df2, name, color, ymin=ymin_hourly, ymax=0, mode=mode, type='negative')
#######################################
#######################################
with c1:
    name = 'Elkjel'
    color = '#1d3c34'
    calculate_costs_object.forb = df_positive[name].to_numpy()
    ymax_hourly = ymax_hourly*2.5
    ymin_hourly = ymin_hourly
    show_costs_plot(calculate_costs_object, df, name, color, ymin=0, ymax=ymax_hourly)
    calculate_costs_object.forb = df2[name].to_numpy()
    show_costs_plot(calculate_costs_object, df2, name, color, ymin=ymin_hourly, ymax=0, type='negative', nettleie_mode=False)
with c2:
    name = 'Energibrønner'
    color = '#b7dc8f'
    calculate_costs_object.forb = df_positive[name].to_numpy()
    show_costs_plot(calculate_costs_object, df, name, color, ymin=0, ymax=ymax_hourly)
    calculate_costs_object.forb = df2[name].to_numpy()
    show_costs_plot(calculate_costs_object, df2, name, color, ymin=ymin_hourly, ymax=0, type='negative', nettleie_mode=False)
with c3:
    name = 'Termos og sol'
    color = '#48a23f'
    calculate_costs_object.forb = df_positive[name].to_numpy()
    show_costs_plot(calculate_costs_object, df, name, color, ymin=0, ymax=ymax_hourly)
    calculate_costs_object.forb = df2[name].to_numpy()
    show_costs_plot(calculate_costs_object, df2, name, color, ymin=ymin_hourly, ymax=0, type='negative', nettleie_mode=False)
#######################################
#######################################
#st.line_chart(calculate_costs_object.spot_sats[calculate_costs_object.sone])



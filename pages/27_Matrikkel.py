import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np
from requests_oauthlib import OAuth2Session
from oauthlib.oauth2 import BackendApplicationClient
from fuzzywuzzy import process
from helpscripts._energianalyse import plot_2_timeserie, plot_3_timeserie, Grunnvarme
from pygwalker.api.streamlit import StreamlitRenderer, init_streamlit_comm

st.set_page_config(page_title="Matrikkel", page_icon="🧮", layout="wide")

with open("styles/main.css") as f:
    st.markdown("<style>{}</style>".format(f.read()), unsafe_allow_html=True)

st.title("Matrikkeldata")

fylker = ['Agder', 'Akershus', 'Buskerud', 'Finnmark', 'Innlandet', 'Møre og Romsdal', 'Nordland', 'Oslo', 'Rogaland', 'Trøndelag', 'Vestfold', 'Østfold', 'Telemark', 'Troms', 'Vestland']
#fylker = ['Rogaland', 'Trøndelag', 'Vestfold', 'Østfold', 'Telemark', 'Troms', 'Vestland']

#df = pd.read_csv(f"src/data/matrikkel/Usikker2.csv", sep=';', decimal=',', encoding = "ISO-8859-1")
#df = df[df['FYLKES_NAVN'] == 'TELEMARK']
#df.reset_index(inplace=True, drop=True)
#df.to_csv(f'src/data/matrikkel/Telemark.csv')

################################
################################
################################
with st.expander("Preprossesering"):
    if st.button("Start preprosessering"):
        my_bar = st.progress(0, text="Laster inn...")    
        increment = int(100 / len(fylker))
        percent_complete = 0
        for fylke in fylker:
            percent_complete = percent_complete + increment 
            my_bar.progress(percent_complete, text=f"Laster inn {fylke}...")
            df = pd.read_csv(f"src/data/matrikkel/{fylke}.csv", sep=';', decimal=',', encoding = "ISO-8859-1")
            df['BRUKSAREAL_TOTALT'] = df['BRUKSAREAL_TOTALT'].astype(float).astype(int)
            df = df[df["BRUKSAREAL_TOTALT"] > 80]
            df['ANTALL'] = 1
            grouped = df.groupby('BYGNINGSTYPE_NAVN')
            df_sum_values = grouped.sum()
            df_sum_values = df_sum_values[['BRUKSAREAL_TOTALT', 'ANTALL_ETASJER', 'UX_KOORDINAT', 'UY_KOORDINAT', 'BEBYGD_AREAL', 'ANTALL']]
            df_sum_values['FYLKE'] = fylke
            df_sum_values.reset_index(inplace=True)
            df_sum_values.to_csv(f'src/data/matrikkel/{fylke}_summert.csv')
        #st.write(df)
        my_bar.progress(100, text=f"Ferdig!")
################################
################################
################################
    
def show_aggregated_statistics(df, selected_y):
    if selected_y == "BRUKSAREAL_TOTALT":
        y_axis_name = "Bruksareal (m²)"
    elif selected_y == "ANTALL":
        y_axis_name = "Antall bygninger"
    else:
        y_axis_name = "Gj.snittlig bruksareal (m²)"
    fig = px.bar(df, x='FYLKE', y=selected_y, color="FYLKE", barmode='group')
    fig.update_layout(
        height=600,
        yaxis_tickformat=',.0f',
        xaxis_title=None,
        yaxis_title=y_axis_name,)
    st.plotly_chart(fig, use_container_width=True)

def show_statistics(df, selected_y, n_largest = 10, fylker = "Alle"):
    df = df.loc[df['FYLKE'].isin(fylker)]
    if selected_y == "BRUKSAREAL_TOTALT":
        y_axis_name = "Bruksareal (m²)"
        metric_text = "Bruksareal (m²)"
    else:
        y_axis_name = "Antall bygninger"
        metric_text = "Antall bygninger"

    top_10_categories = df.groupby('BYGNINGSTYPE_NAVN')[selected_y].sum().nlargest(n_largest).index
    df = df[df['BYGNINGSTYPE_NAVN'].isin(top_10_categories)]
    #df_sorted = df.groupby('BYGNINGSTYPE_NAVN').sum().sort_values(by=selected_y, ascending=False).reset_index()

    # Rejoin with original DataFrame to retain color information
    #df = df_sorted.merge(df[['BYGNINGSTYPE_NAVN', 'FYLKE']], on='BYGNINGSTYPE_NAVN', how='left')

    fig = px.bar(df, x='BYGNINGSTYPE_NAVN', y=selected_y, color='FYLKE', barmode='stack')
    fig.update_layout(
        height=600,
        yaxis_tickformat=',.0f',
        xaxis_title=None,
        yaxis_title=y_axis_name)
    st.plotly_chart(fig, use_container_width=True)
    c1, c2, c3 = st.columns(3)
    with c1:
        st.write("**Alle bygninger**")
        alle_bygninger = int(np.sum(df[selected_y]))
        st.metric(metric_text, value=f"{alle_bygninger:,}".replace(","," "))
    with c2:
        if grouping_mode:
            st.write("**Småhus**")
            df = df[df["BYGNINGSTYPE_NAVN"] == "Småhus"]
        else:
            st.write("**Eneboliger**")
            df = df[df["BYGNINGSTYPE_NAVN"] == "Enebolig"]
        
        eneboliger = int(np.sum(df[selected_y]))
        st.metric(metric_text, value=f"{eneboliger:,}".replace(","," "), delta=f"{int((eneboliger/alle_bygninger)*100)}%")
    with c3:
        st.write("**Andre bygninger**")
        andre_bygninger = alle_bygninger - eneboliger
        st.metric(metric_text, value=f"{andre_bygninger:,}".replace(","," "), delta=f"{int((andre_bygninger/alle_bygninger)*100)}%")

################################
################################
################################
df_list = []
for fylke in fylker:
    df = pd.read_csv(f"src/data/matrikkel/{fylke}_summert.csv", sep=',', index_col=0)
    df_list.append(df)
df_concat = pd.concat(df_list)
df_concat.reset_index(inplace=True, drop=True)

def give_building_type(x):
    if x == "Enebolig" or x == "Våningshus" or x == "VÃ¥ningshus" or x == "Enebolig m/hybel/sokkelleil." or x == "Fritidsbygg(hyttersommerh. ol" or x == "Rekkehus" or x == "Tomannsbolig, vertikaldelt" or x == "Tomannsbolig, horisontaldelt" or x == "Andre småhus m/3 boliger el fl" or x == "Andre smÃ¥hus m/3 boliger el fl":
        return "Småhus"
    else:
        return "None"

grouping_mode = st.toggle("Slå sammen eneboliger, tomannsbolig, enebolig m/sokkelleilighet o.l til *Småhus*")
if grouping_mode:
    df_concat['BYGNINGSTYPE_KATEGORISERT'] = df_concat['BYGNINGSTYPE_NAVN'].apply(give_building_type)
    df_concat.loc[df_concat['BYGNINGSTYPE_KATEGORISERT'] == 'Småhus', 'BYGNINGSTYPE_NAVN'] = df_concat['BYGNINGSTYPE_KATEGORISERT']

with st.expander("Bygningsstatistikk per valgt fylke", expanded=False):
    fylker = st.multiselect("Velg fylker", options = fylker, default=fylker)
    n_largest = st.number_input("Filtrering (antall av de *høyeste* som vises i figurene)", value=10)
    if len(fylker) == 0:
        st.warning("Du må velge ett fylke.")
        st.stop()

    tab1, tab2 = st.tabs(["Bruksareal", "Antall"])
    with tab1:
        show_statistics(df = df_concat, selected_y = 'BRUKSAREAL_TOTALT', n_largest = n_largest, fylker=fylker)
    with tab2:
        show_statistics(df = df_concat, selected_y = 'ANTALL', n_largest = n_largest, fylker=fylker)

################################
################################
################################

with st.expander("Utvalgt bygningstype per fylke", expanded=False):
    unique_buildings = list(df_concat["BYGNINGSTYPE_NAVN"].unique())
    if grouping_mode:
        enebolig_index = unique_buildings.index("Småhus")
    else:
        enebolig_index = unique_buildings.index("Enebolig")  
    selected_building = st.selectbox("Valgt bygningstype", options = unique_buildings, index = enebolig_index)
    df_eneboliger = df_concat[df_concat["BYGNINGSTYPE_NAVN"] == selected_building]
    df_eneboliger["GJENNOMSNITTLIG BRA"] = df_eneboliger["BRUKSAREAL_TOTALT"] / df_eneboliger["ANTALL"]
    df_eneboliger.reset_index(inplace=True, drop=True)
    tab1, tab2, tab3 = st.tabs(["Bruksareal", "Antall", "Gj.snitt"])
    with tab1:
        show_aggregated_statistics(df = df_eneboliger, selected_y = "BRUKSAREAL_TOTALT")
    with tab2:
        show_aggregated_statistics(df = df_eneboliger, selected_y = "ANTALL")
    with tab3:
        show_aggregated_statistics(df = df_eneboliger, selected_y = "GJENNOMSNITTLIG BRA")

################################
################################
################################

def getSecret(filename):
    with open(filename) as file:
        secret = file.readline()
    return secret

def profet_api(area, regular_percentage, efficient_percentage, very_efficient_percentage, tynt_losmassedekke_faktor = 0.7, gjennomsnittlig_bra = 190):
    token_url = "https://identity.byggforsk.no/connect/token"
    api_url = "https://flexibilitysuite.byggforsk.no/api/Profet"

    client_id = 'profet_2024'
    client_secret = getSecret('src/csv/secret.txt')

    api_client = BackendApplicationClient(client_id=client_id)
    oauth = OAuth2Session(client=api_client)
    token = oauth.fetch_token(token_url=token_url, client_id=client_id,
            client_secret=client_secret)

    predict = OAuth2Session(token=token)
    
    new_area = area * tynt_losmassedekke_faktor

    antall_etter = int(new_area/gjennomsnittlig_bra)
    st.write(f"Antall før {int(area/gjennomsnittlig_bra)}")
    st.write(f"Antall etter {antall_etter}")
    #regular = area * regular_percentage
    #efficient = area * efficient_percentage
    #very_efficient = area * very_efficient_percentage

    payload = {
        "StartDate": "2023-01-01",             
        "Areas": {
            f"Hou": {f"Reg": new_area},
            #f"Hou": {f"Eff-E": efficient},
            #f"Hou": {f"Vef": very_efficient},
            },
        "RetInd": False,                                        
        #"TimeSeries": {"Tout": temperature_array}
        }

    r = predict.post(api_url, json=payload)
    data = r.json()
    df = pd.DataFrame.from_dict(data)
    df.index = pd.to_datetime(df.index, unit='ms')
    return df, antall_etter

if grouping_mode:
    grouped = df_eneboliger.groupby('FYLKE')
    df_eneboliger = grouped.sum()
    df_eneboliger.reset_index(drop=False, inplace=True)

if len(df_eneboliger) != 15:
    st.stop()

with st.expander("Antakelser", expanded=True):
    df_eneboliger = df_eneboliger[["BRUKSAREAL_TOTALT", "ANTALL", "GJENNOMSNITTLIG BRA", "FYLKE"]]
    
    df_eneboliger["kWh per m2"] = [80, 90, 80, 60, 80, 80, 70, 90, 90, 80, 90, 90, 80, 60, 80]
    with st.form("profet input"):
        #regular_percentage = st.slider("Prosentandel av eneboliger som er lite energieffektive [%]", min_value = 0, value = 70, max_value = 100) / 100
        #efficient_percentage = st.slider("Prosentandel av eneboliger som er middels energieffektive (etter dagens standard) [%]", min_value = 0, value = 25, max_value = 100) / 100
        #very_efficient_percentage = st.slider("Prosentandel av eneboliger som er veldig energieffektive (passivhus) [%]", min_value = 0, value = 5, max_value = 100) / 100
        tynt_losmassedekke_faktor = st.slider("Prosentandel av eneboliger som er på tynt løsmassedekke [%]", min_value = 0, value = 70, max_value = 100) / 100
        
        COP = st.slider("COP", min_value = 2.0, value = 3.5, max_value = 5.0)
        WELL_DEPTH = st.slider("Brønndybde", min_value = 150, value = 300, max_value = 350)
        show_plot = st.toggle("Vis plot", value=False)
        submitted = st.form_submit_button("Kjør beregning")
    if submitted:
        #if regular_percentage + efficient_percentage + very_efficient_percentage != 1:
        #    st.warning("Sammenlagt prosent må være 100%")
        #    st.stop()
        df_eneboliger["ANTALL"] = (df_eneboliger["ANTALL"] * tynt_losmassedekke_faktor).astype(int)
        teller_antall = 0
        for index, row in df_eneboliger.iterrows():
            area = row["BRUKSAREAL_TOTALT"]
            fylke = row["FYLKE"]
            antall = row["ANTALL"]
            gjennomsnittlig_bra = row["GJENNOMSNITTLIG BRA"]
            regular_percentage, efficient_percentage, very_efficient_percentage = 0, 0, 0
            df_profet, antall_etter = profet_api(area, regular_percentage = regular_percentage, efficient_percentage = efficient_percentage, very_efficient_percentage = very_efficient_percentage, tynt_losmassedekke_faktor = tynt_losmassedekke_faktor, gjennomsnittlig_bra = gjennomsnittlig_bra)
            teller_antall = teller_antall + antall_etter
            st.write(f"**{teller_antall}**")
            df_grunnvarme = df_profet[["SpaceHeating", "DHW"]]
            df_grunnvarme.rename(columns = {"SpaceHeating" : "Romoppvarmingsbehov", "DHW" : "Tappevannsbehov"}, inplace=True)
            st.write(f"**{fylke}**")
            fig = plot_2_timeserie(
                df_grunnvarme["Tappevannsbehov"],
                "Tappevannsbehov",
                df_grunnvarme["Romoppvarmingsbehov"],
                "Romoppvarmingsbehov",
                y_min=None,
                y_max=None
                #COLOR_1=TAPPEVANN_FARGE,
                #COLOR_2=ROMOPPVARMING_FARGE,
            )
            if show_plot:
                st.plotly_chart(fig, use_container_width=True)

            grunnvarme_obj = Grunnvarme(objektid = 1, behovstype = "T", df = df_grunnvarme, COP = COP, DEKNINGSGRAD = 100)
            grunnvarme_obj._beregn_grunnvarme()
            fig = plot_3_timeserie(
                grunnvarme_obj.kompressor_arr,
                "Strøm til varmepumpe",
                grunnvarme_obj.levert_fra_bronner_arr,
                "Levert fra brønner",
                grunnvarme_obj.spisslast_arr,
                "Spisslast",
                y_min=None,
                y_max=None
                #COLOR_1=TAPPEVANN_FARGE,
                #COLOR_2=ROMOPPVARMING_FARGE,
            )
            if show_plot:
                st.plotly_chart(fig, use_container_width=True)
            
            well_meters = int(np.sum(grunnvarme_obj.levert_fra_bronner_arr / row["kWh per m2"]))
            average_well_meters = int(well_meters/antall)
            c1, c2 = st.columns(2)
            with c1:
                st.metric("Antall brønnmeter", value = f"{well_meters:,} m".replace(",", " "))
            with c2:
                number_of_wells = int(well_meters/WELL_DEPTH)
                st.metric(f"Antall brønner a {WELL_DEPTH} m dybde", value = f"{number_of_wells:,}".replace(",", " "))

            heat_pump_size = np.max(df_grunnvarme["Romoppvarmingsbehov"] + df_grunnvarme["Tappevannsbehov"])
            #
            df_eneboliger.at[index, 'Varmepumpeeffekt'] = heat_pump_size
            df_eneboliger.at[index, 'Romoppvarmingsenergibehov'] = np.sum(df_grunnvarme["Romoppvarmingsbehov"])
            df_eneboliger.at[index, 'Tappevannsenergibehov'] = np.sum(df_grunnvarme["Tappevannsbehov"])
            df_eneboliger.at[index, 'Termisk energibehov'] = np.sum(df_grunnvarme["Romoppvarmingsbehov"] + df_grunnvarme["Tappevannsbehov"])
            df_eneboliger.at[index, 'Kompressorenergi til varmepumpe'] = np.sum(grunnvarme_obj.kompressor_arr)   
            df_eneboliger.at[index, 'Levert energi fra brønner'] = np.sum(grunnvarme_obj.levert_fra_bronner_arr)   
            df_eneboliger.at[index, 'Energi til spisslast'] = np.sum(grunnvarme_obj.spisslast_arr)
            #
            df_eneboliger.at[index, 'Romoppvarmingseffektbehov'] = np.max(df_grunnvarme["Romoppvarmingsbehov"])
            df_eneboliger.at[index, 'Tappevannseffektbehov'] = np.max(df_grunnvarme["Tappevannsbehov"])
            df_eneboliger.at[index, 'Termisk effektbehov'] = np.max(df_grunnvarme["Romoppvarmingsbehov"] + df_grunnvarme["Tappevannsbehov"])
            df_eneboliger.at[index, 'Kompressoreffekt til varmepumpe'] = np.max(grunnvarme_obj.kompressor_arr)   
            df_eneboliger.at[index, 'Levert effekt fra brønner'] = np.max(grunnvarme_obj.levert_fra_bronner_arr)   
            df_eneboliger.at[index, 'Effekt til spisslast'] = np.max(grunnvarme_obj.spisslast_arr)   
            #           
            df_eneboliger.at[index, 'Antall brønner'] = number_of_wells
            df_eneboliger.at[index, 'Brønnmeter'] = well_meters
            
        df_eneboliger.to_csv(f'src/data/matrikkel/Småhus_summert.csv')

################################
################################
################################

def get_value(df, column, aggregation = "sum"):
    if aggregation == "sum":
        return f"{float(round(df[column].sum()/1000000000,1)):,} TWh".replace(",", " ")
    else:
        return f"{int(round(df[column].sum()/1000,0)):,} GW".replace(",", " ")

with st.expander("Resultater", expanded=True):
    df_results = pd.read_csv("src/data/matrikkel/Småhus_summert.csv")
    st.write(df_results)
    st.metric("Termisk behov", value = get_value(df_results, 'Termisk energibehov', 'sum') + " | " + get_value(df_results, 'Termisk effektbehov', 'max'))
    st.metric("Levert fra brønner", value = get_value(df_results, 'Levert energi fra brønner', 'sum') + " | " + get_value(df_results, 'Levert effekt fra brønner', 'max'))
    st.metric("Antall brønner", value = f"{int(np.sum(df_results['Antall brønner'])):,}".replace(",", " "))
    





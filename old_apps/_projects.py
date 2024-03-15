import streamlit as st
import re 
from geopy.geocoders import Nominatim
from datetime import date
import pandas as pd
import pydeck as pdk
from deta import Deta

deta = Deta("a0558p23_LQWhbxaMFYb3qiEok2Z7sD7JWgEhZYnj")

db = deta.Base("Prosjekter_V2")

def insert_data(project_name, id, project_type, project_status, lat, long, name, date, percentage, checked_sendttilbud, checked_registrertoppdrag, checked_oppdragsbekreftelse, checked_sendtrapport, checked_faktura, workers, comment):
    return db.put({
        "key" : project_name,
        "Oppdragsnummer" : id, 
        "Type" : project_type,
        "Status" : project_status,
        "Latitude" : lat,
        "Longitude" : long, 
        "Innsender" : name,
        "Dato" : date,
        "Prosent" : percentage,
        "Tilbud" : checked_sendttilbud, 
        "Registrert" : checked_registrertoppdrag, 
        "Oppdragsbekreftelse" : checked_oppdragsbekreftelse,
        "Sendt" : checked_sendtrapport,
        "Fakturert" : checked_faktura,
        "Medarbeidere" : workers,
        "Kommentar" : comment
        })

def fetch_all_data():
    res = db.fetch()
    return res.items

def get_data(projectname):
    return db.get(projectname)

def remove_data(projectname):
    return db.delete(projectname)

def address_to_coordinate (adresse):
    geolocator = Nominatim(user_agent="my_request")
    location = geolocator.geocode(adresse, timeout=None, country_codes="NO")
    if location is None:
        lat = 0
        long = 0
    else:
        lat = location.latitude
        long = location.longitude
    return lat, long

    
def new_project(name):
    with st.form("new_entry", clear_on_submit=True):
        c1, c2 = st.columns(2)
        with c1: 
            project_name = st.text_input("*Prosjektnavn")
            project_address = st.text_input("*Adresse eller sted")
            project_id = st.text_input("*Oppdragsnummer")

        with c2:
            project_type = st.multiselect("*Oppdragstype", ["TRT", "TRT & Dimensjonering", "Dimensjonering", "Konseptutredning", "Annet"])
            project_status = st.multiselect("*Oppdragsstatus", ["Pågår", "Tilbud", "Fremtidig", "Fullført", "Nyhetssak"])
            percentage = st.slider("Prosent fullført (%)", min_value = 0, value = 0, max_value=100)

        option_list = ["Randi", "Henrik", "Magne", "Sofie", "Johanne"]
        workers = st.multiselect("Medarbeidere", options=option_list)
        
        comment = st.text_area("Kommentar")
        st.caption("Hvis nyhetssak; lim inn URL i kommentar")
        
        #checked_sendttilbud = st.checkbox("Sendt tilbud", on_change=None) 
        #checked_registrertoppdrag = st.checkbox("Registrert oppdrag", on_change=None)
        #checked_oppdragsbekreftelse = st.checkbox("Sendt oppdragsbekreftelse", on_change=None)
        #checked_sendtrapport = st.checkbox("Sendt rapport", on_change=None)
        #checked_faktura = st.checkbox("Fakturert", on_change=None)

        checked_sendttilbud = False
        checked_registrertoppdrag = False
        checked_oppdragsbekreftelse = False
        checked_sendtrapport = False
        checked_faktura = False

        #if len(project_address) > 0: 
        #    lat, long = 0, 0
        #    lat, long = address_to_coordinate(project_address)
            
            #res = re.findall(r'\w+', project_name)
            #for index, value in enumerate(res):
            #    lat, long = address_to_coordinate(value)
            #    if lat or long > 0:
            #        break

        if st.form_submit_button("Oppdater"):
            lat, long = address_to_coordinate(project_address)
            date_today = date.today().strftime("%d/%m/%Y")
            insert_data(project_name, project_id, project_type[0], project_status[0], lat, long, name, date_today, percentage, checked_sendttilbud, checked_registrertoppdrag, checked_oppdragsbekreftelse, checked_sendtrapport, checked_faktura, workers, comment)
            st.success("Oppdrag registrert!")

def change_project(name):
    ds = fetch_all_data()
    df = pd.DataFrame(ds)
    arr = df["key"].to_numpy()
    selected = st.multiselect("Velg oppdrag", arr)
    if len(selected) > 0:
        with st.form("change", clear_on_submit=False):
            if len(selected) > 0:
                c1, c2 = st.columns(2)
                list = get_data(selected[0])

                with c1:
                    project_name = st.text_input("*Prosjektnavn", value = list["key"])
                    project_id = st.text_input("*Oppdragsnummer", value = list["Oppdragsnummer"])

                with c2:
                    project_status = list["Status"]
                    if project_status == "Pågår":
                        selected_index = 0
                    if project_status == "Tilbud":
                        selected_index = 1
                    if project_status == "Fremtidig":
                        selected_index = 2
                    if project_status == "Fullført":
                        selected_index = 3
                    if project_status == "Nyhetssak":
                        selected_index = 4

                    project_status = st.selectbox("*Oppdragsstatus", ["Pågår", "Tilbud", "Fremtidig", "Fullført", "Nyhetssak"], index=selected_index)

                    percentage = st.slider("*Prosent fullført (%)", min_value = 0, value = list["Prosent"], max_value=100) 

                comment = st.text_area("Kommentar", value = list["Kommentar"])
                #st.write("--")   
                #checked_sendttilbud = st.checkbox("Sendt tilbud?", value = list["Tilbud"], on_change=None) 
                #checked_registrertoppdrag = st.checkbox("Registrert oppdrag?", value = list["Registrert"], on_change=None)
                #checked_oppdragsbekreftelse = st.checkbox("Sendt oppdragsbekreftelse?", value = list["Oppdragsbekreftelse"], on_change=None)
                #checked_sendtrapport = st.checkbox("Sendt rapport?", value = list["Sendt"], on_change=None)
                #checked_faktura = st.checkbox("Fakturert?", value = list["Fakturert"],  on_change=None)

                checked_sendttilbud = False
                checked_registrertoppdrag = False
                checked_oppdragsbekreftelse = False
                checked_sendtrapport = False
                checked_faktura = False

                #--
                
                project_type = list["Type"]

                lat = list["Latitude"]

                long = list["Longitude"]

                workers = list["Medarbeidere"]
                    
            if st.form_submit_button("Oppdater"):
                date_today = date.today().strftime("%d/%m/%Y")
                insert_data(project_name, project_id, project_type, project_status, lat, long, name, date_today, percentage, checked_sendttilbud, checked_registrertoppdrag, checked_oppdragsbekreftelse, checked_sendtrapport, checked_faktura, workers, comment)
                st.success("Oppdrag endret!")


def remove_project():
    ds = fetch_all_data()
    df = pd.DataFrame(ds)
    arr = df["key"].to_numpy()
    key = st.multiselect("Velg oppdrag", arr, key="delete")
    if len(key) > 0:
        with st.form("delte", clear_on_submit=True):
            remove_data(key[0])
            st.form_submit_button("Slett oppdrag")
            
##

def map(df, color_pick):
    init = pdk.Layer(
    type='ScatterplotLayer',
    data=df,
    get_position='[Longitude, Latitude]',
    pickable=True,
    stroked=True,
    radius_max_pixels=10,
    radius_min_pixels=500,
    filled=True,
    line_width_scale=25,
    line_width_max_pixels=5,
    get_fill_color=color_pick,
    get_line_color=[0, 0, 0])

    st.pydeck_chart(pdk.Deck(
    map_style='mapbox://styles/mapbox/streets-v11',
    initial_view_state=pdk.ViewState(
    latitude=64.01487,
    longitude=11.49537,
    pitch=0,
    bearing=0,
    zoom = 3.1
    ),
    layers=[init], tooltip={
    'html': '<b>{key}</b> <br> {Type}, {Oppdragsnummer} <br> Ansvar: {Medarbeidere} <br> {Prosent}% fullført <br> -- <br> <i>{Kommentar} </i>',
    'style': {'color': 'white'}}))

def check_list(df, status_text):
    st.markdown("---")
    st.subheader("Sjekkliste")
    df = df.loc[df['Status'] == status_text]
    df1 = df[["key", "Tilbud", "Registrert", "Oppdragsbekreftelse", "Sendt", "Fakturert"]]
    df1 = df1.rename(columns={"key": "Navn", "Tilbud": "Sendt tilbud?", "Registrert" : "Registrert oppdrag?", "Oppdragsbekreftelse" : "Sendt oppdragsbekreftelse?", "Sendt" : "Sendt rapport?", "Fakturert" : "Sendt faktura?" })
    df1 = df1.set_index('Navn')
    st.write(df1)


def projects(name):
    st.title("Registrere / Endre / Slette")
    with st.expander("Nytt oppdrag"):
        new_project(name)
        
    with st.expander("Endre oppdrag"):
        change_project(name)

    with st.expander("Slett oppdrag"):
        remove_project()

    #--
    st.title("Oppdragsoversikt")
    ds = fetch_all_data()
    df = pd.DataFrame(ds)

    tab1, tab2, tab3, tab4, tab5 = st.tabs(["Pågår", "Tilbud", "Fremtidig", "Fullført", "Nyhetssak"])

    with tab1:
        status_text = "Pågår"
        st.subheader(f"{len(df.loc[df['Status'] == status_text])} pågående oppdrag")
        map(df.loc[df['Status'] == status_text], [255, 195, 88])
        #check_list(df, status_text)
        
    with tab2:
        status_text = "Tilbud"
        st.subheader(f"{len(df.loc[df['Status'] == status_text])} leverte tilbud")
        map(df.loc[df['Status'] == status_text], [29, 60, 52])
        #check_list(df, status_text)

    with tab3: 
        status_text = "Fremtidig"
        st.subheader(f"{len(df.loc[df['Status'] == status_text])} fremtidige oppdrag")
        map(df.loc[df['Status'] == status_text], [183, 220, 143])
        #check_list(df, status_text)

    with tab4: 
        status_text = "Fullført"
        st.subheader(f"{len(df.loc[df['Status'] == status_text])} fullførte oppdrag")
        map(df.loc[df['Status'] == status_text], [183, 220, 143])
        #check_list(df, status_text)

    with tab5: 
        status_text = "Nyhetssak"
        st.subheader(f"{len(df.loc[df['Status'] == status_text])} saker i media")
        map(df.loc[df['Status'] == status_text], [183, 220, 143])
        #check_list(df, status_text)
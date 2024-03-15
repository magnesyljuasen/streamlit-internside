import streamlit as st
from st_keyup import st_keyup
import requests
import time

#  Adresse
class Address:
    def __init__(self):
        self.lat = float
        self.long = float
        self.name = str
        self.area = int

    def search(self, adr):
        options_list = []
        lat_list = []
        long_list = []
        postnummer_list = []
        r = requests.get(f"https://ws.geonorge.no/adresser/v1/sok?sok={adr}&fuzzy=true&treffPerSide=5&sokemodus=OR", auth=('user', 'pass'))
        if r.status_code == 200 and len(r.json()["adresser"]) == 5:   
            for i in range(0, 5):
                json = r.json()["adresser"][i]
                adresse_tekst = json["adressetekst"]
                poststed = (json["poststed"]).capitalize()
                postnummer = json["postnummer"]
                postnummer_list.append(postnummer)
                opt = f"{adresse_tekst}, {poststed}"
                options_list.append(opt)
                lat_list.append(json["representasjonspunkt"]["lat"])
                long_list.append(json["representasjonspunkt"]["lon"])
        return options_list, lat_list, long_list, postnummer_list
            
    def process(self):
        adr = st_keyup("📍 Skriv inn adresse", key="adresse1")
        if len(adr) == 0:
            st.stop()
        options_list, lat_list, long_list, postcode_list = self.search(adr)
        c1, c2 = st.columns(2)
        if len(options_list) > 0:
            with c1:
                s1 = st.checkbox(options_list[0])
                s2 = st.checkbox(options_list[1])
            with c2:
                s3 = st.checkbox(options_list[2])
                s4 = st.checkbox(options_list[3])

            if s1 == False and s2 == False and s3 == False and s4 == False:
                selected_adr = 0
            elif s1 == False and s2 == False and s3 == False and s4 == True:
                selected_adr = options_list[3]
                selected_lat = lat_list[3]
                selected_long = long_list[3]
                selected_postcode = postcode_list[3]  
            elif s1 == False and s2 == False and s3 == True and s4 == False:
                selected_adr = options_list[2]
                selected_lat = lat_list[2]
                selected_long = long_list[2]
                selected_postcode = postcode_list[2]
            elif s1 == False and s2 == True and s3 == False and s4 == False:
                selected_adr = options_list[1]
                selected_lat = lat_list[1]
                selected_long = long_list[1]
                selected_postcode = postcode_list[1]
            elif s1 == True and s2 == False and s3 == False and s4 == False:
                selected_adr = options_list[0]
                selected_lat = lat_list[0]
                selected_long = long_list[0]
                selected_postcode = postcode_list[0]
            else:
                selected_adr = 0
                st.error("Du kan kun velge én adresse!", icon="🚨")
            if selected_adr != 0:
                self.lat = selected_lat
                self.long = selected_long
                self.name = selected_adr
                self.postcode = selected_postcode
            else:
                st.stop()
        else:
            st.stop()
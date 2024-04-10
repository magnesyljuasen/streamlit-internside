import streamlit as st
from PIL import Image
import requests
from streamlit_lottie import st_lottie
import streamlit_authenticator as stauth
import yaml
#import hydralit_components as hc
#import time
import base64

st.set_page_config(
    page_title="Grunnvarme",
    page_icon="🏔️",
    layout="centered"
)

#with hc.HyLoader('', hc.Loaders.standard_loaders,index=[0]):
#    time.sleep(1)

with open("styles/main.css") as f:
    st.markdown("<style>{}</style>".format(f.read()), unsafe_allow_html=True)

#with open('src/login/config.yaml') as file:
#    config = yaml.load(file, Loader=stauth.SafeLoader)

#authenticator = stauth.Authenticate(config['credentials'],config['cookie']['name'],config['cookie']['key'],config['cookie']['expiry_days'])
#name, authentication_status, username = authenticator.login('Asplan Viak🌱 Innlogging for grunnvarme', 'main')

#if authentication_status == False:
#    st.error('Ugyldig brukernavn/passord')
#elif authentication_status == None:
#    st_lottie(requests.get("https://assets3.lottiefiles.com/packages/lf20_szeieqx5.json").json())
#elif authentication_status:
#    with st.sidebar:
#        authenticator.logout('Logg ut', 'sidebar')
    #--
    col1, col2, col3 = st.columns(3)
    with col1:
        image = Image.open('src/data/img/logo.png')
        st.image(image)  
    with col2:
        st.title("Grunnvarme")
        st.write('Internside')
    
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["Lenker", "Apper", "Admin", "Symboler", "Prosjekter"])
    #--
    with tab1:
        c1, c2 = st.columns(2)
        with c1:
            st.write("[• GRANADA](%s)" % "https://geo.ngu.no/kart/granada_mobil/")
            st.write("[• NADAG](%s)" % "https://geo.ngu.no/kart/nadag-avansert/")
            st.write("[• Løsmasser](%s)" % "https://geo.ngu.no/kart/losmasse_mobil/")
            st.write("[• Berggrunn](%s)" % "https://geo.ngu.no/kart/berggrunn_mobil/")
            st.write("[• InSAR](%s)" % "https://insar.ngu.no/")
            st.write("[• UnderOslo](%s)" % "https://kart4.nois.no/underoslo/Content/login.aspx?standalone=true&onsuccess=restart&layout=underoslo&time=637883136354120798&vwr=asv")
            st.write("[• Høydedata](%s)" % "https://hoydedata.no/LaserInnsyn2/")      
        with c2:
            st.write("[• Profilmanual](%s)" % "https://profil.asplanviak.no/")
            st.write("[• Nord Pool](%s)" % "https://www.nordpoolgroup.com/en/Market-data1/#/nordic/table")
            st.write("[• COPCALC](%s)" % "https://www.copcalc.com/tangix/index.php/desktop/index/live/norwegian")
            st.write("[• Grunnlagsdata](%s)" % "https://grunnlagsdata.asplanviak.no/") 
            st.write("[• GeoNorge](%s)" % "https://www.geonorge.no/")
            st.write("[• Saksinnsyn](%s)" % "https://od2.pbe.oslo.kommune.no/kart/")
            st.write("[• AV-kartet](%s)" % "https://kart.asplanviak.no/")     
            st.write("[• Kommunekart](%s)" % "https://www.kommunekart.com/")     
    with tab2:
        c1, c2 = st.columns(2)
        with c1:
            st.write("[• Bergvarmekalkulatoren 1.0](%s)" % "https://bergvarmekalkulator.streamlit.app/")
            st.write("[• Tidligfasevurdering](%s)" % "https://tidligfase-grunnvarme.streamlit.app/")
            st.write("[• Termisk responstest](%s)" % "https://termisk-responstest.streamlit.app/")
            st.write("[• Elhub Nedre Glomma](%s)" % "https://nedre-glomma-forbruksdata.streamlit.app/")
            st.write("[• GeoTermos Ernströmgruppen](%s)" % "https://geotermos-regneeksempel.streamlit.app/")  
            st.write("[• EPZ Nedre Glomma](%s)" % "https://nedre-glomma.streamlit.app/")
            st.write("[• EPZ Hovinbyen](%s)" % "https://hovinbyen.streamlit.app/")
            st.write("[• EPZ Østmarka](%s)" % "https://energianalyes-oestmarka.streamlit.app/")
            st.write("[• EPZ Kringsjå](%s)" % "https://streamlit-kringsjaa.azurewebsites.net/")
            st.write("[• EPZ Bodø](%s)" % "https://demo-energy-plan-zero.streamlit.app/")
        with c2:
            st.write("[• 3D kart](%s)" % "https://asplanviak.maps.arcgis.com/apps/webappviewer3d/index.html?id=66d6a06bc9a84510a4db7262411ffda7")
            st.write("[• Sammenstilling](%s)" % "https://asplanviak.maps.arcgis.com/apps/instant/basic/index.html?appid=901e9d0f94b24ec186bd4e1f7ce426c6")
            st.write("[• Grunnvarmekartet](%s)" % "https://asplanviak.maps.arcgis.com/apps/mapviewer/index.html?webmap=466de4612e0a443f85f413fda02857b5")
            st.write("[• Melhus HUB](%s)" % "https://melhus-asplanviak.hub.arcgis.com/")
            st.write("[• Nedre Glomma](%s)" % "https://experience.arcgis.com/experience/3325ef32e4684d3ea40eecd32db98104/")
            st.write("[• NAP Storymap](%s)" % "https://storymaps.arcgis.com/stories/4b8a1f1d088a49c5bb25dfd67121e3b0")
            st.write("[• NAP Nettdata](%s)" % "https://demo-tensio-data.streamlit.app/") 
            st.write("[• Dashboard Melhus](%s)" % "https://demo-melhus.streamlit.app/")
            st.write("[• Dashboard Kolbotn](%s)" % "https://demo-kolbotn.streamlit.app/")
            st.write("[• Dashboard Røa](%s)" % "https://datalogging-roa.streamlit.app/")
            st.write("[• Geotermos Ernströmgruppen](%s)" % "https://www.geotermos.no/")
    with tab3:
        c1, c2 = st.columns(2)
        with c1:
            st.write("[• OneNote](%s)" % "https://asplanviak.sharepoint.com/sites/10333-03/_layouts/15/Doc.aspx?sourcedoc={8a98f001-87e7-44ee-a92a-0829b4885f29}&action=edit&wd=target%28Sysselsetting.one%7C537d1ee5-fba2-4a28-96e2-3de9aec333f0%2FSysselsetting%7C1c40e3b4-a502-4af9-8a70-602c287675db%2F%29&wdorigin=NavigationUrl")
            st.write("[• Tilbud (Sales)](%s)" % "https://asvsales.crm4.dynamics.com/main.aspx?appid=552e1ed3-ff62-ea11-a811-000d3a4aaf7b&pagetype=entitylist&etn=apv_project&viewid=6eb3c9ad-2190-ed11-aad1-0022489c5e15&viewType=4230")
            st.write("[• Sysselsetting](%s)" % "https://asplanviak.sharepoint.com/:x:/r/sites/10333-03/_layouts/15/Doc.aspx?sourcedoc=%7B16A5245E-E536-4A50-B78A-79AC4835A40F%7D&file=Sysselsetting%20grunnvarme.xlsx&action=default&mobileredirect=true&cid=421904ae-05a4-4426-bbcd-bfb2f0c56fad") 
            #st.write("[• Prosess & miljø](%s)" % "https://asplanviak.sharepoint.com/:x:/r/sites/10362-00-50/_layouts/15/Doc.aspx?sourcedoc=%7B76F0DFE8-561D-49AB-BCD5-BD8C777C0483%7D&file=Prosess%20og%20milj%C3%B8_%20Sysselsetting_2023_A.xlsm&action=default&mobileredirect=true") 
            st.write("[• TRT's](%s)" % "https://asplanviak.sharepoint.com/sites/10333-03/Delte%20dokumenter/General/Termisk%20responstest/Testoversikt.xlsx") 
        with c2:
            st.write("[• Ebooks](%s)" % "https://asplanviak.sharepoint.com/sites/10333-03")
            st.write("[• Gamle Ebooks](%s)" % "http://bikube/Oppdrag/8492/default.aspx")
            st.write("[• Maler](%s)" % "https://asplanviak.sharepoint.com/sites/10333-03/Delte%20dokumenter/General/Maler") 
    with tab4:
        c1, c2 = st.columns(2)
        with c1:
            st.code("°C")
            st.code("W/(m∙K)")
            st.code("(m∙K)/W")
            st.code("Δ")
            st.code("m²")
        with c2:
            st.code("á")
            st.code("∙")
            st.code("±")
            st.code("λ")
            st.code("CO₂")
            st.code("kg/m³")
    with tab5:
        st.write("")
        
    #--
    #c1, c2, c3, c4, c5 = st.columns(5)
    #with c1:
    #    image = Image.open('src/data/img/RKR.png')
    #    st.image(image)
    #with c2:
    #    image = Image.open('src/data/img/HH.png')
    #    st.image(image)
    #with c3:
    #    image = Image.open('src/data/img/SH.png')
    #    st.image(image)
    #with c4:
    #    image = Image.open('src/data/img/JS.png')
    #    st.image(image)
    #with c5:
    #    image = Image.open('src/data/img/MS.png')
    #    st.image(image)
    st_lottie(requests.get("https://assets1.lottiefiles.com/packages/lf20_l22gyrgm.json").json())


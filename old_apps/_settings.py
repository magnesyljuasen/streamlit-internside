import streamlit as st
import streamlit_authenticator as stauth
import yaml
import base64

def settings():
    #st.set_page_config(page_title="AV Grunnvarme", page_icon=":bar_chart:", layout="centered")
    st.set_page_config(page_title="AV Grunnvarme", layout="centered", page_icon="src/data/img/AsplanViak_Favicon_32x32.png")

    with open("src/styles/main.css") as f:
        st.markdown("<style>{}</style>".format(f.read()), unsafe_allow_html=True)

    with open('src/login/config.yaml') as file:
        config = yaml.load(file, Loader=stauth.SafeLoader)
    authenticator = stauth.Authenticate(config['credentials'],config['cookie']['name'],config['cookie']['key'],config['cookie']['expiry_days'])
    name, authentication_status, username = authenticator.login('Asplan Viak🌱 Innlogging for grunnvarme', 'main')
    return name, authentication_status, username, authenticator
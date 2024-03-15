import streamlit as st 

st.set_page_config(
    page_title="Grunnvarme",
    page_icon="🏔️",
)
with open("styles/main.css") as f:
    st.markdown("<style>{}</style>".format(f.read()), unsafe_allow_html=True)
    
st.title("Pygfunction")
st.radio("Brønnplassering", options=["Velg brønnplassering", "Last inn fra fil [CSV]"])
df_well = st.file_uploader("Last opp brønnplassering [CSV]")
df_energy = st.file_uploader("Last opp energigrunnlag (timeserie til/fra brønner) [kW]")
with st.form("Simuleringsparametere"):
    depth = st.number_input("Velg brønndybde [m]", value = 300)
    radius = st.number_input("Velg diameter [mm]", value = 115)
    st.warning("Flere parametere ...")
    st.form_submit_button("Start beregning")

if st.button("Start simulering"):
    st.warning("Temperaturutviklingsplot inn til VP. Interaktive plot, mulighet til å zoome inn / ut av plot. Foreslår å bruke Plotly eller Echarts. ")
    st.warning("Temperaturutviklingsplot ut fra VP. Interaktive plot, ulighet til å zoome inn / ut av plot. Foreslår å bruke Plotly eller Echarts. ")
    


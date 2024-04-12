import streamlit as st 
import pandas as pd
from PIL import Image
import plotly.graph_objects as go

st.set_page_config(
    page_title="Grunnvarme",
    page_icon="🏔️",
)
with open("styles/main.css") as f:
    st.markdown("<style>{}</style>".format(f.read()), unsafe_allow_html=True)

###################################################################
###################################################################
###################################################################

st.title("Uforstyrret temperatur")
st.subheader("Inndata")
uploaded_file = st.file_uploader("Last opp fil (excel)")
with st.expander("Hvordan skal filen se ut?"):
    image = Image.open("src/data/img/uforstyrretTemperaturInput.PNG")
    st.image(image)  
if uploaded_file:
    df = pd.read_excel(uploaded_file)
    st.subheader("Data")
    groundwater_table = st.number_input("Grunnvannstand (m)", value=5, min_value=0, max_value=100, step=1)
    df = df[df["Dybde"] >= groundwater_table]
    df = df.reset_index(drop=True)
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df['Temperatur'], y=df['Dybde'], mode='lines', line=dict(color="Black", width=3)))
    fig.update_yaxes(autorange='reversed')
    fig.add_shape(type="line", x0=min(df['Temperatur']), x1=max(df['Temperatur']), y0=groundwater_table, y1=groundwater_table,line=dict(color="Blue", width=3, dash="dash"))
    fig.update_layout(
        xaxis={'side': 'top'},
        xaxis_title='Temperatur (°C)', 
        yaxis_title='Dybde (m)',
        height=600 
        )
    st.plotly_chart(fig, use_container_width=True)
    with st.expander("Se data"):
        st.dataframe(data=df, use_container_width=True)
    df.reset_index(inplace=True)
    step = 0.0001
    with st.spinner("Beregner uforstyrret temperatur med en geometrisk metode..."):
        mean_value = df["Temperatur"].mean()
        positive_deviation = 0
        negative_deviation = 0
        for i in range(0, 10000):
            #--
            for i in range(0, len(df)-1):
                if df["Temperatur"].iloc[i] > mean_value:
                    x1 = df["Temperatur"].iloc[i] - mean_value
                    x2 = df["Temperatur"].iloc[i+1] - mean_value
                    delta_y = df["Dybde"].iloc[i+1] - df["Dybde"].iloc[i]
                    areal_trekant = delta_y*abs(x1-x2)/2
                    if x1 > x2:
                        langside = x1 - abs(x1-x2)
                    elif x2 < x1:
                        langside = x2 - abs(x1-x2)
                    else:
                        langside = x1
                    areal_rektangel = delta_y*langside
                    totalt_areal = areal_rektangel + areal_trekant
                    positive_deviation += totalt_areal
                elif df["Temperatur"].iloc[i] < mean_value:
                    x1 = mean_value - df["Temperatur"].iloc[i] 
                    x2 = mean_value - df["Temperatur"].iloc[i+1] 
                    delta_y = df["Dybde"].iloc[i+1] - df["Dybde"].iloc[i]
                    areal_trekant = delta_y*abs(x1-x2)/2
                    if x1 > x2:
                        langside = x1 - abs(x1-x2)
                    elif x2 < x1:
                        langside = x2 - abs(x1-x2)
                    else:
                        langside = x1
                    areal_rektangel = delta_y*langside
                    totalt_areal = areal_rektangel + areal_trekant
                    negative_deviation += totalt_areal
            trigger_value = positive_deviation/negative_deviation
            if trigger_value > 1:
                mean_value = mean_value + step
            if trigger_value < 1:
                mean_value = mean_value - step
        
        st.subheader(f"Uforstyrret temperatur = {round(float(mean_value),2)} °C")
        st.write(f"Avvik: {abs(100 - abs(positive_deviation/negative_deviation)*100)} %.")
        st.info("Om avviket er høyt, er det noe feil. Kontrollsjekk resultatene.")
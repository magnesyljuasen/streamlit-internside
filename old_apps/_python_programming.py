import streamlit as st

def python_programming():
    st.title("FAQ")

    st.header("IDE")
    st.write("[Visual Studio Code](%s)" % "https://code.visualstudio.com/")

    with st.expander("YouTube"):
        st.subheader("Python")
        st.write("[Grunnlegende](%s)" % "https://www.youtube.com/watch?v=kqtD5dpn9C8")
        st.write("[Data science](%s)" % "https://www.youtube.com/watch?v=7eh4d6sabA0")
        st.write("[Tips & tricks](%s)" % "https://www.youtube.com/watch?v=F3T8tg2tVKM")
        st.write("[Objektorientert](%s)" % "https://www.youtube.com/watch?v=JeznW_7DlB0")
        
        st.subheader("Streamlit")
        st.write("[Streamlit 1](%s)" % "https://www.youtube.com/c/CodingIsFun/videos")
        st.write("[Streamlit 2](%s)" % "https://www.youtube.com/c/FaniloAndrianasolo/videos")

    st.header("Nytt prosjekt")
    st.subheader("Oppsett")
    st.write("1) Åpne terminal; Windows key -> Skriv cmd -> Command Prompt")
    st.write("2) Naviger til programmeringsmappe i terminal (navigering med kommandoene dir | cd NAVN | cd ..)")
    st.write("3) Lag mappe for prosjekt i programmeringsmappen med mkdir NAVN")
    st.write("4) Når du står i mappe; skriv code. ")
    st.write("*I VS Code -> lag Virtual Environment*")
    st.write("5) python -m venv .venv")
    st.write("6) .venv/scripts/activate")
    st.write("7) ctrl+shift+p; Python select interpreter; .venv")
    st.write("*Som hovedregel bør alle packages installeres i Virtual Environment. For eksempel: pip install numpy | pip install pandas | pip install pygfunction |pip install streamlit*")
    st.write("8) Lag python-fil; main.py ved å klikke new file i venstre hjørne")

    st.header("Eksempler")
    st.subheader("Les .csv og plot")
    st.code(""" 

    #importerer packages
    import pandas as pd
    import numpy as np
    import matplotlib.pyplot as plt

    def show_elspot():
        #laster inn .csv elspot-priser til en pandas DataFrame
        df = pd.read_csv('src/csv/el_spot_hourly_2018.csv', sep=';', on_bad_lines='skip')
        
        #transformerer DataFrame til numpy array
        elspot_arr = np.resize(df.iloc[:, i].to_numpy() / 1000, 8760)

        #hvis vi vil øke alle elementene med 0,4 kroner (f.eks. nettleie)
        elprice_arr = elspot_arr + 0.4

        #nå kan vi plotte strømprisen
        plt.plot(np.arange(0, 1, 8760), elprice_arr)
        plt.show()
        plt.close()

    #kjør funksjon
    show_elspot()
    """)





    


    


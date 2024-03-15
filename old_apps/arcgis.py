import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import random
import numpy as np

from Energianalyse import Energianalyse

from arcgis.gis import GIS
import getpass

st.set_page_config(layout = "wide")

class Fordeling:
    PROSENTFORDELING = {"A" : [70, 20, 10], "B" : [50, 50, 0]}
    def __init__(self, df, omraadeid = "A"):
        #self.valg_fordeling = [70, 20, 10]
        self.df = df
        
    def _add_values_randomly(self, df, kolonnenavn, prosent, verdi = True):
        antall_rader = len(df)
        n_values = int((prosent/100) * antall_rader)  
        random_indices = random.sample(range(antall_rader), n_values)
        random_values = [verdi for _ in range(n_values)]
        df.loc[random_indices, kolonnenavn] = random_values
        
    def endre_byggtabell(self):
        self.df.loc[self.df['Energibronn'] <= 1, 'grunnvarme_start_beregning'] = 1
        
        
        self._add_values_randomly(df = self.df, kolonnenavn = ["fjernvarme_start_beregning"], prosent = 0, verdi = 1)
        self._add_values_randomly(df = self.df, kolonnenavn = ["luft_luft_start_beregning"], prosent = 0, verdi = 1)
        self._add_values_randomly(df = self.df, kolonnenavn = ["solproduksjon_start_beregning"], prosent = 80, verdi = 1)
        
        #self.energibehov_bygningstype = sdf["Byggtype_profet"]
        #self.energibehov_bygningsstandard = sdf["Energistandard_profet"]
        #self.energibehov_areal = sdf["BRUKSAREAL_TOTALT"]
        
        #if self.energibehov_bygningstype == "A":
        #    luftluftprosent = 30
        #else:
        #    luftluftprosent = 10
        """
        for i in range(0, len(self.df)):
            energi_obj = Energianalyse(
            filplassering=r"C:\inetpub\wwwroot\plot\energianalyse_intozero",
            objektid=self.df["OBJECTID"][i],
            energibehov_start_beregning=True,
            # energibehov_temperatur_serie=frost_obj.series_2020_2021,
            energibehov_bygningstype="K",
            energibehov_bygningsstandard="Y",
            energibehov_areal=self.df["BRUKSAREAL_TOTALT"][i],
            solproduksjon_lat=63.452412609974175,
            solproduksjon_lon=10.448158917293863,
            solproduksjon_takflate_vinkel=None,
            solproduksjon_takflate_navn=["A", "B", "C", "D"],
            solproduksjon_takflate_arealer=[None, 200, None, None],
            solproduksjon_takflate_orienteringer=[None, -180, None, None],
            grunnvarme_cop=3.2,
            grunnvarme_dekningsgrad=90,
            grunnvarme_start_beregning=self.df["grunnvarme_start_beregning"][i],
            grunnvarme_energibehov="T",
            solproduksjon_start_beregning=self.df["solproduksjon_start_beregning"][i],
            fjernvarme_start_beregning=self.df["fjernvarme_start_beregning"][i],
            fjernvarme_dekningsgrad=100,
            fjernvarme_energibehov="T",
            luft_luft_start_beregning=self.df["luft_luft_start_beregning"][i],
            luft_luft_dekningsgrad=100,
            luft_luft_cop=2.2,
            visualiser=True,
        )   
            with st.expander(f"Bygg {self.df['OBJECTID'][i]}"):
                #st.write((self.df["grunnvarme_start_beregning"][i]))
                #st.write((self.df["fjernvarme_start_beregning"][i]))
                #st.write((self.df["luft_luft_start_beregning"][i]))
                st.checkbox("Solceller", bool(self.df["solproduksjon_start_beregning"][i]), key = f"{i}")
                col1, col2 = st.columns(2)
                with col1:
                    tab1, tab2, tab3 = st.tabs(["Timeplot", "Varighetskurve", "Data"])
                    with tab1:
                        st.write("**Før**")
                        st.plotly_chart(energi_obj.behovsplot_timeplot, use_container_width=True)
                    with tab2:
                        st.write("**Før**")
                        st.plotly_chart(energi_obj.behovsplot_varighetskurve, use_container_width=True)
                    with tab3:
                        st.dataframe(energi_obj.timeserier_obj.df, use_container_width=True)
                with col2:
                    tab1, tab2, tab3 = st.tabs(["Timeplot", "Varighetskurve", "Data"])
                    with tab1:
                        st.write("**Etter**")
                        st.plotly_chart(energi_obj.nettutveksling_timeplot, use_container_width=True)
                    with tab2:
                        st.write("**Etter**")
                        st.plotly_chart(energi_obj.nettutveksling_varighetskurve, use_container_width=True)
                    with tab3:
                        st.dataframe(energi_obj.timeserier_obj.df, use_container_width=True)
                if i == 5:
                    break
            """
                
with open(r'C:\Users\magne.syljuasen\Desktop\password.txt') as f:
    password = f.readlines()

gis = GIS(
  url="https://www.arcgis.com",
  username="magne.syljuasen",
  password=password
)

item = gis.content.get("176aa005459547bda6f097e20cda4a1b")
flayer = item.layers[0]
# create a Spatially Enabled DataFrame object
sdf = pd.DataFrame.spatial.from_layer(flayer)
sdf['OMRAADE'] = ["A" if i % 2 == 0 else "B" for i in range(len(sdf))]

valgt_omraade = st.radio("Områdevelger", options = ["A", "B"])
valgt_sdf = sdf[sdf["OMRAADE"] == valgt_omraade]
valgt_sdf = valgt_sdf.reset_index(drop=True)


fordeling_obj = Fordeling(df = valgt_sdf)
fordeling_obj.endre_byggtabell()

#count = (fordeling_obj.df["Fjernvarme"] > 0).sum()

#st.write(f"**{int((count / len(fordeling_obj.df)) * 100)} %**")

st.write(fordeling_obj.df)
st.area_chart(fordeling_obj.df[["fjernvarme_start_beregning", "solproduksjon_start_beregning", "grunnvarme_start_beregning", "luft_luft_start_beregning"]])
            
            
            
            
"""
def prosentfordeling(fjernvarme_prosent, grunnvarme_prosent, luftluftprosent):
    # random funksjonen
    return df 
    


def func(byggtabell):
    df = pd.DataFrame(byggtabell)
    df = df.drop("Område A") # velge ut område
    



"""
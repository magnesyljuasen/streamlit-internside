import numpy as np
import pandas as pd
import streamlit as st
import datetime as datetime
import plotly.express as px

class CalculateCosts:
    def __init__(self, energy_demand):
        self.forb = energy_demand.to_numpy()
        
    def regn_ut_strompris(self):
        #Kjører hele beregningen, samt viser input og resultater i streamlit-nettside
        self.streamlit_input()
        self.bestem_prissatser()
        self.dager_i_hver_mnd()
        self.energiledd()
        self.kapasitetsledd()
        self.offentlige_avgifter()
        self.spotpris()
        self.ekstra_nettleie_storre_naring()
        self.hele_nettleie()
        self.totaler()
        #self.plot_resultater()

    def streamlit_input(self):
        with st.form(key="myform", border=False):
            c1, c2, c3 = st.columns(3)
            with c1:
                nettleie_provider = st.selectbox("Nettleieselskap", options=["Tensio", "Glitre", "Tensio fremtidig", "Ingen nettleie"])
                if nettleie_provider == "Tensio":
                    filename = "src/data/input/Prissatser_nettleie_Tensio.xlsx"
                elif nettleie_provider == "Glitre":
                    filename = "src/data/input/Prissatser_nettleie_Glitre.xlsx"
                elif nettleie_provider == "Tensio fremtidig":
                    filename = "src/data/input/Prissatser_nettleie_Tensio_fremtidig.xlsx"
                elif nettleie_provider == "Ingen nettleie":
                    filename = "src/data/input/Prissatser_nettleie_ingen_nettleie.xlsx"
                self.spotprisfil_aar = st.selectbox(label='Årstall for spotpriser',options=['3 kr/kWh om vinteren og 0,5 kr/kWh om sommeren', '2023', '2022', '2021', '2020'],index=0)
                if self.spotprisfil_aar == '3 kr/kWh om vinteren og 0,5 kr/kWh om sommeren':
                    self.spotprisfil_aar = 'Fremtidig'
            with c2:
                self.prissats_filnavn = filename
                self.type_kunde = st.selectbox(label='Type strømkunde',options=['Privatkunde', 'Mindre næringskunde', 'Større næringskunde'],index=0)
                self.sone = st.selectbox(label='Prisområde',options=['NO1','NO2','NO3','NO4','NO5'],index=0)            
            with c3:
                self.paaslag = st.number_input(label='Påslag spotpris (kr/kWh)', value=0.05, step=0.01)
                mva = st.selectbox(label='Priser inkludert mva.', options=["Ja", "Nei"], index=1)
                if mva == "Ja":
                    self.mva = True
                else:
                    self.mva = False
            st.form_submit_button(label='Start beregning')
                
            
        self.skuddaar = False
        self.spotprisfil = 'src/csv/spotpriser_kalkulator.xlsx'

    def bestem_prissatser(self):
        #Leser av prissatser for nettleie fra excel-filen som er lastet opp. Skjer kun hvis man ikke velger konstant pris
        prissats_fil = pd.read_excel(self.prissats_filnavn,sheet_name=self.type_kunde)
        
        if self.type_kunde != 'Større næringskunde':
            if self.mva == False:
                kol0 = 6
                kol00 = 4
            else:
                kol0 = 7
                kol00 = 3
            self.energi = prissats_fil.iloc[0,kol0]                     #Energiledd inkl. fba.
            self.reduksjon_energi = prissats_fil.iloc[1,kol0]
            self.fast_avgift = prissats_fil.iloc[2,kol0]
            self.kap_sats = prissats_fil.iloc[:,kol00]

            self.max_kW_kap_sats = prissats_fil.iloc[:,2]
            self.starttid_reduksjon = prissats_fil.iloc[0,10]                     # Klokkeslett for start av reduksjon i energileddpris
            self.sluttid_reduksjon = prissats_fil.iloc[1,10]
            helg_spm = prissats_fil.iloc[2,10]
            if helg_spm == 'Ja':
                self.helgereduksjon = True
            elif helg_spm == 'Nei':
                self.helgereduksjon = False
        else:
            kol = 1
            if self.mva == False:
                mva_faktor = 1
            elif self.mva == True:
                mva_faktor = 1.25
            
            self.energi_storre_naring = prissats_fil.iloc[2,kol]*mva_faktor
            self.kap_sats_apr_sept = prissats_fil.iloc[5,kol]*mva_faktor
            self.kap_sats_okt_mar = prissats_fil.iloc[3,kol]*mva_faktor
            self.avgift_sats_jan_mar = prissats_fil.iloc[7,kol]*mva_faktor
            self.avgift_sats_apr_des = prissats_fil.iloc[8,kol]*mva_faktor
            self.fastledd_sats = prissats_fil.iloc[0,kol]*mva_faktor
            self.sond_avgift_sats = prissats_fil.iloc[10,kol]*mva_faktor

        self.prissats_fil = prissats_fil

    def dager_i_hver_mnd(self):
        # Lager en vektor som inneholder antal dager i hver måned i året
        if self.skuddaar == True:
            self.dager_per_mnd = np.array([31, 29, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31])
        else:
            self.dager_per_mnd = np.array([31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31])
        
    def energiledd(self):
        # Kun hvis ikke konstante prisverdier: 
        # Regner ut energiledd til nettleien basert på satsen som er lest av. 
        # Ved større næringskunde beregnes den på en annen måte enn ved enkelthusholdning og mindre næringskunde.
        # Returnerer energiledd med timesoppløsning og månedsoppløsning
        energiledd_mnd = np.zeros(12)
        
        if self.type_kunde == 'Større næringskunde':
            energiledd_time = (self.energi_storre_naring/100)*self.forb           # kr

            forrige = 0
            for i in range(0,len(self.dager_per_mnd)):
                energiledd_mnd[i] = np.sum(energiledd_time[forrige:forrige+self.dager_per_mnd[i]*24])
                forrige = forrige + self.dager_per_mnd[i]*24

        else:
            energiledd_time = np.zeros(len(self.forb))
            for i in range(24,len(self.forb)+24,24):
                dagsforb = self.forb[i-24:i]
                dag_nummer = i/24
                
                #Ukedag eller helligdag:
                dagtype ="ukedag"
                if self.helgereduksjon == True:
                    year = int(self.spotprisfil_aar)
                    dato = datetime.datetime(year, 1, 1) + datetime.timedelta(dag_nummer - 1)
                    if dato.weekday() >= 5:         
                        dagtype="helg"
                    
                    if year == 2022:
                        norske_helligdager = [(1, 1), (4, 14), (4, 15), (4, 17), (4, 18), (5, 1), (5, 17), (5, 26), (6, 5), (6, 6), (12, 25), (12, 26),]
                    elif year == 2021:
                        norske_helligdager = [(1, 1), (4, 1), (4, 2), (4, 4), (4, 5), (5, 1), (5, 13), (5, 17), (5, 23), (5, 24), (12, 25), (12, 26),]
                    elif year == 2020:
                        norske_helligdager = [(1, 1), (4, 9), (4, 10), (4, 12), (4, 13), (5, 1), (5, 17), (5, 21), (5, 31), (6, 1), (12, 25), (12, 26),]
                    
                    if (dato.month, dato.day) in norske_helligdager:
                        dagtype="helg"
                
                

                if dagtype == 'ukedag':
                    for j in range(0,len(dagsforb)):
                        if j < self.sluttid_reduksjon or j >= self.starttid_reduksjon:
                            energiledd_time[i-24+j]=dagsforb[j]*(self.energi-self.reduksjon_energi)
                        else:
                            energiledd_time[i-24+j]=dagsforb[j]*(self.energi)
                elif dagtype == 'helg':
                    for j in range(0,len(dagsforb)):
                        energiledd_time[i-24+j]=dagsforb[j]*(self.energi-self.reduksjon_energi)


            for j in range(0,len(self.forb)):                    #Setter energileddet lik 0 i timer med 0 forbruk
                if self.forb[j] == 0:
                    energiledd_time[j] = 0

            forrige = 0
            for k in range(0,len(self.dager_per_mnd)):
                energiledd_mnd[k] = np.sum(energiledd_time[forrige:forrige+self.dager_per_mnd[k]*24])
                forrige = forrige + self.dager_per_mnd[k]*24
        
        self.energiledd_time = energiledd_time
        self.energiledd_mnd = energiledd_mnd

    def kapasitetsledd(self):
        # Kun hvis ikke konstante prisverdier: 
        # Regner ut kapasitetsledd til nettleien basert på satsen som er lest av.
        # Hvis større næringskunde: effektledd = kapasitetsledd. Leser av sats fra fil og bruker denne 
        # Hvis mindre næringskunde eller enkelthusholdning: Finner passende kapasitetstrinn basert på tabell som ble avlest i bestem_prissatser. Bruker den for snitt tre høyeste døgnmakser
        # Returnerer kapasitetsledd med timesoppløsning og månedsoppløsning
        kapledd_mnd = np.zeros(12)
        kapledd_time = []
        forrige = 0
        for i in range(0,len(self.dager_per_mnd)):
            mnd_forb = self.forb[forrige:forrige+self.dager_per_mnd[i]*24]
            forrige = forrige + self.dager_per_mnd[i]*24

            if self.type_kunde == 'Større næringskunde':   
                if 3 <= i <=8: 
                    kap_sats = self.kap_sats_apr_sept
                else:
                    kap_sats = self.kap_sats_okt_mar
                
                kapledd_time_denne_mnd = [((kap_sats/(np.sum(self.dager_per_mnd)))*self.dager_per_mnd[i]*np.max(mnd_forb))/(self.dager_per_mnd[i]*24)] * self.dager_per_mnd[i]*24
                kapledd_time = kapledd_time + (kapledd_time_denne_mnd)
                kapledd_mnd[i] = np.sum(kapledd_time_denne_mnd)

            else:
                forrige_dag = 0
                forrige_mnd = 0
                max_per_dag = np.zeros(self.dager_per_mnd[i])
                for j in range(0,self.dager_per_mnd[i]):
                    dag_forb = mnd_forb[forrige_dag:forrige_dag+24]
                    forrige_dag = forrige_dag + 24
                    max_per_dag[j] = np.max(dag_forb)

                max_per_dag_sort = np.sort(max_per_dag)
                tre_hoyeste = max_per_dag_sort[-3:]
                snitt_tre_hoyeste = np.mean(tre_hoyeste)

                if snitt_tre_hoyeste == 0:                  # Hvis det ikke brukes noe strøm en måned, skal kapledd være 0 denne måneden
                    kapledd_mnd[i] = 0
                else:
                    for k in range(0,len(self.max_kW_kap_sats)):
                        if snitt_tre_hoyeste < self.max_kW_kap_sats[k]:
                            break
                    kapledd_mnd[i] = self.kap_sats[k]

                ant_timer_med_forb = 0
                for l in range(0,len(mnd_forb)):
                    if mnd_forb[l] != 0:
                        ant_timer_med_forb = ant_timer_med_forb+1

                for m in range(0,len(mnd_forb)):
                    if mnd_forb[m] != 0:
                        kapledd_time = kapledd_time + [kapledd_mnd[i]/(ant_timer_med_forb)]
                    elif mnd_forb[m] == 0:
                        kapledd_time = kapledd_time + [0]

                forrige_mnd = forrige_mnd + self.dager_per_mnd[i]*24
        
        kapledd_time = np.array(kapledd_time)

        self.kapledd_time = kapledd_time
        self.kapledd_mnd = kapledd_mnd

    def offentlige_avgifter(self):
        # Kun hvis ikke konstante prisverdier: 
        # Regner ut ekstra offentlige avgifter i nettleien basert på satsen som er lest av.
        # Hvis større næringskunde: Forbruksavgift (da denne ikke er inkludert noe annet sted) kr/kWh
        # Hvis mindre næringskunde: Avlest sats på fast avgift (satt til 0)
        # Hvis privatkunde: Avlest sats på fast avgift (enovaavgift) kr/kWh
        # Returnerer offentlige avgifter med timesoppløsning og månedsoppløsning
        if self.type_kunde == 'Større næringskunde':
            offentlig_mnd = np.zeros(12)
            offentlig_time = []
            forrige = 0
            for i in range(0,len(self.dager_per_mnd)):
                mnd_forb = self.forb[forrige:forrige+self.dager_per_mnd[i]*24]
                forrige = forrige + self.dager_per_mnd[i]*24
                if i <=2:
                    avgift_sats = self.avgift_sats_jan_mar
                else:
                    avgift_sats = self.avgift_sats_apr_des
                
                offentlig_time = offentlig_time + [avgift_sats/100*mnd_forb]
                offentlig_mnd[i] = np.sum([avgift_sats/100*mnd_forb])

            offentlig_time = [item for sublist in offentlig_time for item in sublist]
            offentlig_time = np.array(offentlig_time)

        else:
            offentlig_mnd = np.zeros(12)
            forrige = 0
            for i in range(0,len(self.dager_per_mnd)):
                offentlig_mnd[i] = np.sum(self.forb[forrige:forrige+self.dager_per_mnd[i]*24])*self.fast_avgift
                forrige = forrige + self.dager_per_mnd[i]*24
            offentlig_time = self.forb*self.fast_avgift
        
        self.offentlig_time = offentlig_time
        self.offentlig_mnd = offentlig_mnd

    def spotpris(self):
        # Hvis ikke konstante prisverdier: Leser av riktig kolonne (sone og år) i spotpristabell
        # Regner ut spotpris med timesoppløsning og månedsoppløsning. Hvis ikke konstante prisverdier tas hensyn til mva og påslag
        spot_sats = pd.read_excel(self.spotprisfil,sheet_name=self.spotprisfil_aar)
        self.spot_sats = spot_sats
        spot_sats = spot_sats.loc[:,self.sone]+self.paaslag
        if self.mva == True:
            spot_time = self.forb*spot_sats
        elif self.mva == False:
            spot_time = self.forb*(spot_sats/1.25)
        spot_mnd = np.zeros(12)
        forrige = 0
        for k in range(0,len(self.dager_per_mnd)):
            spot_mnd[k] = np.sum(spot_time[forrige:forrige+self.dager_per_mnd[k]*24])
            forrige = forrige + self.dager_per_mnd[k]*24
        
        self.spot_time = spot_time
        self.spot_mnd = spot_mnd

    def ekstra_nettleie_storre_naring(self):
        # Kun hvis ikke konstante prisverdier:
        # Leser av og Regner ut ekstra deler av nettleien som kun finnes for større næringskunder: Fastledd og næringsavgift til energifondet
        # Fordeler denne kun mellom timene som har >0 forbruk
        if self.type_kunde == 'Større næringskunde':
            fastledd_mnd = np.zeros(12)
            fond_avgift_mnd = np.zeros(12)
            fastledd_time = []
            fond_avgift_time =[]

            forrige = 0
            for i in range(0,len(self.dager_per_mnd)):
                mnd_forb = self.forb[forrige:forrige+self.dager_per_mnd[i]*24]
                forrige = forrige + self.dager_per_mnd[i]*24
                
                if np.sum(mnd_forb) == 0:
                    fastledd_mnd[i] = 0
                    fond_avgift_mnd[i] = 0
                else:
                    fastledd_mnd[i] = (self.fastledd_sats/(np.sum(self.dager_per_mnd)))*self.dager_per_mnd[i]
                    fond_avgift_mnd[i] = (self.sond_avgift_sats/np.sum(self.dager_per_mnd))*self.dager_per_mnd[i]

                # Fordeler de faste avgiftene likt mellom de timene i måneden som har >0 forbruk:
                ant_timer_med_forb = 0
                for l in range(0,len(mnd_forb)):
                    if mnd_forb[l] != 0:
                        ant_timer_med_forb = ant_timer_med_forb+1

                for m in range(0,len(mnd_forb)):
                    if mnd_forb[m] != 0:
                        fastledd_time = fastledd_time + [fastledd_mnd[i]/(ant_timer_med_forb)]
                        fond_avgift_time = fond_avgift_time + [fond_avgift_mnd[i]/(ant_timer_med_forb)]
                    elif mnd_forb[m] == 0:
                        fastledd_time = fastledd_time + [0]
                        fond_avgift_time = fond_avgift_time + [0]

            self.fastledd_time = fastledd_time
            self.fastledd_mnd = fastledd_mnd
            self.fond_avgift_time = fond_avgift_time
            self.fond_avgift_mnd = fond_avgift_mnd 

    def hele_nettleie(self):
        # Regner ut total nettleie som sum av de ulike delene, avhengige av hvilke som er aktuelle i ulike tilfeller
        if self.type_kunde == 'Større næringskunde':
            tot_nettleie_time = self.fastledd_time+self.energiledd_time+self.kapledd_time+self.offentlig_time+self.fond_avgift_time
            tot_nettleie_mnd = self.fastledd_mnd+self.energiledd_mnd+self.kapledd_mnd+self.offentlig_mnd+self.fond_avgift_mnd                 
        
        else:
            tot_nettleie_time = self.energiledd_time+self.kapledd_time+self.offentlig_time
            tot_nettleie_mnd = self.energiledd_mnd+self.kapledd_mnd+self.offentlig_mnd
                
        self.tot_nettleie_time = tot_nettleie_time
        self.tot_nettleie_mnd = tot_nettleie_mnd

    def totaler(self):
        # Regner ut total strømpris som sum av total nettleie og spotpris
        tot_nettleie_aar = np.sum(self.tot_nettleie_mnd)
        self.tot_strompris_aar = tot_nettleie_aar + np.sum(self.spot_mnd)
        self.tot_strompris_time = self.tot_nettleie_time+self.spot_time
        self.tot_forb = np.sum(self.forb)

    def plot_resultater(self):
        # Skriver ut og plotter alle resultater til streamlit-nettsiden
        # Hvilke ting som plottes i figurene er avhengig av valg i input.
        st.header('Resultater')
        if self.mva == True:
            mva_str = 'inkl. mva.'
        elif self.mva == False:
            mva_str = 'ekskl. mva.'
        
        if self.type_kunde == 'Større næringskunde':
            timesnettleie_til_plot = pd.DataFrame({'Energiledd':self.energiledd_time, 'Effektledd':self.kapledd_time, 'Forbruksavgift':self.offentlig_time, 'Fastledd':self.fastledd_time, 'Avgift til energifondet':self.fond_avgift_time})
            plot_farger = ['#1d3c34', '#FFC358', '#48a23f', '#b7dc8f', '#FAE3B4']
        else:
            timesnettleie_til_plot = pd.DataFrame({'Energiledd inkl. fba.':self.energiledd_time, 'Kapasitetsledd':self.kapledd_time, 'Andre offentlige avgifter':self.offentlig_time})
            plot_farger = ['#1d3c34', '#FFC358', '#48a23f']

        fig1 = px.line(timesnettleie_til_plot, title='Nettleie for '+self.type_kunde.lower()+' med gitt forbruk '+mva_str, color_discrete_sequence=plot_farger)
        fig1.update_layout(xaxis_title='Timer', yaxis_title='Timespris med gitt forbruk (kr)',legend_title=None)
        st.plotly_chart(fig1)  
        
        plot_tittel = 'Strømpris for '+self.type_kunde.lower()+' med gitt forbruk i '+self.sone+' basert på spotpriser i '+self.spotprisfil_aar+' '+mva_str
    
        # Plotter nettleie og strømpris med timesoppløsning
        timestrompriser_til_plot = pd.DataFrame({"Total strømpris" : self.tot_strompris_time, "Spotpris" : self.spot_time, "Nettleie" : self.tot_nettleie_time})
        fig2 = px.line(timestrompriser_til_plot, title=plot_tittel, color_discrete_sequence=['#1d3c34', '#FFC358', '#48a23f'])
        fig2.update_layout(xaxis_title='Timer', yaxis_title='Timespris med gitt forbruk (kr)',legend_title=None)
        st.plotly_chart(fig2)


        # Plotter nettleie og strømpris med månedsoppløsning
        mnd_akse = ['Januar', 'Februar', 'Mars', 'April', 'Mai', 'Juni', 'Juli', 'August', 'September', 'Oktober', 'November', 'Desember']
        maanedsstrompriser_til_plot = pd.DataFrame({'Måned':mnd_akse,'Spotpris':self.spot_mnd,'Nettleie':self.tot_nettleie_mnd})
        fig5 = px.bar(maanedsstrompriser_til_plot,x='Måned',y=['Spotpris','Nettleie'],title=plot_tittel, color_discrete_sequence=['#FFC358', '#48a23f'])
        fig5.update_layout(yaxis_title='Månedspris med gitt forbruk (kr)',legend_title=None)
        st.plotly_chart(fig5)

        c1, c2, c3 = st.columns(3)
        with c1:
            st.metric('Totalt forbruk:',f"{round(self.tot_forb)} kWh")
        with c2:
            st.metric('Total energikostnad dette året:',f"{round(self.tot_strompris_aar)} kr")
        with c3:
            st.metric('Gjennomsnittlig energikostnad per kWh',f"{round(self.tot_strompris_aar/self.tot_forb,3)} kr/kWh")
        


# Mulige forbedringer/tillegg:
# Forbruksavgift er nå inkludert i energiledd, men den bør kanskje skilles ut og plasseres i kategorien "offentlige avgifter" sammen med Enovaavgift.
# Mindre næringskunder skal muligens også betale Enovapåslag på 800 kr/år, men dette er kun lagt inn for større næringskunder.
# Excel-filene med prissatser kan eventuelt bygges inn i koden i stedet for at de skal lastes opp. Kan også legge til prissatser fra flere nettselskaper.
# Bør kanskje legges inn noe som gjør at koden fungerer selv om timesforbruket er fra et skuddår.
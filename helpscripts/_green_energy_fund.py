import numpy_financial as npf

class GreenEnergyFund:
    def __init__(self):
        # Define economic parameters
        self.INFLASJON = 2
        self.RENTE_SWAP_5 = 2.25
        self.RENTEMARGINAL = 1.5
        self.RENTEKOST = self.RENTE_SWAP_5 + self.RENTEMARGINAL
        self.BELAANING = 0.30
        self.ØKONOMISK_LEVETID = 15
        self.MANAGEMENT_FEE = 1
        self.BOLAGSSKATT = 22
        self.AV_VARME = 20
        self.AV_SOL = 10
        self.ENOVA = 1600
        self.AVKASTNINGSKRAV_BYGG = 4

        # Define investment parameters
        self.effekt_vp = 200
        self.levert_varme = 900000
        self.COP = 3.5
        self.el_vp = self.levert_varme / self.COP
        self.elpris = 1
        self.boring = 4.83e6
        self.vp = 4e6
        self.enova_bidrag = self.ENOVA * self.effekt_vp
        self.sol = 0
        
        self.driftskostnad = 50000
        self.LEASING_EAAS = 450000
        self.REINVEST_VP_2 = 2 * 7e5
        self.REINVEST_VP_1 = 0.2 * self.vp

        self.calculate_investment_cost_15()
        self.calculate_investment_cost_eaas()

        self.LEASING_15 = 0.102 * self.investering # gjør om til parameter på 15

        

    def calculate_investment_cost_15(self):
        self.investering = (
            (self.boring + self.vp - self.enova_bidrag)
            * (1 + self.AV_VARME / 100)
            + self.sol * (1 + self.AV_SOL / 100)
        )
        self.arvode_av_varme = 0
        self.arvode_av_sol = 0
    
    def calculate_investment_cost_eaas(self):
        self.arvode_av_varme = (self.boring + self.vp - self.enova_bidrag) * (self.AV_VARME / 100)
        self.arvode_av_sol = self.sol * (self.AV_SOL / 100)
        self.investering = self.boring + self.vp - self.enova_bidrag + self.arvode_av_varme + self.sol + self.arvode_av_sol

    def seb_15_year(self):
        self.calculate_investment_cost_15()

        egenkapital = (1 - self.BELAANING) * self.investering

        laan = self.investering - egenkapital
        resterende_laan = laan

        reinvest_vp1 = self.REINVEST_VP_1 * (1 + self.INFLASJON / 100) ** self.ØKONOMISK_LEVETID 
        
        year = list(range(0, 16))
        # Initialize arrays to store results
        yearly_fee = [0] * len(year)
        management = [0] * len(year)
        reinvest = [0] * len(year)
        avskrivning = [0] * len(year)
        yearly_drift = [0] * len(year)
        EBIT = [0] * len(year)
        Rentekostnad = [0] * len(year)
        EBT = [0] * len(year)
        yearly_bolagsskatt = [0] * len(year)
        gevinst_etter_skatt = [0] * len(year)
        ammortering = [0] * len(year)
        cash_flow = [0] * len(year)
        sum_cash_flow = [0] * len(year)

        # Calculate financial parameters
        for i in range(len(year)):
            yearly_fee[i] = self.LEASING_15 * (1 + self.INFLASJON / 100) ** year[i]
            management[i] = -self.investering * self.MANAGEMENT_FEE / 100
            reinvest[i] = -reinvest_vp1 / self.ØKONOMISK_LEVETID
            avskrivning[i] = -self.investering / self.ØKONOMISK_LEVETID
            yearly_drift[i] = -self.driftskostnad * (1 + self.INFLASJON / 100) ** year[i]
            EBIT[i] = yearly_fee[i] + management[i] + avskrivning[i] + yearly_drift[i]
            Rentekostnad[i] = -resterende_laan * (self.RENTEKOST / 100)
            EBT[i] = EBIT[i] + Rentekostnad[i]
            yearly_bolagsskatt[i] = min([0, -EBT[i] * self.BOLAGSSKATT / 100])
            gevinst_etter_skatt[i] = EBT[i] + yearly_bolagsskatt[i]

            if i <= self.ØKONOMISK_LEVETID:
                ammortering[i] = -laan / self.ØKONOMISK_LEVETID
            else:
                ammortering[i] = 0
            self.resterende_laan = laan + sum(ammortering)
            cash_flow[i] = gevinst_etter_skatt[i] - yearly_drift[i] - avskrivning[i]
            sum_cash_flow[i] = cash_flow[i] + ammortering[i]

        IRR = npf.irr([-egenkapital] + sum_cash_flow)

        # Calculate the price for the customer in year 1
        pris = self.LEASING_15 + self.el_vp * self.elpris
        pris_kWh = pris / self.levert_varme

        driftsnetto = (self.levert_varme - self.el_vp) * self.elpris * (1 + self.INFLASJON / 100) ** year[-1] + yearly_drift[-1] + reinvest[-1]
        verdi_anlegg = driftsnetto / (self.AVKASTNINGSKRAV_BYGG / 100) # SKRIV UT

        # pris etter år 15
        pris_15 = self.el_vp * self.elpris

        #print("Investment:", self.Investering)
        #print("Internal Rate of Return (IRR): {:.2%}".format(IRR))
        #print("Price for the customer in year 1:", Pris)
        #print("Price per kWh:", Pris_kWh)

        return self.investering, IRR, pris, pris_kWh, pris_15, verdi_anlegg

    def seb_energy_as_a_service(self):

        self.calculate_investment_cost_eaas()

        egenkapital = (1 - self.BELAANING) * self.investering
        laan = self.investering - egenkapital
        resterende_laan = laan

        # Define the number of years
        year = list(range(0, 16))
        reinvest_vp2 = self.REINVEST_VP_2 * (1 + self.INFLASJON / 100) ** self.ØKONOMISK_LEVETID

        # Initialize arrays to store results
        yearly_fee = [0] * len(year)
        management = [0] * len(year)
        yearly_drift = [0] * len(year)
        reinvest = [0] * len(year)
        avskrivning = [0] * len(year)
        EBIT = [0] * len(year)
        rentekostnad = [0] * len(year)
        EBT = [0] * len(year)
        yearly_bolagsskatt = [0] * len(year)
        gevinst_etter_skatt = [0] * len(year)
        ammortering = [0] * len(year)
        cash_flow = [0] * len(year)
        sum_cash_flow = [0] * len(year)

        # Calculate financial parameters for script2
        for i in range(len(year)):
            yearly_fee[i] = self.LEASING_EAAS * (1 + self.INFLASJON / 100) ** year[i]
            management[i] = -self.investering * self.MANAGEMENT_FEE / 100
            yearly_drift[i] = -self.driftskostnad * (1 + self.INFLASJON / 100) ** year[i]
            reinvest[i] = -reinvest_vp2 / self.ØKONOMISK_LEVETID
            avskrivning[i] = -self.investering * 0.025
            EBIT[i] = yearly_fee[i] + management[i] + avskrivning[i] + yearly_drift[i] + reinvest[i]
            rentekostnad[i] = -resterende_laan * (self.RENTEKOST / 100)
            EBT[i] = EBIT[i] + rentekostnad[i]
            yearly_bolagsskatt[i] = min([0, -EBT[i] * self.BOLAGSSKATT / 100])
            gevinst_etter_skatt[i] = EBT[i] + yearly_bolagsskatt[i]

            if i <= 100:
                ammortering[i] = -laan / 100
            else:
                ammortering[i] = 0
            resterende_laan = laan + sum(ammortering)
            cash_flow[i] = gevinst_etter_skatt[i] - yearly_drift[i] - avskrivning[i]
            sum_cash_flow[i] = cash_flow[i] + ammortering[i]

        # Calculate the value of the facility
        driftsnetto = (self.levert_varme - self.el_vp) * self.elpris * (1 + self.INFLASJON / 100) ** year[-1] + yearly_drift[-1] + reinvest[-1]
        verdi_anlegg = driftsnetto / (self.AVKASTNINGSKRAV_BYGG / 100) # SKRIV UT

        # Calculate the internal rate of return for script2
        IRR = npf.irr([-egenkapital] + sum_cash_flow[:-1] + [sum_cash_flow[-1] + verdi_anlegg - resterende_laan])

        # Calculate the price for the customer in year 1
        pris = self.LEASING_EAAS + self.el_vp * self.elpris
        pris_kWh = pris / self.levert_varme

        #print("Investment:", Investering)
        #print("Internal Rate of Return (IRR): {:.2%}".format(IRR))
        #print("Price for the customer in year 1:", Pris)
        #print("Price per kWh:", Pris_kWh)
        #print("Arvode_AV_Varme:", Arvode_AV_Varme)
        #print("Arvode_AV_Sol:", Arvode_AV_Sol)

        return self.investering, IRR, pris, pris_kWh, self.arvode_av_varme, self.arvode_av_sol, verdi_anlegg
        
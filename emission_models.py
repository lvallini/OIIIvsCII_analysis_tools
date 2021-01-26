import numpy as np
import scipy
import pyneb as pn
from ion_structure import Ni,NF,NHIyi,NHIy0
from cooling_rates import lambdaCIIh,lambdaCIIe

O3 = pn.Atom('O', 3) #load the OIII ion from pyneb

# Set the oxygen abundance. 
#We assume Asplund et al 2009 abundance at Zsun and that Ao scales linearly with Z. Z in solar units
def oxygen_abundance(Z):
    Ao=4.90e-4
    return Ao*Z

# Set the carbon abundance. 
#We assume Asplund et al 2009 abundance at Zsun and that Ac scales linearly with Z. Z in solar units
def carbon_abundance(Z):
    Ac=2.7e-4 
    return Ac*Z
     
# Gas surface density from the SFR surface density assuming the Kennicutt-Schmidt relation. 
#Sigma_sfr in Msun/yr/kpc^2, k is the burstiness parameter
def Sigmag_of_Sigmasfr(Sigma_sfr, k, n=1.4):
    out=(((k*(10.0**-12))**-1)*Sigma_sfr)**(1./n)
    return out

# Ionizaton parameter from SFR and gas surface densities. 
#Eq. 38 Ferrara et al. 2019. Sigma_sfr in Msun/yr/kpc^2, Sigma_g in Msun/kpc^2
def U_Sigmag_Sigmasfr(Sigma_sfr, Sigma_g):
    out= (1.7e+14)*(Sigma_sfr/(Sigma_g*Sigma_g))
    return out

# Emerging [CII] flux for the density bounded case dens bounded case.  Eq. 34 in Ferrara et al. 2019
def fcii_DB(n, Z, U, column, TPDR, THII):
    g2_cii=4. # 
    g1_cii=2.
    E12_158um = 0.0079 #energy between the eV
    A21_158um = 2.4e-6 #s^-1

    fcii_neutral    = 0.0

    if(n<=3300):
        # rates:  
        lambdaCII4   = lambdaCIIe(THII)
        fcii_ionized_DB = n*carbon_abundance(Z)*lambdaCII4*NHIy0(U, Z, column)
    else:
        LTE_pop_levels_HII = (g2_cii/g1_cii)*np.exp((-1.602e-12*E12_158um)/(1.38065e-16*THII))
        fcii_ionized_DB    = LTE_pop_levels_HII * carbon_abundance(Z) * A21_158um * (1.602e-12*E12_158um)* NHIy0(U, Z, column)
        
    out= fcii_neutral + fcii_ionized_DB

    return out

# Emerging [CII] flux in the ionization bounded case, and for NF> N0. Equations 30, 31 in Ferrara et al. 2019
def fcii_IB_N0(n, Z, U, column, TPDR, THII):
    g2_cii=4.
    g1_cii=2.
    E12_158um = 0.0079 #eV
    A21_158um = 2.4e-6 #s^-1
    # ionized column density
    N_i= Ni(U,Z)
    
    if(n<=3300):
        # rates:  
        lambdaCII    = lambdaCIIh(TPDR)
        lambdaCII4   = lambdaCIIe(THII)

        # cii from neutral
        fcii_neutral    = n*carbon_abundance(Z)*lambdaCII*(column - N_i)
        # cii from ionized layer
        fcii_ionized_IB = n*carbon_abundance(Z)*lambdaCII4*NHIyi(U, Z)
    
        out             = fcii_neutral + fcii_ionized_IB
    else:
        LTE_pop_levels_PDR = (g2_cii/g1_cii)*np.exp((-1.602e-12*E12_158um)/(1.38065e-16*TPDR))
        LTE_pop_levels_HII = (g2_cii/g1_cii)*np.exp((-1.602e-12*E12_158um)/(1.38065e-16*THII))
        #
        fcii_neutral       = LTE_pop_levels_PDR * carbon_abundance(Z) * A21_158um * (1.602e-12*E12_158um)* (column - N_i)
        fcii_ionized_IB    = LTE_pop_levels_HII * carbon_abundance(Z) * A21_158um * (1.602e-12*E12_158um)* NHIyi(U, Z)
        #
        out                = fcii_neutral + fcii_ionized_IB
        
    return out


# Emerging [CII] flux in the ionization bounded case, and for NF< N0. Equations 30, 32 in Ferrara et al. 2019
def fcii_IB_NF(n, Z, U, column, TPDR, THII):
    g2_cii    = 4.
    g1_cii    = 2.
    E12_158um = 0.0079 #eV
    A21_158um = 2.4e-6 #s^-1
    # ionized column density
    N_i= Ni(U,Z)
    # NL column density
    N_F=NF(U, Z)
    
    if(n<=3300):
        # rates:  
        lambdaCII    = lambdaCIIh(TPDR)
        lambdaCII4   = lambdaCIIe(THII)
        # cii from neutral
        fcii_neutral = n*carbon_abundance(Z)*lambdaCII*(N_F - N_i)
        # cii from ionized layer
        fcii_ionized_IB=n*carbon_abundance(Z)*lambdaCII4*NHIyi(U, Z)
        
    else:
        LTE_pop_levels_PDR = (g2_cii/g1_cii)*np.exp((-1.602e-12*E12_158um)/(1.38065e-16*TPDR))
        LTE_pop_levels_HII = (g2_cii/g1_cii)*np.exp((-1.602e-12*E12_158um)/(1.38065e-16*THII))
        fcii_neutral       = LTE_pop_levels_PDR * carbon_abundance(Z) * A21_158um * (1.602e-12*E12_158um)* (N_F - N_i)
        fcii_ionized_IB    = LTE_pop_levels_HII * carbon_abundance(Z) * A21_158um * (1.602e-12*E12_158um)* NHIyi(U, Z)

    out= fcii_neutral + fcii_ionized_IB
        
    return out


# The following three equations are instrumental for the Eq. 35 in Ferrara et al. 2019.
def sigma_cii_DB(logn, Z, k, Sigma_sfr):
    n             = 10**logn
    SS_g          = Sigmag_of_Sigmasfr(Sigma_sfr, k)
    UU            = U_Sigmag_Sigmasfr(Sigma_sfr, SS_g)
    column_density= (SS_g*10**22.0)/7.5e+7
    ff            = fcii_DB(n, Z, UU, column_density, 100., 1e+4)
    SS_CII        = ff*2.474e+9
    return SS_CII

def sigma_cii_IB_N0(logn, Z, k, Sigma_sfr):
    n             = 10**logn
    SS_g          = Sigmag_of_Sigmasfr(Sigma_sfr, k)
    UU            = U_Sigmag_Sigmasfr(Sigma_sfr, SS_g)
    column_density= (SS_g*10**22.0)/7.5e+7
    ff            = fcii_IB_N0(n, Z, UU, column_density, 100., 1e+4)
    SS_CII        = ff*2.474e+9
    return SS_CII

def sigma_cii_IB_NF(logn, Z, k, Sigma_sfr):
    n             = 10**logn
    SS_g          = Sigmag_of_Sigmasfr(Sigma_sfr, k)
    UU            = U_Sigmag_Sigmasfr(Sigma_sfr, SS_g)
    column_density= (SS_g*10**22.0)/7.5e+7
    ff            = fcii_IB_NF(n, Z, UU, column_density, 100., 1e+4)
    SS_CII        = ff*2.474e+9
    return SS_CII

# Eq. 35 in Ferrara et al. 2019
def Sigma_CII158(logn, Z, k, Sigma_sfr):
    
    SS_g           = Sigmag_of_Sigmasfr(Sigma_sfr, k)
    UU             = U_Sigmag_Sigmasfr(Sigma_sfr, SS_g)
    column_density = (SS_g*10**22.0)/7.5e+7
    N_i            = Ni(UU,Z)
    N_F            = NF(UU,Z)
    
    if(column_density<N_i):
         out = sigma_cii_DB(logn, Z, k, Sigma_sfr)
    elif(column_density<N_F):
         out=sigma_cii_IB_N0(logn, Z, k, Sigma_sfr)
    else:
         out=sigma_cii_IB_NF(logn, Z, k, Sigma_sfr)
    return out
    
# Part related to the [OIII] line emission (88 and 52 micron), 
#details can be found in Vallini et al. 2021. Emissivity computed with Pyneb.
def foiii88(n, Z, U, THII):
    # emissivity for 88micron:  
    emOIII        = O3.getEmissivity(THII, n, wave='88.3m') # erg s^-1 cm^3
    # ionized column density
    N_i           = Ni(U,Z)
    #correction for the presence of OII in the ionized region
    fo3           = np.array([0.10994503, 0.73298314, 0.96966708])
    Uo3           = np.array([-3.5, -2.5, -1.5])
    Xoiii         = np.interp(np.log10(U), Uo3, fo3)
    n1_ntot       = O3.getPopulations(THII, n)[1]
    Nh_oiii       = oxygen_abundance(Z)*Xoiii*N_i
    foiii_ionized = emOIII * n * Nh_oiii
    return foiii_ionized

def foiii52(n, Z, U, THII):
    #emissivity for 52micron:  
    emOIII        = O3.getEmissivity(THII, n, wave='51.8m') #erg s^-1 cm^3
    # ionized column density
    N_i           = Ni(U,Z)
    #correction for the presence of OII in the ionized region
    fo3           = np.array([0.10994503, 0.73298314, 0.96966708])
    Uo3           = np.array([-3.5, -2.5, -1.5])
    Xoiii         = np.interp(np.log10(U), Uo3, fo3)
    n2_ntot       = O3.getPopulations(THII, n)[2]
    Nh_oiii       = oxygen_abundance(Z)*Xoiii*N_i
    foiii_ionized = emOIII * n * Nh_oiii
    return foiii_ionized 

def Sigma_OIII88(logn, Z, k, Sigma_sfr):
    n    = 10**logn
    SS_g = Sigmag_of_Sigmasfr(Sigma_sfr, k)
    UU   = U_Sigmag_Sigmasfr(Sigma_sfr, SS_g)
    ff   = foiii88(n, Z, UU, 1e+4)
    out  = ff*2.474e+9 # 
    return out

def Sigma_OIII52(logn, Z, k, Sigma_sfr):
    n    = 10**logn
    SS_g = Sigmag_of_Sigmasfr(Sigma_sfr, k)
    UU   = U_Sigmag_Sigmasfr(Sigma_sfr, SS_g)
    ff   = foiii52(n, Z, UU, 1e+4)
    out  = ff*2.474e+9
    return out

def Delta(logn, Z, k, Sigma_sfr):

    from empirical import delooze_fit_resolved
    
    out = np.log10(Sigma_CII158(logn, Z, k, Sigma_sfr))-np.log10(delooze_fit_resolved(Sigma_sfr))
    return out




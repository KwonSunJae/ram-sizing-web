# -*- coding: utf-8 -*-
"""
Created on Wed Apr 23 20:24:11 2014

@author: Maxim
"""

def m_to_ft(length):
    return 3.2808399*float(length)

def ft_to_m(length):
    return float(length)/3.2808399

def sqm_to_sqft(area):
    return 10.76391044943201*float(area)

def sqft_to_sqm(area):
    return float(area)/10.76391044943201

def kg_to_lb(mass):
    return 2.20462262 * float(mass)

def lb_to_kg(mass):
    return float(mass)/2.20462262

def kgf_to_lbf(force):
    return float(force)*2.20462262

def lbf_to_kgf(force):
    return float(force)/2.20462262

def cubm_to_gal(volume):
    return float(volume)*264.172052

def gal_to_cubm(volume):
    return float(volume)/264.172052

def nm_to_m(distance):
    return float(distance)*1852

def m_to_nm(distance):
    return float(distance)/1852

def N_to_lbf(force):
    return float(force)/4.44822162

def lbf_to_N(force):
    return float(force)*4.44822162

def kt_to_msec(speed):
    return float(speed)*0.514444444

def msec_to_kt(speed):
    return float(speed)/0.514444444

def sfcImp_to_sfcSI(sfc):
    """Convert specific fuel consumption from imperial units lb/(h*lbf) to 
    SI units kg/(h*kgf)"""
    return 

def lbft2_to_pa(pressure):
    return pressure*47.880258888889

def pa_to_lbft2(pressure):
    return pressure/47.880258888889

def run_test1():
    print (m_to_ft(1))
    print (sqm_to_sqft(15))

if __name__=="__main__":
    run_test1()
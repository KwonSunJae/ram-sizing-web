# -*- coding: utf-8 -*-
"""
Created on Fri Jan 10 15:08:33 2014

@author: Maxim
"""
from math import exp
from adsp.utils import constants as const


__all__ = ['FlightConditions', 'ISAtmosphere', 'get_density_altitude']


class FlightConditions(object):
    """
    stores flight conditions of an aircraft. Atmosphere properties are calculated
    using ISAtmosphere and stored in self.atmosphere
    
    Parameters
    ----------
    speed : float
        if speed > 3.0 then speed is treated as airspeed [m/sec]
        if speed < 3.0 then treated as Mach number
        
    altitude : float, meters
        altitude
    
    dT : degrees Kelvin
        temperature deviation from standard atmosphere

    refLength : float, meters
        reference length to calculate Reynolds number
    """
    def __init__(self,speed, altitude, dT=0.0, refLength=1.0):
        #self.atm = ISAtmosphere(altitude,dT)
        self.g = const.GRAVITY_ACCEL
        self.atm = ISAtmosphere_mason(altitude,dT)
        self.refLength = float(refLength)
        if speed <= 0.1:
            self.Mach = float(speed)
            self.velocity = self.Mach * self.atm.soundSpeed
        else:
            self.velocity = float(speed)
            self.Mach = self.velocity / self.atm.soundSpeed
        self.Re = self.atm.density*self.velocity*self.refLength/self.atm.viscosity
        self.dynamicPressure = self.atm.density*self.velocity*self.velocity/2.0
    
    def set_speed(self,speed):
        """
        sets new speed
        """
        self.__init__(float(speed),self.atm.altitude,self.atm.dT,self.refLength)

    def set_altitude(self,altitude):
        """
        sets new altitude. Atmosphere parameters are recalculated using new altitude.
        """
        self.__init__(self.velocity,altitude,self.atm.dT,self.refLength)
        
    def set_ref_length(self,refLength):
        """
        sets new reference length
        """
        self.__init__(self.velocity,self.atm.altitude,self.atm.dT,float(refLength))
    
    def get_wall_spacing(self,yplus=1.0):
        """
        calculates minimum wall spacing based on yplus value.
        """
        Cf = 0.026 / (self.Re**(1/7))
        rho = self.atm.density
        tauWall = Cf*rho * self.velocity**2/2
        Ufric = (tauWall/rho)**0.5
        ds = yplus*self.atm.viscosity / (Ufric*rho)
        return ds


class ISAtmosphere:
    def __init__(self,altitude,dT=0,gas='air'):
        altitude = float(altitude)
        P0 = 101325.0
        T0 = 288.15
        G0 = 9.80665
        R  = 287.04
        GAMMA = 1.4
        if altitude<11000:
            T = T0 - 6.5 * altitude / 1000 + dT
            P = P0 * (1 - 0.0065 * altitude / T0) ** 5.2561
        else:
            T11 = T0 - 6.5 * 11000 / 1000 + dT
            P11 = P0 * (1 - 0.0065 * 11000 / T0) ** 5.2561
            T = T11 + dT
            P = P11 * exp(-G0 / (R * T11) * (altitude - 11000))  
        rho = P / (R * T)
        a = (GAMMA * R * T) ** 0.5
        self.dT          = dT
        self.gas         = gas
        self.altitude    = altitude
        self.temperature = T
        self.pressure    = P
        self.soundSpeed  = a
        self.density     = rho
        self.set_sutherland_viscosity(self.gas)
        self.g = const.get_gravity_acceleration(altitude)
    
    def set_sutherland_viscosity(self,gas):
        if gas == 'ideal-gas':
            mu0 = 1.716e-5
            T0  = 273.11
            C   = 110.56
        elif gas == 'air':
            mu0 = 18.27e-6
            T0  = 291.15
            C   = 120.0
        mu = mu0*(T0+C)/(self.temperature+C)*((self.temperature/T0)**(3/2))
        self.viscosity = mu
    
    def set_altitude(self,altitude):
        self.__init__(altitude,self.dT,self.gas)

class ISAtmosphere_mason(object):
    def __init__(self,altitude,dT=0,gas='air'):
        h = float(altitude)
        dT = float(dT)
        
        GAMMA = 1.4
        R = 287.0
        
        K = 34.163195
        C1 = 3.048e-4
        T0 = 288.15
        P0 = 101325
        RHO0 = 1.225
        C1 = 0.001
        A0 = 340.294
        
        H = C1*h/(1 + C1*h/6356.766)
        #print H
        if H<11.0:
            T = 288.15 - 6.5*H;
            PP = (288.15/T)**(-K/6.5)
        elif H<20.0:
            T = 216.65;
            PP = 0.22336*exp(-K*(H-11)/216.65)
        elif H<32.0:
            T = 216.65 + (H-20);
            PP = 0.054032*(216.65/T)**K;
        elif H<47.0:
            T = 228.65 + 2.8*(H-32);
            PP = 0.0085666*(228.65/T)**(K/2.8)
        elif H<51.0:
            T = 270.65;
            PP = 0.0010945*exp(-K*(H-47)/270.65)
        elif H<71.0:
            T = 270.65 - 2.8*(H-51);
            PP = 0.00066063*(270.65/T)**(-K/2.8)
        elif H<84.852:
            T = 214.65 - 2*(H-71);
            PP = 3.9046e-5*(214.65/T)**(-K/2)
        else:
            raise ValueError('Altitude is too high')
        
        self.altitude = h
        self.soundSpeed1 = (GAMMA*R*T)**0.5
        self.density = PP/(T/288.15) *RHO0
        TS = T/288.15
        self.dT = dT
        self.temperature = T0*TS
        self.soundSpeed = A0*TS**0.5
        self.pressure = PP *P0
        self.set_sutherland_viscosity(gas)
        self.ReM = self.density*self.soundSpeed/self.viscosity

    def set_sutherland_viscosity(self,gas):
        if gas == 'ideal-gas':
            mu0 = 1.716e-5
            T0  = 273.11
            C   = 110.56
        elif gas == 'air':
            mu0 = 18.27e-6
            T0  = 291.15
            C   = 120.0
        mu = mu0*(T0+C)/(self.temperature+C)*((self.temperature/T0)**(3/2))
        self.viscosity = mu

def get_density_altitude(density):
    """
    Finds altitude with given density. 
    
    Parameters
    ----------
    density : float, kg/m^3
         atmospheric density
    
    Note
    ----
    approximated method is valid for altitude < 11km
    """
    a =  3.30858898e-09
    b = -1.13728614e-04
    c =  1.22202839e+00 - density
    return (-b - (b*b - 4.0*a*c)**0.5) / (2.0*a)


# --- debug ---
def run_test1():
    fc = FlightConditions(24,150.)
    print (fc.atm.density)
    print (fc.atm.viscosity)
    print (fc.atm.soundSpeed)
    print (fc.Re)
    print (fc.Mach)
    alt = get_density_altitude(1.0)
    fc.set_altitude(alt)
    print (fc.atm.density)
    
    print (const.get_gravity_acceleration(10000))

def run_test2():
    from numpy import linspace, zeros
    import matplotlib.pyplot as plt
    n = 50
    h = linspace(0,85e3,n)
    T1 = zeros(n)
    p1 = zeros(n)
    rho1 = zeros(n)
    a1 = zeros(n)
    T2 = zeros(n)
    p2 = zeros(n)
    rho2 = zeros(n)
    a2 = zeros(n)
    isa1 = ISAtmosphere(0)
    isa2 = ISAtmosphere_mason(0)
    for i,_h in enumerate(h):
        isa1.__init__(_h)
        isa2.__init__(_h)
        T1[i] = isa1.temperature
        p1[i] = isa1.pressure
        rho1[i] = isa1.density
        a1[i] = isa1.soundSpeed
        T2[i] = isa2.temperature
        p2[i] = isa2.pressure
        rho2[i] = isa2.density
        a2[i] = isa2.soundSpeed1
    plt.figure(1)
    # plt.hold()
    plt.grid()
    plt.xlabel('Temperature, K')
    plt.ylabel('altitude, m')
    plt.plot(T1,h,'bo-')
    plt.plot(T2,h,'rd-')
    plt.figure(2)
    # plt.hold()
    plt.grid()
    plt.plot(h,p1,'bo-')
    plt.plot(h,p2,'rd-')
    plt.figure(3)
    # plt.hold()
    plt.grid()
    plt.plot(h,rho1,'bo-')
    plt.plot(h,rho2,'rd-')
    plt.figure(4)
    # plt.hold()
    plt.grid()
    plt.plot(h,a1,'bo-')
    plt.plot(h,a2,'rd-')
    plt.show()

def run_test3():
    fc = FlightConditions(12,1.2e4)
    print (fc.Re/1e6)
    print (fc.Mach)
    print (fc.velocity)
    print (fc.atm.temperature)
    print (fc.atm.pressure)
    print (fc.atm.soundSpeed)
    
if __name__=="__main__":
    run_test2()
    run_test3()    


# -*- coding: utf-8 -*-
"""
Created on Wed Jan 08 13:37:27 2014

@author: Maxim
"""

GRAVITY_ACCEL = 9.80665
EARTH_RADIUS = 6371.0e3
DENSITY_GASOLINE = 710.0 #kg/m3
DENSITY_KEROSENE = 800.0

def get_gravity_acceleration(altitude):
    c = (EARTH_RADIUS/(EARTH_RADIUS+altitude))**2.0
    return GRAVITY_ACCEL*c

def getValue(self,name):
    value=None
    try:value=self.dict.get(name)
    except:print('error in constants(): entry not found')
    return value

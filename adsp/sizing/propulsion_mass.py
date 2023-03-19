
import numpy as np

# NOTE: power values are in kW

def _calc_propeller_mass(prop_diameter, powerReq, num_of_blade):
    # [ propeller design for conceptual turboprop aircraft - pg 49]
    propeller_mass = 1.1*(prop_diameter*powerReq*np.sqrt(num_of_blade))**0.52
    return propeller_mass

def _motor_regression(max_cont_power):
    max_cont_power_kw = max_cont_power
    motor_mass = 0.208*max_cont_power_kw + 2.23   # kg
    return motor_mass

def _inverter_regression(max_cont_power):
    max_cont_power_kw = max_cont_power # kW
    inverter_mass = 0.0553*max_cont_power_kw + 1.721 # kg
    return inverter_mass
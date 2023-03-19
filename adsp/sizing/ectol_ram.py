import numpy as np
import math
import adsp.sizing.propulsion_mass as eProp
import adsp.utils.flight_conditions as fc
from scipy.optimize import fsolve

atm0 = fc.ISAtmosphere(0, 0, 'air') # sea level
g = atm0.g # gravity accel


# effy product to convert mechanical to electrial
def calc_product_efficiency(combus):
    combus.effy_product_cruise = combus.effy_propeller_cruise*\
        combus.effy_controller*combus.effy_motor
    combus.effy_product_climb  = combus.effy_propeller_climb*\
        combus.effy_controller*combus.effy_motor
    combus.effy_product_takeoff = combus.effy_propeller_takeoff*\
        combus.effy_controller*combus.effy_motor
    combus.effy_product = combus.effy_controller*combus.effy_motor

def calc_total_mass(combus, missionInput, params):
    calc_prop_system_mass(combus, params)
    calc_energy_system_mass(combus, missionInput)
    mtow = (combus.mass_propulsion_sys + combus.mass_energy\
        + combus.mass_payload) / (1-(combus.mass_frac_struct\
        + combus.mass_frac_subsys + combus.mass_frac_avionics))
    combus.mass_total_out = mtow
    combus.mass_struct  = combus.mass_frac_struct*combus.mass_total_out
    combus.mass_subsys  = combus.mass_frac_subsys*combus.mass_total_out
    combus.mass_avionics = combus.mass_frac_avionics*combus.mass_total_out
    combus.mass_frac_OEM = (combus.mass_struct+combus.mass_subsys\
                              +combus.mass_avionics
                              +combus.mass_propulsion_sys)/combus.mass_total_out
    combus.mass_frac_payload = combus.mass_payload/combus.mass_total_out
    combus.mass_frac_energy  = combus.mass_energy/combus.mass_total_out


def calc_prop_system_mass(combus, params):
    # TODO: controller mass
    calc_prop_mass(combus, params)
    calc_motor_mass(combus, params)
    calc_controller_mass(combus, params)
    combus.mass_propulsion_sys = combus.num_of_propellers_ctol\
        *(combus.mass_propeller + combus.coef_propulsion_install\
        * (combus.mass_motor + combus.mass_controller))


def calc_energy_system_mass(combus, missionInput):
    mission_analysis(combus, missionInput)
    totalEnergyReq = combus.energy_mission
    calc_battery_mass(combus, energy=totalEnergyReq)
    # calc_battery_mass_2(combus, energy=totalEnergyReq)
    combus.mass_energy = combus.mass_battery
    
    
def mission_analysis(combus, missionInput):
    missionSeg = len(missionInput.seg)
    totalEnergy = 0
    totalDistance = 0
    totalTime     = 0
    mission = None
    for i in range(missionSeg):
        if missionInput.seg[i].name == 'TAKEOFF':
            distance = missionInput.seg[i].range
            altitude = missionInput.seg[i].start_altitude
            params = {}
            params['distance_takeoff'] = distance
            params['altitude']             = altitude
            calc_takeoff_distance_elec_power_req(combus, mission, params)
            combus.time_takeoff    =  distance/combus.speed_liftoff
            combus.energy_takeoff  = combus.power_takeoff * combus.time_takeoff
            # totalEnergy += combus.energy_takeoff
            # totalDistance +=distance
            # totalTime     +=combus.time_takeoff
            totalEnergy +=0
            totalDistance +=0
            totalTime +=0
        elif missionInput.seg[i].name == 'CLIMB':
            rateOfClimb = missionInput.seg[i].speed
            start_altitude = missionInput.seg[i].start_altitude
            end_altitude   = missionInput.seg[i].end_altitude
            distance       = abs(end_altitude-start_altitude)
            combus.time_climb   = distance /rateOfClimb
            params = {}
            params['rate_of_climb'] = rateOfClimb       
            params['altitude']      = abs(start_altitude+end_altitude)/2
            calc_rate_of_climb_elec_power_req(combus, mission, params)
            combus.energy_climb = combus.power_climb *  combus.time_climb
            totalEnergy  += combus.energy_climb
            totalDistance +=distance
            totalTime     +=combus.time_climb  
        elif missionInput.seg[i].name == 'CRUISE':
            distance = missionInput.seg[i].range
            speed    = missionInput.seg[i].speed
            altitude = missionInput.seg[i].start_altitude
            combus.time_cruise = distance / speed
            params = {}
            params['altitude'] = altitude
            params['speed_cruise'] = speed
            calc_level_flight_elec_power_req(combus, mission, params)
            combus.energy_cruise = combus.power_cruise * combus.time_cruise
            totalEnergy += combus.energy_cruise
            totalDistance +=distance
            totalTime     +=combus.time_cruise
        elif missionInput.seg[i].name == 'LOITER':
            time = missionInput.seg[i].duration
            speed = missionInput.seg[i].speed
            altitude = missionInput.seg[i].start_altitude
            combus.time_cruise = time
            combus.distance_cruise = speed*time
            params['altitude'] = altitude
            params['speed_cruise'] = speed
            calc_level_flight_elec_power_req(combus, mission, params)
            combus.energy_cruise = combus.power_cruise * combus.time_cruise
            totalEnergy += combus.energy_cruise
            totalDistance +=distance
            totalTime     +=combus.time_cruise
        elif missionInput.seg[i].name == 'DESCENT':
            rateOfDescent = missionInput.seg[i].speed
            start_altitude = missionInput.seg[i].start_altitude
            end_altitude   = missionInput.seg[i].end_altitude
            totalEnergy  += 0#combus.energy_descent
            totalDistance +=0
            totalTime     +=0
        elif missionInput.seg[i].name == 'LANDING':
            distance = missionInput.seg[i].range
            altitude = missionInput.seg[i].start_altitude
            calc_landing_distance_elec_power_req(combus, altitude, distance)
            totalEnergy += 0
            totalDistance +=0
            totalTime     +=0
        else:
            print ("%s This segment analysis is not available"\
                .missionSeg.seg[i].name)
        combus.energy_mission = totalEnergy 
        combus.energy_total   = combus.energy_mission
        combus.range          = totalDistance
        combus.endurance      = totalTime

def calc_prop_mass(combus, params):
    power_total     = combus.mass_total_inp*g * combus.power_loading/combus.effy_propeller_cruise
    # effy_propeller   = combus.effy_propeller_cruise
    combus.power_propeller_req = power_total 
    # Power for one propeller Watt
    P_unit = combus.power_propeller_req / combus.num_of_propellers_ctol
    P_unit_kw = P_unit*1e-3
    if combus.num_of_propeller_blades == 2:
        kp  =  0.56 
    elif combus.num_of_propeller_blades == 3:
        kp  = 0.52
    elif 3 < combus.num_of_propeller_blades <= 6:
        kp  = 0.49
    else:
        raise ValueError('Unknown number of propeller blades')

    combus.diam_propeller = kp * (P_unit_kw)**0.25
    # Propeller Regerssion model
    # mass_propeller = regress._propeller_regression(combus.diam_propeller)
    mass_propeller = eProp._calc_propeller_mass(combus.diam_propeller, \
                                                  P_unit_kw, combus.num_of_propeller_blades)
    combus.mass_propeller = mass_propeller
    combus.mass_propeller_total = combus.mass_propeller*combus.num_of_propellers_ctol

def calc_motor_mass(combus, params):
    combus.power_motor_req = combus.power_propeller_req\
        / combus.effy_motor
    P_unit = combus.power_motor_req / combus.num_of_propellers_ctol 
    P_unit_kw = P_unit*1e-3
    mass_motor = eProp._motor_regression(P_unit_kw)
    combus.mass_motor       = mass_motor
    combus.mass_motor_total = combus.mass_motor  * combus.num_of_propellers_ctol


def calc_controller_mass(combus, params):
    effy_controller = combus.effy_controller    
    combus.controller_power_req = combus.power_motor_req/effy_controller
    P_unit = combus.power_motor_req/combus.num_of_propellers_ctol
    P_unit_kw = P_unit*1e-3
    # motor Regression model
    mass_controller  = eProp._inverter_regression(P_unit_kw)
    combus.mass_controller = mass_controller
    combus.mass_controller_total = combus.mass_controller \
        *combus.num_of_propellers_ctol


def calc_battery_mass(combus, energy):
    batt_energy = energy / (combus.coef_batt_usable_energy * combus.effy_batt)
    # batt spec energy in [Wh/kg]
    combus.mass_battery = batt_energy / (3600*combus.spec_energy_batt_wh_per_kg)

# === constraints ===
def calc_stall_speed(combus, mission, params):
    combus.speed_stall = np.sqrt(2 * combus.wing_loading/ (
        atm0.density * combus.CL_max))


def calc_best_endurance_condition(combus, mission, params):
    atm = fc.ISAtmosphere(params['altitude'])
    combus.speed_endurance_best = np.sqrt(2/(atm.density)*\
                                   combus.wing_loading*np.sqrt(combus.k/(3*combus.CD_0)))
    combus.speed_cruise = combus.speed_endurance_best
    
    params['speed_cruise'] = combus.speed_endurance_best
    calc_level_flight_elec_power_req(combus, mission, params)
    combus.specific_endurance = 1/combus.power_cruise
    
def calc_max_range_speed(combus, mission, params):
    atm = fc.ISAtmosphere(params['altitude'])
    combus.speed_range_best = np.sqrt(2/(atm.density)\
                                      *(combus.wing_loading*np.sqrt(combus.k/combus.CD_0)))
    print ("Range_speed", combus.speed_range_best)
    # params['speed_cruise'] = combus.speed_range_best
    #params['speed_cruise'] = combus.speed_range_best
    calc_level_flight_elec_power_req(combus, mission, params)
    combus.specific_air_range = combus.speed_range_best/combus.power_cruise

def calc_level_flight_max_speed(combus, mission, params):
    # [Aircraft performance- an engineering approach pg 265]
    atm = fc.ISAtmosphere(params['altitude'])
    def func(Vmax):
        lhs = combus.power_loading*combus.effy_propeller_cruise
        rhs = 0.5*atm.density*Vmax**3*(1/combus.wing_loading)*combus.CD_0\
            +(2*combus.k*combus.wing_loading/(atm.density*Vmax))
        return (lhs-rhs)**2
    Vmax = fsolve(func, 500,xtol=1e-3)[0] 
    combus.speed_max = Vmax
    params['speed_cruise'] = combus.speed_max
    calc_level_flight_elec_power_req(combus, mission, params)
    combus.power_cruise_speed_max = combus.power_cruise
       
def calc_max_rate_of_climb(combus, mission, params):
    # [Gudmusson pg 834]
    atm = fc.ISAtmosphere(params['altitude'])
    combus.speed_climb_best = np.sqrt(2/(atm.density)*\
                               combus.wing_loading*np.sqrt(combus.k/(3*combus.CD_0)))
    # [Gudmussion pg 869]
    combus.lift_to_drag_ratio_max = 1/np.sqrt(4*combus.CD_0*combus.k)    
    # [Gudmusson pg 834]
    ROC_max = combus.effy_propeller_climb*combus.power_loading - \
        ( combus.speed_climb_best*1.1547/combus.lift_to_drag_ratio_max)
    combus.rate_of_climb = ROC_max
    combus.climb_angle   = np.degrees(np.arcsin((combus.rate_of_climb\
        / combus.speed_climb_best)))
    params['rate_of_climb'] = combus.rate_of_climb
    calc_rate_of_climb_elec_power_req(combus, mission, params)

                            
def calc_takeoff_distance(combus, mission, params):
    # ref:: [Gudmundsson pg 806]
    calc_stall_speed(combus, mission, params)
    combus.speed_liftoff = 1.2 * combus.speed_stall
    combus.speed_ground_roll_avg = combus.speed_liftoff/np.sqrt(2)
    field = fc.FlightConditions(combus.speed_ground_roll_avg,
        params['altitude'])
    thrust_avg = combus.power_motor_total * combus.num_of_propellers_ctol\
        * combus.effy_propeller_takeoff / combus.speed_ground_roll_avg
    drag_avg = combus.area_wing * field.dynamicPressure\
        * combus.CD_takeoff
    lift_avg = combus.area_wing * field.dynamicPressure\
        * combus.CL_takeoff
    combus.distance_ground_roll = combus.speed_liftoff**2\
        * combus.weight_total_inp\
        / (2 * field.g * (thrust_avg - drag_avg)
        - combus.coef_ground_friction\
        * (combus.weight_total_inp - lift_avg))
    Vtr = 1.15*combus.speed_stall
    R = Vtr**2/(0.2*atm0.g)
    height_transition   = R*(1-np.cos(np.radians(combus.climb_angle)))
    distance_transition = np.sqrt(R**2-(R-combus.height_obstacle)**2)
    distance_climb_out  = (combus.height_obstacle - height_transition)\
        / (np.tan(np.radians(combus.climb_angle)))
    combus.distance_takeoff  = combus.distance_ground_roll + distance_transition \
        + distance_transition + distance_climb_out    
    params['distance_ground_roll'] = combus.distance_ground_roll
    params['distance_takeoff']      = combus.distance_takeoff
    calc_takeoff_distance_elec_power_req(combus, mission, params)

    
def calc_landing_distance(combus, mission, params):
    # Gudmussion [935]
    
    distance_landing  = 5*combus.wing_loading*(1/combus.CL_max)+ combus.distance_approach
    combus.distance_landing = distance_landing
    params['distance_landing'] = distance_landing
    calc_landing_distance_elec_power_req(combus, mission, params)
    

def calc_max_range(combus, mission, params):
    # print (combus.power_loading, combus.wing_loading)
    # calc_max_range_speed(combus, mission, params)
    atm = fc.ISAtmosphere(params['altitude'])
    combus.speed_range_best = np.sqrt(2/(atm.density)\
                                      *(combus.mass_total_inp*g/combus.area_wing*np.sqrt(combus.k/combus.CD_0)))
    params['speed_cruise'] = combus.speed_range_best
    #params['speed_cruise'] = 95
    #combus.speed_range_best = params['speed_cruise']
    calc_level_flight_elec_power_req(combus, mission, params)
    combus.specific_air_range = combus.speed_range_best/combus.power_req
    combus.range_max = combus.specific_air_range*combus.spec_energy_batt_wh_per_kg*3600\
        *combus.mass_battery*combus.effy_batt
    combus.range_max_km = combus.range_max*1e-3

def calc_max_endurance(combus, mission, params):
    calc_best_endurance_condition(combus, mission, params)
    combus.endurance_max = combus.specific_endurance\
        *combus.spec_energy_batt_wh_per_kg * 3600 * combus.mass_battery\
        *combus.effy_batt
    combus.endurance_max_hr = combus.endurance_max/3600

        
# ==== power required calculation funciton from given parameters ==== #          
def calc_rate_of_climb_elec_power_req(combus, mission, params):    
    # [Gudmundsson eq 3-3]
    calc_product_efficiency(combus)
    atm = fc.ISAtmosphere(params['altitude'])

    combus.speed_climb_best = np.sqrt(2/(atm.density)*\
                               combus.wing_loading*np.sqrt(combus.k/(3*combus.CD_0)))
    # [Gudmussion pg 869]
    combus.lift_to_drag_ratio_max = 1/np.sqrt(4*combus.CD_0*combus.k)    
    # [Gudmusson pg 834]
    ROC = params['rate_of_climb']
    combus.power_loading_climb = (ROC + combus.speed_climb_best*1.1547/combus.lift_to_drag_ratio_max)\
        / combus.effy_propeller_climb
    combus.thrust_to_weight_req = combus.power_loading_climb*combus.effy_propeller_climb \
        / combus.speed_climb_best
    combus.power_climb= combus.power_loading_climb*combus.mass_total_inp*g\
        / combus.effy_product

def calc_takeoff_distance_elec_power_req(combus, mission, params):
    calc_stall_speed(combus, mission, params)
    combus.speed_liftoff = 1.2 * combus.speed_stall
    field = fc.FlightConditions(combus.speed_liftoff/np.sqrt(2), 
        params['altitude'])
    tw_req = combus.speed_liftoff**2 / (2*g*params['distance_takeoff'])\
        + field.dynamicPressure*combus.CD_takeoff / combus.wing_loading\
        + combus.coef_ground_friction * (1 - field.dynamicPressure\
        * combus.CL_takeoff / combus.wing_loading)
    combus.thrust_to_weight_req = tw_req
    combus.thrust_req = tw_req * combus.mass_total_inp * g 
    combus.power_req = combus.thrust_req * field.velocity\
          / combus.effy_product_takeoff
    combus.power_takeoff= combus.power_req
    combus.power_loading_takeoff = combus.power_takeoff*combus.effy_product/(combus.weight_total_inp)
          
def calc_level_flight_elec_power_req(combus, mission, params):
    calc_product_efficiency(combus)
    slf = fc.FlightConditions(params['speed_cruise'], params['altitude'])
    tw_req = slf.dynamicPressure * combus.CD_0 * (1/combus.wing_loading)\
         + combus.k * (1/slf.dynamicPressure) * combus.wing_loading
    combus.thrust_to_weight_req = tw_req
    combus.thrust_req = tw_req * combus.mass_total_inp * g
    combus.power_req = combus.thrust_req * slf.velocity\
           / combus.effy_product_cruise
    combus.power_cruise= combus.power_req
    combus.power_loading_cruise = combus.power_cruise*combus.effy_product/(combus.mass_total_inp*g)


def calc_landing_distance_elec_power_req(combus, mission, params):
    combus.power_landing= 0.0
    combus.power_loading_landing= combus.power_landing/(combus.mass_total_inp*g)  
    
def calc_stall_speed_wing_loading(combus, mission, params):
    atm = fc.ISAtmosphere(0.0)
    vstall = params['speed_stall']
    combus.wing_loading_speed_stall = 0.5*atm.density*vstall**2*combus.CL_max
    
    
    
    
    
    
    
    
    
    
    
    
    
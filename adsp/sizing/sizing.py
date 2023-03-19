from scipy.optimize import fmin_slsqp, fsolve
import numpy as np

import matplotlib.pyplot as plt
import matplotlib.patheffects as patheffects
import plotly.graph_objects as go

import adsp
import adsp.sizing.ectol_ram as ram


__all__ = ['SizingOptimization']

g = adsp.utils.constants.GRAVITY_ACCEL

class SizingOptimization(object):
    def __init__(self, input_filename, combus_name='sizing-ram'):       
        self.cb = adsp.combus.CommunicationBus2(combus_name)
        self.inp = adsp.SizingInput(input_filename)
        self.cb.__dict__.update(self.inp.params)
        self.report = adsp.utils.AnalysisReport()



        self._analysis_func = {
            'dummy_func' : self._dummy_function,
            'calc_total_mass' : ram.calc_total_mass,
            'calc_stall_speed' : ram.calc_stall_speed,
            'calc_level_flight' : ram.calc_max_range_speed,
            'calc_rate_of_climb' : ram.calc_max_rate_of_climb,
            'calc_maximum_speed' : ram.calc_level_flight_max_speed,
            'calc_takeoff_dist' : ram.calc_takeoff_distance,
            'calc_landing_dist' : ram.calc_landing_distance,
            'calc_max_range': ram.calc_max_range,
            'calc_max_endurance': ram.calc_max_endurance,
            'calc_rate_of_climb_elec_power_req' : ram.calc_rate_of_climb_elec_power_req,
            'calc_level_flight_elec_power_req': ram.calc_level_flight_elec_power_req,
            'calc_takeoff_distance_elec_power_req': ram.calc_takeoff_distance_elec_power_req,
            }
        

    def _set_x(self, x):
        self.cb.set_values(self.inp.dvar_names, x)
        # TODO: need analysis that will pre-process data
        self.cb.weight_total_inp = self.cb.mass_total_inp * g
        self.cb.power_motor_total = self.cb.power_loading\
            *self.cb.weight_total_inp
        self.cb.power_motor_total_kw = self.cb.power_motor_total*1e-3
        self.cb.area_wing = self.cb.weight_total_inp\
            /self.cb.wing_loading
        self.cb.k = 1.0 / (self.cb.aspect_ratio_wing * np.pi\
            * self.cb.oswald_effy)


    def _dummy_function(self, cb, mis, par):
        self.cb.dummy_obj = self.cb.mass_total_inp*1e-2\
             + self.cb.power_motor_total*1e-4 + self.cb.area_wing

    def _obj_func(self, x):
        self._set_x(x)
        self._analysis_func[self.inp.objective.func_name](self.cb, self.inp.mission,
            self.inp.objective.add_params)
        return self.cb.__dict__[self.inp.objective.param_name]


    def _constr_func(self, x):
        self._set_x(x)
        g = np.zeros( len(self.inp.constraints)+1 )

        # this constraint enables IDF and should not be removed
        self._analysis_func['calc_total_mass'](self.cb, self.inp.mission, 
            self.inp.objective.add_params)
        # g[0] = 0.01 - (self.cb.mass_total_inp-self.cb.mass_total_out)**2.0
        g[0] = 1e-3 - (self.cb.mass_total_inp\
            - self.cb.mass_total_out)**2
        # user defined constraints
        for i, cnstr in enumerate(self.inp.constraints):
            self._analysis_func[cnstr.func_name](self.cb, 
                self.inp.mission, cnstr.add_params)
            gval = self.cb.__dict__[cnstr.param_name]

            if type(cnstr.target_value)==str:
                g_target = self.cb.__dict__[cnstr.target_value]
            else:
                g_target = cnstr.target_value

            if cnstr.target=='leq':
                g[i+1] = g_target - gval
            elif cnstr.target=='geq':
                g[i+1] = gval - g_target
            else:
                raise ValueError('unknown constraint target')
            # print('const violated: ', np.arange(len(g))[g<=0])
        return g
    
    def run_analysis(self, wingloading , powerloading, mass_opt):
        params ={}
        params['altitude']=3000
        self.cb.power_loading = powerloading
        self.cb.wing_loading  = wingloading
        
        self.cb.mass_total_in = mass_opt
        
        self._analysis_func['calc_maximum_speed'](self.cb, self.inp.mission, 
            params)
        self._analysis_func['calc_stall_speed'](self.cb, self.inp.mission, 
            params)
        self._analysis_func['calc_takeoff_dist'](self.cb, self.inp.mission, 
            params)
        self._analysis_func['calc_landing_dist'](self.cb, self.inp.mission, 
            params)        
        self._analysis_func['calc_rate_of_climb'](self.cb, self.inp.mission, 
            params)

        self._analysis_func['calc_max_range'](self.cb, self.inp.mission, 
            params)
        self._analysis_func['calc_max_endurance'](self.cb, self.inp.mission, 
            params)       
        self._analysis_func['calc_total_mass'](self.cb, self.inp.mission, 
            self.inp.objective.add_params)
    
         
    def run(self):
        bounds = np.transpose( np.vstack([self.inp.dvar_lb, 
                                          self.inp.dvar_ub]) )

        rslt = fmin_slsqp(self._obj_func, self.inp.dvar_init_val, 
            bounds=bounds, f_ieqcons=self._constr_func,
            full_output=True, iter=100, iprint=2)       
        self._set_x(rslt[0])     
        self.cb.span_wing = np.sqrt(self.cb.aspect_ratio_wing*self.cb.area_wing)
        self.report.add_optimize_results(self.cb)  
        self.report.add_configuration_data(self.cb) 
        self.report.add_mass_data(self.cb)
        self.run_analysis(self.cb.wing_loading, self.cb.power_loading, self.cb.mass_total_inp)
        self.report.add_performance_data(self.cb)

    
    def run_payload_range_sensitivity(self, spec_energy, payload_range, mass_opt):
        self.cb.spec_energy_batt_wh_per_kg = spec_energy
        initMass = mass_opt
        initPayload = max(payload_range)
        payloadRange = payload_range
        params = {}
        params['altitude']=3000
        mass_out = np.zeros(len(payloadRange))
        max_range = np.zeros(len(payloadRange))
        for i,pay in enumerate(payloadRange):
            self.cb.mass_payload = pay
            self.cb.mass_total_inp = initMass - (initPayload-pay)
            mass_out[i]=self.cb.mass_total_inp 
            self._analysis_func['calc_max_range'](self.cb, self.inp.mission, 
                params)
            max_range[i]=self.cb.range_max/1e3
        int_range = [0]
        int_payload = [initPayload]
        max_range = np.hstack(( max_range, int_range,))
        payloadRange = np.hstack(( payloadRange, int_payload,))
        return max_range, payloadRange
    
    def plot_range_payload(self, spec_energy_range, payload_range, mass_opt):  
        mass = round(mass_opt, 2)
        speed = 95
        plt.figure()
        fig, ax = plt.subplots()
        ax.set_title('Payload-range sensitivity'+'\n' \
            + f'design mass={mass}[kg]'+'\n'+f'crusie speed={speed} [m/s]')  
        for i,e in enumerate(spec_energy_range):
            max_range, payloadRange = self.run_payload_range_sensitivity(e, payload_range, mass_opt)            
            ax.plot(max_range, payloadRange, 'o-',label=f'{e} [Wh/kg]')
            plt.xlabel('maximum range [km]')
            plt.ylabel('payload [kg]')
            plt.grid()
            plt.legend(fontsize=12)
        return fig
    
    
    def get_power_loading_for_constr(self, wingloading):    
        self.cb.wing_loading = wingloading
        self.run_mass_convergence()
        params = {}
        params['altitude'] = 0.0
        params['speed_cruise'] = 120
        ram.calc_level_flight_elec_power_req(self.cb,self.inp.mission, params)
        pl_max = self.cb.power_loading_cruise
        params['speed_cruise'] = 95
        ram.calc_level_flight_elec_power_req(self.cb,self.inp.mission, params)
        pl_cruise = self.cb.power_loading_cruise
        params['distance_takeoff'] = 800
        ram.calc_takeoff_distance_elec_power_req(self.cb, self.inp.mission, params)
        pl_takeoff = self.cb.power_loading_takeoff
        params['rate_of_climb'] = 6.25
        ram.calc_rate_of_climb_elec_power_req(self.cb, self.inp.mission, params)
        pl_climb = self.cb.power_loading_climb
        return pl_max, pl_cruise, pl_takeoff, pl_climb,

    def run_mass_convergence(self):
        params={}
        params['altitude'] = 0
        def func(mass_in):
            self._analysis_func['calc_total_mass'](self.cb, self.inp.mission,params)
            mass_out = self.cb.mass_total_out
            
            return (mass_in-mass_out)**2
        mass_in = fsolve(func, 3000, xtol=1e-3)[0]
        self.cb.mass_total_out = mass_in

                  
    def run_carpet_plot(self,wingloading_min=800, wingloading_max=2000,
                               powerloading_min=6, powerloading_max=20):
        n = 5
        powerloading = np.linspace(powerloading_min,powerloading_max, n)
        wingloading  = np.linspace(wingloading_min, wingloading_max, n)
        mass  = np.zeros((n,n))
        params={}
        params['altitude'] = 3000
        PL_cruise = np.zeros(n)
        PL_max_speed = np.zeros(n)
        PL_takeoff  = np.zeros(n)
        PL_climb    = np.zeros(n)
        ws_stall    = np.zeros(n)
        for i,ws in enumerate(wingloading):
            for j,pl in enumerate(powerloading):
                self.cb.wing_loading = ws
                self.cb.power_loading = pl              
                self.run_mass_convergence()                
                mass[i,j] = self.cb.mass_total_out
            pl_max, pl_cruise, pl_takeoff, pl_climb  = self.get_power_loading_for_constr(ws)
            params['speed_stall'] = self.cb.speed_stall
            ram.calc_stall_speed_wing_loading(self.cb, self.inp.mission, params)
            ws_stall[i] = self.cb.wing_loading_speed_stall
            PL_max_speed[i]= pl_max
            PL_cruise[i] = pl_cruise
            PL_takeoff[i] = pl_takeoff
            PL_climb[i]   = pl_climb
        
        fig = go.Figure()
        
        fig.add_trace(go.Carpet(
            a = wingloading,
            b = powerloading,
            y = mass,
            aaxis = dict(
                tickprefix = 'W/S = ',
                ticksuffix = '[N/m^2]',
                smoothing = 1,
                minorgridcount = 3,
                gridcolor = 'black',
                color = 'black',
                ),
            baxis = dict(
                tickprefix = 'P/W = ',
                ticksuffix = '[W/N]',
                smoothing =1,
                minorgridcount = 3,
                gridcolor = 'black',
                color = 'black',
                ),
        ))

        fig.add_trace(go.Scattercarpet(
            name = 'cruise-speed',
            a = wingloading,
            b = PL_cruise,
            line = dict(
              shape = 'spline',
              smoothing = 1,
              color = 'red'
            )
            ))
        fig.add_trace(go.Scattercarpet(
            name = 'maximum-speed',
            a = wingloading,
            b = PL_max_speed,
            line = dict(
              shape = 'spline',
              smoothing = 1,
              color = 'blue'
            )
            ))
        fig.add_trace(go.Scattercarpet(
            name = 'takeoff-distance',
            a = wingloading,
            b = PL_takeoff,
            line = dict(
              shape = 'spline',
              smoothing = 1,
              color = 'yellow'
            )
            ))
        fig.add_trace(go.Scattercarpet(
            name = 'maximum-climb-rate',
            a = wingloading,
            b = PL_climb,
            line = dict(
              shape = 'spline',
              smoothing = 1,
              color = 'green'
            )
            ))
        
        fig.add_trace(go.Scattercarpet(
            name = 'stall speed',
            a = ws_stall,
            b = powerloading,
            line = dict(
              shape = 'spline',
              smoothing = 1,
              color = 'black'
            )
            ))
        
        fig.update_layout(
        margin=dict(l=20, r=20, t=20, b=20,),
        paper_bgcolor="white",)
        fig.layout =  dict(
            yaxis = dict(title = 'MTOW [kg]'),)
        return fig
    
    def run_sizing_matrix_plot(self, wingloading_min=1000, wingloading_max=2000,
                               powerloading_min=10, powerloading_max=40, 
                               wingloading_opt=1335, powerloading_opt=18):
        n = 10
        powerloading = np.linspace(powerloading_min,powerloading_max,n)
        wingloading  = np.linspace(wingloading_min, wingloading_max, n)
        mass  = np.zeros((n,n))
        params={}
        params['altitude'] = 0
        PL_cruise = np.zeros(n)
        PL_max_speed = np.zeros(n)
        PL_takeoff  = np.zeros(n)
        PL_climb    = np.zeros(n)

        for i,ws in enumerate(wingloading):
            for j,pl in enumerate(powerloading):
                self.cb.wing_loading = ws
                self.cb.power_loading = pl              
                self.run_mass_convergence()                
                mass[j,i] = self.cb.mass_total_out
            pl_max, pl_cruise, pl_takeoff, pl_climb, = self.get_power_loading_for_constr(ws)
            PL_max_speed[i]= pl_max
            PL_cruise[i] = pl_cruise
            PL_takeoff[i] = pl_takeoff
            PL_climb[i]   = pl_climb
        params['speed_stall'] = 36
        ram.calc_stall_speed_wing_loading(self.cb, self.inp.mission, params)
        ws_stall = self.cb.wing_loading_speed_stall
        plt.figure()
        fig, ax = plt.subplots()
        ax.set_title('sizing matrix plot')  
        ax.contourf(wingloading,powerloading,mass, 15, cmap='RdYlBu_r',alpha=00.5)
        cs2 = ax.contour(wingloading,powerloading,mass, 15, colors='black')      
        ax.clabel( cs2, inline =1, fontsize=10)
        ax.plot(wingloading, PL_max_speed, 'b-', label = 'max-speed', linewidth=2,
                path_effects=[patheffects.withTickedStroke(spacing=7, angle=135)])
        ax.plot(wingloading, PL_climb,'g-', label='climb',linewidth=2,
                path_effects=[patheffects.withTickedStroke(spacing=7, angle=-135)])
        ax.plot(wingloading, PL_cruise,'r-', label='cruise', linewidth=2,
                path_effects=[patheffects.withTickedStroke(spacing=7, angle=-135)])       
        ax.plot(wingloading, PL_takeoff, 'y-', label = 'takeoff', linewidth=2,
                path_effects=[patheffects.withTickedStroke(spacing=7, angle=-135)])            
        ax.axvline(ws_stall, color='k', label='stall-speed',
                   path_effects=[patheffects.withTickedStroke(spacing=7, angle=-135)])
        ax.scatter(wingloading_opt, powerloading_opt, marker='o', s=100, c='k')
        
        ax.set_xlabel("wing loading [N/m^2]")
        ax.set_ylabel("power loading [W/N]")
        plt.legend()
        return fig
        
            
    def run_stall_speed_max_speed_carpet_plot(self, powerloading_opt, mass_opt):
        n = 5
        wingloading = np.linspace(1000, 2000, n)
        CLmax       = np.linspace(1.8,2.7, n)
        stall_speed = np.zeros((n,n))
        maximum_speed = np.zeros((n,n))
        wingArea      = np.zeros((n,n))
        params = {}
        for i,ws in enumerate(wingloading):
            for j, clmax in enumerate(CLmax):
                self.cb.wing_loading = ws
                self.cb.power_loading = powerloading_opt
                self.cb.CL_max       = clmax
                params['altitude']   = 0
                ram.calc_stall_speed(self.cb, self.inp.mission, params)
                stall_speed[i,j] = self.cb.speed_stall
                ram.calc_level_flight_max_speed(self.cb, self.inp.mission, params)
                maximum_speed[i,j] = self.cb.speed_max
                wingArea[i,j] = mass_opt*g*1/self.cb.wing_loading
                
        plt.figure()
        fig, ax = plt.subplots()
        mass = round(mass_opt, 2)
        ax.set_title('stall speed - max speed carpet plot' + '\n' \
                     +f'MTOW={mass}[kg], CD0={self.cb.CD_0},'+'\n' \
                     +f'powerloading={round(powerloading_opt,2)}[Watt/N]')
        tol = 0.2
        y_pos = stall_speed.transpose()
        x_pos = max(maximum_speed[4])
        for i in range(n):
            s = round(wingArea[i][0],2)
            ax.plot(maximum_speed[i], stall_speed[i], '-', label= f'S = {s} [m^2]')
            ax.text(x_pos+tol, max(y_pos[i]), f'CLmax={CLmax[i]}')
        ax.plot(maximum_speed, stall_speed,'k-')
        plt.xlabel('maximum speed [m/s]')
        plt.ylabel('stall speed [m/s]')
        plt.grid()
        plt.legend()
        fig.tight_layout()
        return fig
    
    def get_mass_break_down(self, mass_opt):
        mass = round(mass_opt,2)
        y = [self.cb.mass_payload, self.cb.mass_struct,  self.cb.mass_battery,
              self.cb.mass_propeller_total, self.cb.mass_motor_total, 
              self.cb.mass_controller_total, self.cb.mass_subsys, self.cb.mass_avionics]

        label = ["payload","structural","battery","propellers","motors","Inverters",
                 "subsystem","avionics"]
        plt.figure()
        fig, ax = plt.subplots()
        ax.set_title("Mass break down"+'\n'+
                     f'design mass={mass} [kg]')
        plt.pie(y,labels=label, autopct='%1.1f%%')
        return fig
    
    def print_data(self):
        
        print ('\n',"-------Configuration parameters------")
        print ("Wing Area      :", self.cb.area_wing)
        print ("Wing Span      :", np.sqrt(self.cb.aspect_ratio_wing*self.cb.area_wing))
        print ("Aspect Ratio   :", self.cb.aspect_ratio_wing)
        print ("Prop Diameter  :", self.cb.diam_propeller)
        print ("Number of Prop :", self.cb.num_of_propellers_ctol, '\n')
        
        print ("-------ePropulsion System Mass------")
        print ("propeller-mass   :", self.cb.mass_propeller_total)
        print ("motor_mass       :", self.cb.mass_motor_total)
        print ("controller_mass  :", self.cb.mass_controller_total)
        print ("Propulsion Total :", self.cb.mass_propeller_total\
            + self.cb.mass_motor_total+self.cb.mass_controller_total, '\n')
        
        print ("----- Energy System Mass ------ ")
        print ("battery mass     :", self.cb.mass_battery, '\n')
        print ("----- Structural, Subsys and Mis Mass -----")
        print ("Structural mass  :", self.cb.mass_struct)
        print ("Subsystem mass   :", self.cb.mass_subsys)
        print ("Avionics         :", self.cb.mass_avionics)
        print ("Structural Total :", self.cb.mass_struct+self.cb.mass_subsys\
            + self.cb.mass_avionics, '\n')
        print ("------ Payload Mass ------")
        print ("Payload          :", self.cb.mass_payload, '\n')
        print ("----- MTOW out, in -----")
        print ("MTOW in          :", self.cb.mass_total_inp)
        print ("MTOW out         :", self.cb.mass_total_out, '\n')
        
        # print ("----- Mass friction -----")
        print ("OEM frac    :", self.cb.mass_frac_OEM)
        print ("payload frac:", self.cb.mass_frac_payload)
        print ("energy frac :", self.cb.mass_frac_energy, '\n')
        
        print ("----- Power and wing loading -----")
        print ("power loading   :", self.cb.power_loading)
        print ("wing loading    :", self.cb.wing_loading)
        print ("power           :", self.cb.power_motor_req)
        print ("wing loading    :", self.cb.wing_loading)
        print ("wing area       :", self.cb.area_wing)
        print ("wing span       :", np.sqrt(self.cb.area_wing*self.cb.aspect_ratio_wing),'\n')
        print ("energy density:", self.cb.spec_energy_batt_wh_per_kg, '\n')
        print ("----- Total energy-----------")
        print ("total energy   :", self.cb.energy_total/3600,'\n')
        
        print ("----- Constraints-------")
        print ("stall speed      :", self.cb.speed_stall)
        print ("maximum speed    :", self.cb.speed_max)
        print ("ROC_max          :", self.cb.rate_of_climb)
        print ("takeoff distance :", self.cb.distance_takeoff, '\n') 

        print ("----- Max Range, Endurance -------")
        print ("Maximum Range (km)     :", self.cb.range_max_km)
        print ("Max range speed        :", self.cb.speed_range_best)
        print ("Maximum endurance (hr) :", self.cb.endurance_max_hr)
        print ("Max endurance speed    :", self.cb.speed_endurance_best)    

    def save_report(self, path):
        self.report.save_files()
                



                

            

                
            
         

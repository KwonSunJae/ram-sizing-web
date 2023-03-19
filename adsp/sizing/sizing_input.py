import csv
import numpy as np

import adsp.paths
from adsp.utils.misc_tools import convert_cell_value
from adsp.sizing.mission import MissionProfile


__all__ = ['SizingInput']


class FunctionSettings(object):
    def __init__(self):
        self.func_name = '' # function to run
        self.param_name = '' # objective or constraint parameter
        self.target_value = 0 # for constraints
        self.target = ''  # min/max for objective, leq/geq for constraint
        self.add_params = {}  # dict of optional parameters

        self._mult_factor = 1
    
    def _process(self):
        if self.target=='min':
            self._mult_factor = 1
        elif self.target=='max':
            self._mult_factor = -1
    
    def __repr__(self):
        out = f'{self.func_name} {self.target}\n'
        for key, val in self.add_params.items():
            out += f'{key} : {val}\n'
        return out


class SizingInput:
    def __init__(self, input_filename):
        self.params = {}
        self.dvar_names = list()
        self.dvar_init_val = list()
        self.dvar_lb = list()
        self.dvar_ub = list()
        self.objective   = FunctionSettings()
        self.constraints = list()
        self.mission = MissionProfile()
        self.tradeoff = list()

        path = adsp.paths.db.get_input_file_path(input_filename)

        with open(path, mode='r', encoding='utf-8-sig') as csv_file:
            reader = csv.reader(csv_file, delimiter=',')
            row = next(reader)
            if row[0]!='SIZING INPUT':
                raise IOError('Input file must start with SIZING INPUT \
                    keyword!')

            row = next(reader)
            while row[0]!='DESIGN VARIABLE':
                self.params[row[0]] = convert_cell_value(row[1])
                row = next(reader)

            self.mission.read_csv(self.params['mission_profile'])

            row = next(reader)
            while row[0]!='OBJECTIVE':
                self.dvar_names.append(row[0])
                self.dvar_init_val.append(convert_cell_value(row[1]))
                self.dvar_lb.append(convert_cell_value(row[2]))
                self.dvar_ub.append(convert_cell_value(row[3]))
                row = next(reader)
            
            self.dvar_lb = np.array(self.dvar_lb)
            self.dvar_init_val = np.array(self.dvar_init_val)
            self.dvar_ub = np.array([self.dvar_ub])

            assert (self.dvar_ub >= self.dvar_init_val).all()
            assert (self.dvar_init_val >= self.dvar_lb).all()

            # read objective function data
            row = next(reader)
            self.objective.func_name = row[0]
            row = next(reader)
            self.objective.param_name = row[0]
            self.objective.target    = row[1]
            row = next(reader)
            while row[0]!='CONSTRAINT':
                self.objective.add_params[row[0]] =\
                    convert_cell_value(row[1])
                row = next(reader)
            self.objective._process()

            # read constraints data
            i = 0
            self.constraints.append(FunctionSettings())
            for row in reader:
                if i==0:
                    self.constraints[-1].func_name = row[0]
                    i += 1
                elif i==1:
                    self.constraints[-1].param_name = row[0]
                    self.constraints[-1].target = row[1]
                    self.constraints[-1].target_value = \
                        convert_cell_value(row[2])
                    i += 1
                elif row[0]=='CONSTRAINT':
                    self.constraints.append(FunctionSettings())
                    i = 0                             
                else:
                    self.constraints[-1].add_params[row[0]] = \
                        convert_cell_value(row[1])
                    i += 1
         
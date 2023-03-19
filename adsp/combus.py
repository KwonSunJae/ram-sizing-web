# -*- coding: utf-8 -*-
"""
Created on Mon May 23 14:22:18 2022

@author: maxim
"""
from numpy import float64
import adsp.paths
import csv



class DataStruct(object):
    _attr_display_len  = 25
    _value_display_len = 12
    def add_variable(self, var_name, var_type):
        if var_type=='float':
            val = 0
        elif var_type=='str':
            val = ''
        elif var_type=='bool':
            val = True
        else:
            raise IOError(f'Unknown variable type {var_type} in combus!')
        self.__dict__[var_name] = val
    
    def _check_var_type(self):
        for attr, value in self.__dict__.items():
            print(attr, type(value))

    def __repr__(self):
        out = ''
        for attr, value in self.__dict__.items():
            val_type = type(value)
            if val_type==str:
                out += '{:<25} : {:<12}\n'.format(attr, value)
            elif val_type==DataStruct:
                out += f'\n# {attr}\n'
                out += self.__dict__[attr].__repr__()
            else:
                out += '{:<25} = {:<12}\n'.format(attr, value)
        return out


class CommunicationBus2(DataStruct):
    def __init__(self, combus_name):
        path = adsp.paths.db.get_combus_input_csv_path(combus_name)
        sec_name = 'none'
        with open(path, mode ='r', encoding='utf-8-sig') as csv_file:
            reader = csv.reader(csv_file, delimiter=',')
            for row in reader:
                if row[0]=='SECTION':
                    sec_name = row[1]
                    self.__dict__[sec_name] = DataStruct()
                else:
                    if sec_name=='none':
                        self.add_variable(row[0], row[1])
                    else:
                        self.__dict__[sec_name].add_variable(row[0], 
                                                             row[1])
    
    def set_values(self, param_name_list, values):
        assert len(param_name_list)==len(values)
        for p, v in zip(param_name_list, values):
            self.__dict__[p] = v
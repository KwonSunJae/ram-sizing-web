# -*- coding: utf-8 -*-
"""
Created on Tue Jun 14 10:44:26 2022

@author: maxim
"""
from numpy import ndarray


class DataStructure():
    def __repr__(self):
        out = ''
        for attr, value in self.__dict__.items():
            if type(value) is float:
                out += '{:<10}: {:<+10.5f}\n'.format(attr,value)
            if type(value) is ndarray:
                out += '{:<10}: '.format(attr)
                for val in value:
                    out += '{:<+10.5f}\t'.format(val)
                out += '\n'
            if type(value) is str:
                out += '{:<10}: {:<10}\n'.format(attr, value)
        return out
    
def get_header_str(header, level=1):
    return '\n' + '#'*level + ' ' + header + '\n\n'
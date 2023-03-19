# -*- coding: utf-8 -*-
"""
Created on Thu Jan 09 11:50:25 2014

@author: Maxim
"""

from datetime import datetime
import numpy as np
from scipy.interpolate import Rbf


def convert_cell_value(val):
    # single value only. no arrays
    val = str(val)
    val_clean = val.replace('.','').replace('-','')
    if val_clean.isdigit():
        if val_clean==val:
            return int(val)
        else:
            return float(val)
    else:
        return val

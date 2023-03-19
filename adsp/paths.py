# -*- coding: utf-8 -*-
"""
Created on Tue Jan 07 14:37:02 2014

Module for manipulation with standard files and paths used in software

@author: Maxim
"""

import os
from random import randrange
import platform
from warnings import warn
from datetime import datetime
import sys

_adspSrcDir = os.path.dirname(__file__)


class _Databases:
    """
    store and manipulate database paths
    """
    def __init__(self):
        self.dbPath = os.path.abspath(os.path.join( _adspSrcDir, \
            '../data'))
        self.inpDir = os.path.abspath(os.path.join(_adspSrcDir, \
            '../input'))
        self.outPath = os.path.abspath(os.path.join(_adspSrcDir, '../output'))
        self.combus = os.path.abspath(self.dbPath + '/combus/')
    
    def get_from_db_path(self, name):
        return os.path.abspath(f'{self.dbPath}/{name}.csv')

    def get_constants_csv_path(self, name):
        return os.path.abspath(self.constants + '/%s.csv'%name)

    def get_combus_input_csv_path(self, name):
        return os.path.abspath(self.combus + '/%s.csv'%name)

    def get_tmp_report_dir(self):
        now = sys.argv[1]
        return os.path.abspath(self.outPath + '/' + now), now
    
    def get_input_file_path(self, name):
        return os.path.abspath(self.inpDir + '/%s.csv'%name)
    
    def get_sizing_mission_path(self, name):
        return os.path.abspath(self.dbPath + '/sizing-mission/'\
            + '/%s.csv'%name)
            
db       = _Databases()

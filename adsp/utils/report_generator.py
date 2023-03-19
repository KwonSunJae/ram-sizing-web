# -*- coding: utf-8 -*-
"""
Created on Wed Jun 15 11:37:23 2022
@author: maxim

Set of tools

"""
from adsp import paths
import os
from shutil import copyfile
from datetime import datetime
import numpy as np



class MarkdownDocument():
    def __init__(self, title="ADSP Report"):
        self.doc     = ''
        self.title = title
        self.figIdx  = 0
        self.figures      = list()
        self.figCaptions  = list()
        self.figFileNames = list()
        self.figFormat = 'png'
        self.reportFileName = 'report'
        self.docMargin = 2 # [cm]
        self._write_doc_header()
    
    def _write_doc_header(self):
        self.doc += '---\n'
        self.doc += 'title: \"%s\"\n'%self.title
        self.doc += 'geometry: margin=%.fcm\n'%self.docMargin
        self.doc += 'date: ' + datetime.now().strftime("%Y-%m-%d")
        self.doc += '\n...\n\n'

    
    def set_dir(self, reportFilesDirectory):
        pass
    
    def set_filename(self, reportFileName):
        pass
    
    def cleanup(self):
        self.doc = ''
    
    def add_header(self, header, level=1):
        self.doc += '\n%s %s\n\n'%(level*'#', header)
    
    def add_paragraph(self, text):
        self.doc += '%s\n\n'%text
        
    def add_line(self, text):
        self.doc += '%s\n'%text
    
    def add_table(self, data, headerLabels=None):
        """
        data : list
            this variable should contain a list of all values to be saved 
            into the table
        """
        numOfParam = len(data)
        dataLen    = len(data[0])
        
        if not all(len(arr)==dataLen for arr in data):
            raise ValueError('all arrays must have same length!')
        
        if hasattr(headerLabels,'__iter__'):
            if not len(headerLabels)==numOfParam:
                raise ValueError('Length of header must be the same as number\
                                   of variables in the data list')
        else:
            headerLabels = np.empty(numOfParam, str) + ' '
        
        # write header
        self.doc += '\n'
        for label in headerLabels:
            self.doc += '|%s '%label
        self.doc += '|\n'
        for label in headerLabels:
            self.doc += '|---'
        self.doc += '|\n'
        
         # write data
        for i in range(len(data[0])):
            for j in range(len(data)):
                if type(data[j][i]) is np.str_:
                    self.doc += '%s |'%data[j][i]
                elif type(data[j][i]) is np.float_:
                    self.doc += '%.4f |'%data[j][i]
                else:
                    self.doc += 'None |'

            self.doc += '\n'
  
    def add_figure(self, fig, caption=''):
        """
        add figure in matplotlib format
        """
        self.figIdx += 1
        self.figures.append(fig)
        self.figCaptions.append(caption)
        fileName = 'Figure_%d.%s'%(self.figIdx, self.figFormat)
        self.figFileNames.append(fileName)
        self.doc += '\n![%s](%s)\n\n'%(caption, fileName)
    
    def save_files(self):
        path, dirname = paths.db.get_tmp_report_dir()
        os.mkdir(path)
        mdFile = self.reportFileName +   '.md'
        pdfFile = mdFile[:-2] + 'pdf'
        mdPath = os.path.abspath(path + '\\' + mdFile)
        
        fid = open(mdPath, 'w+')
        fid.write(self.doc)
        fid.close()
        
        # save all figures
        for i in range(self.figIdx):
            figPath = os.path.abspath(path + '\\' + self.figFileNames[i])
            self.figures[i].savefig(figPath)

        # generate pdf
        os.chdir('%s'%path)
        cmd = 'pandoc -s -o \"%s\" \"%s\"'%(pdfFile, mdFile)
        os.system(cmd)
        
        # copy pdf to root folder
        srcFile = os.path.abspath(path + '\\' + pdfFile)
        destFile = os.path.abspath(paths.db.outPath + '\\' + dirname + '.pdf')
        copyfile(srcFile, destFile)


    def __repr__(self):
        return self.doc
    



class AnalysisReport(MarkdownDocument):
    """
    class to store data from each analysis, generate report files and 
    convert them to pdf/doc formats
    """
    def __init__(self, savePath=None):
        super().__init__()
        self.maxLenParName  = 3
        self.maxLenUnit     = 6
        self.maxLenParValue = 10
        self._init_line_format()
    
    def _init_line_format(self):
        self.fmtParamValueUnit = '{0:<%d} = {1:<%d.4f}{2:<%d}'%(self.maxLenParName, 
                                                              self.maxLenParValue, 
                                                              self.maxLenUnit)

    
    def add_param_with_value(self, name, value, unit=''):
        self.add_line( self.fmtParamValueUnit.format(name, value, unit) )
    
    def add_optimize_results(self, cb):
        self.add_header("Optimum varialbes which minimize MTOW")
        self.add_line("Optimize varialbes")
        labels =["Symbols", "Parameters", "Value", "Unit"]
        parameters = np.array(['Total Takeoff Mass', "Power Loading", "Wing loading"])
        symbols = np.array(["MTOW","P/W", "W/S"])
        value   = np.array([cb.mass_total_inp, cb.power_loading, cb.wing_loading])
        units   = np.array(["kg", "Watt/N", "N,m^2"])
        tableValues = [symbols, parameters, value, units]
        self.add_table(tableValues, labels)

    def add_configuration_data(self, cb):
        self.add_line("Optimize configuration parameters")
        labels =["Symbols", "Parameters", "Value", "Unit"]
        parameters = np.array(['Wing area', "Wing span", "Aspect ratio","Propeller Diameter","Num of Propeller"])
        symbols = np.array(["S","b", "AR","$D_{propeller}$","$Num_{propeller}$"])
        value   = np.array([cb.area_wing, cb.span_wing, cb.aspect_ratio_wing,
                     cb.diam_propeller, cb.num_of_propellers_ctol])
        units   = np.array(["m", "m", "-","m",''])
        tableValues = [symbols, parameters, value, units]
        self.add_table(tableValues, labels)

    def add_mass_data(self, cb):
        self.add_line("Optimize mass data")
        labels =["Symbols", "Parameters", "Value", "Unit"]
        parameters = np.array(['propeller mass', "motor mass", "controller mass","total propulsion mass",
                        "Energy mass","payload mass","structural mass","subsystem mass","avionics mass"])
        symbols = np.array(["$mass_{propeller}$","$mass_{motor}$", "$mass_{controller}$","$mass_{prop_{system}}$",
                        "$mass_{energy}$","$mass_{payload}$","$mass_{struct}$","$mass_{subsys}$","$mass_{avionics}$"])
        value   = np.array([cb.mass_propeller_total, cb.mass_motor_total, cb.mass_controller_total,
                     cb.mass_propulsion_sys,cb.mass_energy,cb.mass_payload,cb.mass_struct, cb.mass_subsys, cb.mass_avionics])
        units   = np.array(["kg", "kg", "kg","kg","kg","kg","kg","kg","kg"])
        tableValues = [symbols, parameters, value, units]
        self.add_table(tableValues, labels)

    def add_performance_data(self, cb):
        self.add_line("Optimize performance data")
        labels =["Symbols", "Parameters", "Value", "Unit"]
        parameters = np.array(['stall speed','maximum speed','maximum endurance speed',
                            'maximum range speed','maximum rate of climb', 'takeoff distance',
                            'maximum range', 'maximum endurance'])
        symbols = np.array(['$V_{stall}$','$V_{max}$','$V_{E_{max}}$',
                            '$V_{R_{max}}$','$ROC_{max}$','$S_{to}$',
                            '$R_{max}$','$E_{max}$'])
        value  = np.array([cb.speed_stall,cb.speed_max, cb.speed_endurance_best,cb.speed_range_best,
                            cb.rate_of_climb,cb.distance_takeoff,cb.range_max_km, cb.endurance_max_hr])
        units   = np.array(['m/s','m/s','m/s','m/s','m/s','m','km','hr'])
        tableValues = [symbols, parameters, value, units]
        self.add_table(tableValues, labels)

    def add_constraint_diagram(self, const_figure):
        self.add_header("Constraint Diagram")
        self.add_figure(const_figure, caption="Constraint Diagram")

    def add_mass_breakdown(self, mass_brakdown):
        self.add_header("Mass Breakdown of Optimized Configuraton")
        self.add_figure(mass_brakdown, caption="Mass Brekdown")

    def add_payload_range_tradeoff(self, payload_range_tradeoff):
        self.add_header("Payload Range Tradeoff")
        self.add_figure(payload_range_tradeoff, caption="Payload Range Diagram")

    def add_stall_max_speed_tradeoff(self, stall_max_speed_tradeoff):
        self.add_header("Stall Speed and Maximum Speed Tradeoff")
        self.add_figure(stall_max_speed_tradeoff, caption="Stall and Maximum Speed Tradeoff")
        





        


    
    


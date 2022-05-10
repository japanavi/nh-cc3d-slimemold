"""
Created: June 2011
Author: Niklas Semmler
Updated by: Joshua Apanavicius
Last Updated: May 2022
"""

import math
import random
from pathlib import Path
from typing import List

from cc3d.core.PySteppables import *


class projectSteppable(SteppableBasePy):
                
    def __init__(self,frequency=1):
        SteppableBasePy.__init__(self, frequency)
        
    def start(self):
        """
        any code in the start function runs before MCS=0
        """

    def step(self,mcs):
        """
        type here the code that will run every frequency MCS
        :param mcs: current Monte Carlo step
        """

    def finish(self):
        """
        Finish Function is called after the last MCS
        """

    def on_stop(self):
        # this gets called each time user stops simulation
        return


class SecretionSteppable(SteppableBasePy):
    """ defines additional waves released by random food sources every periode"""
    
    def _ls_pif(self, path: str) -> List[str]:
        p = Path(path)
        return [child.name for child in p.iterdir() if child.suffix == ".pif"]

    def _get_cell_type(self, cell_type: str):
        type_map = {
            "Wall": self.WALL,
            "FoodSource": self.FOODSOURCE,
            "SlimeMold": self.SLIMEMOLD
        }

        return type_map[cell_type]

    def _gen_from_pif(self, path: str) -> None:
        c_id = 0
        c_type = 1
        x_start = 2
        x_finish = 3
        y_start = 4
        y_finish = 5

        ids = {}
        with open(Path(path), "r") as file:
            for line in file.readlines():
                if line.startswith("#"):
                    continue
                    
                c_line = line.split()
                
                if int(c_line[c_id]):
                    if c_line[c_id] in ids.keys():
                        cell = self.fetch_cell_by_id(ids[c_line[c_id]])
                        self.cell_field[int(c_line[x_start]):int(c_line[x_finish]), int(c_line[y_start]):int(c_line[y_finish]), 0] = cell
                        
                    else:
                        cell = self.new_cell(self._get_cell_type(c_line[c_type]))
                        self.cell_field[int(c_line[x_start]):int(c_line[x_finish]), int(c_line[y_start]):int(c_line[y_finish]), 0] = cell
                        ids[c_line[c_id]] = cell.id


    def __init__(self, frequency=50):
        SteppableBasePy.__init__(self, frequency)
        self.runBeforeMCS = 1
        self.counter = 1
        self.hbound = 5
        
    def start(self):
        """
        any code in the start function runs before MCS=0
        """
        self.PATH = Path(__file__).parent.parent.absolute() / "maps"
        self.curr_sim = ""

    def add_steering_panel(self):
        
        self.add_steering_param(
            name='simulation_type', 
            val="Select Simulation to Run", 
            enum=self._ls_pif(self.PATH),
            widget_name='combobox'
            )
        
        self.add_steering_param(
            name='SlimeMoldConnectivity',
            val=50_000,
            min_val=0,
            max_val=100_000,
            decimal_precision=2,
            widget_name='slider'
        )

        self.add_steering_param(
            name='ATTR_Lambda',
            val=300,
            min_val=0,
            max_val=1_000,
            decimal_precision=2,
            widget_name='slider'
        )
        self.add_steering_param(
            name='ATTR_SaturationLinearCoef',
            val=0.0007,
            widget_name='lineedit'
        )

        self.add_steering_param(
            name='REP_Lambda',
            val=-200,
            min_val=-500,
            max_val=500,
            decimal_precision=2,
            widget_name='slider'
        )
        
        self.add_steering_param(
            name='REP_SaturationLinearCoef',
            val=0.005,
            widget_name='lineedit'
        )
       

    def process_steering_panel_data(self):
        simulation_type = self.get_steering_param('simulation_type')
        
        # Fetching steering panel values
        new_conn = self.get_steering_param('SlimeMoldConnectivity')
        
        new_attr = self.get_steering_param('ATTR_Lambda')
        new_attr_coef = self.get_steering_param('ATTR_SaturationLinearCoef')
        
        new_rep = self.get_steering_param('REP_Lambda')
        new_rep_coef = self.get_steering_param('REP_SaturationLinearCoef')
        
        
        # Fetching and setting XML
        self.get_xml_element("sm_connect").cdata = new_conn

        self.get_xml_element("attr_ele").Lambda = new_attr
        self.get_xml_element("attr_ele").SaturationLinearCoef = new_attr_coef
        
        self.get_xml_element("rep_ele").Lambda = new_rep
        self.get_xml_element("rep_ele").SaturationLinearCoef = new_rep_coef
        

    def step(self, mcs):
        
        while self.get_steering_param('simulation_type') == "Select Simulation to Run":
            pass
        # make sure simulation type is allocated
        simulation_type = self.get_steering_param('simulation_type')
        #At the start of the simulation read the sliders for initialization
        # if mcs == 0:
        if self.curr_sim != simulation_type:
            self.curr_sim = simulation_type
            # If we know x.pif is (x, y) pixels
            if self.get_steering_param('simulation_type') == "nl.pif":
                self.resize_and_shift_lattice(new_size=(200, 300, 1), shift_vec=(0, 0, 0))
                
            # ATTR_field = self.field.ATTR
            # REP_field = self.field.REP
            
            # for x, y, z in self.every_pixel():
                # ATTR_field[x, y, z] = 0.0
                # REP_field[x, y, z] = 0.0
                
                
            # self.cell_field[0:50, 0:50, 0] = self.fetch_cell_by_id(0)
            # for cell in self.cell_list:
                # if cell:
                    # self.delete_cell(cell)      
                
            self._gen_from_pif(self.PATH / self.get_steering_param('simulation_type'))
            self.build_wall(self.WALL)
            
            for cell in self.cell_list:
                if cell.type == 1:
                    self.shared_steppable_vars['foodsources'] += [cell]
                elif cell.type == 2:
                    self.slimey = cell  # single cell slime mold
                    self.shared_steppable_vars['slimey'] = self.slimey

            # first definition of the slime mold's volume constraint
            self.shared_steppable_vars['slimey'].targetVolume = self.shared_steppable_vars['baseVolume'] * self.shared_steppable_vars['basePercVolume']
            self.shared_steppable_vars['slimey'].lambdaVolume = 6
            

        self.process_steering_panel_data()
        attrSecretor = self.get_field_secretor("ATTR")

        for cell in self.cell_list:
            cell.onset = 0
            if cell.type == 1 and self.counter == random.randint(1, self.hbound):
                res = attrSecretor.secreteInsideCellTotalCount(cell, 200)
                
        self.counter += 1
        if self.counter > self.hbound:
            self.counter = 1


class VolumeAnnealingSteppable(SteppableBasePy):
    """ volume is changed every 100mcs """

    def __init__(self, frequency=25):
        """ define constants dependent on _simulator"""
        SteppableBasePy.__init__(self, frequency)
        

    def start(self):
        """ defines number of parameters for volume control"""
        # self.nSteps = int(self.get_xml_element("N_steps").cdata)
        
        # Foodsources
        self.foodsources = []
        self.shared_steppable_vars['foodsources'] = self.foodsources

        # Cumulative volume added by foodsources
        self.FSVolume = 0

        # Volume added per connected foodsource
        # self.addFSVolume = 175
        self.addFSVolume = 200

        # base volume of the slime mold
        self.baseVolume = 9 * self.addFSVolume
        self.shared_steppable_vars['baseVolume'] = self.baseVolume

        # base percentage of the volume
        self.basePercVolume = 0.2
        self.shared_steppable_vars['basePercVolume'] = self.basePercVolume

        # 0.2 percentage of the volume oscillating
        # self.oscillPercVolume = 0
        self.oscillPercVolume = 0.2
        
        self.nSteps = int(self.get_xml_element("N_steps").cdata)

        # little more than the rest volume used for growth and shrinking
        self.devPercVolume = 1.2 - (self.basePercVolume + 2 * self.oscillPercVolume)

        self.growthPeriode = (2 * self.nSteps) / (3 * self.frequency)
        self.shrinkPeriode = (self.nSteps / self.frequency) - self.growthPeriode

        # growth per time unit
        self.growthPercVolume = (self.devPercVolume / self.growthPeriode)

        # growth per time unit
        self.shrinkPercVolume = (-(self.devPercVolume / 2) / self.shrinkPeriode)

        self.chanPercVolume = self.growthPercVolume

        # number of mcs between 0 and 2 pi of a sine cycle.
        self.oscillFreq = 1000.0

    def step(self, mcs):
        # if growth periode is over shrink!
        if mcs / self.frequency > self.growthPeriode:
            self.chanPercVolume = self.shrinkPercVolume

        self.volumeDev()  # affects self.basePercVolume
        self.relToFS()    # affects self.FSVolume
        oscillPerc = 0    #self.volumeOscill(mcs)
        # oscillPerc = self.volumeOscill(mcs)

        # integrate oscillation, growth and base percentage
        perc = oscillPerc + self.basePercVolume
        # integratie base and additional volumes
        vol = self.baseVolume + self.FSVolume

        # calculate new combined target volume
        self.shared_steppable_vars['slimey'].targetVolume = perc * vol

    def volumeOscill(self, mcs):
        """ create the oscillation of the slime mold """
        per = math.sin((mcs / self.oscillFreq) * 2 * math.pi) + 1
        print("Oscillation: ", per)
        return per * self.oscillPercVolume

    def volumeDev(self):
        """ develop volume (either growth or shrinkage)"""
        self.basePercVolume += self.chanPercVolume
        print("Growth: ", self.basePercVolume)

    def relToFS(self):
        """ find the number of connected foodsources and calc additional volume """
        self.FSVolume = 0

        for cell in self.foodsources:
            for nbr, csa in self.get_cell_neighbor_data_list(cell):
                if nbr:
                    if nbr.type == 2:
                        self.FSVolume += self.addFSVolume

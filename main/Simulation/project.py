"""
Created: June 2011
Author: Niklas Semmler
Updated by: Joshua Apanavicius
Last Updated: May 2022
"""

from cc3d import CompuCellSetup
        

from projectSteppables import projectSteppable, VolumeAnnealingSteppable, SecretionSteppable

CompuCellSetup.register_steppable(steppable=projectSteppable(frequency=1))
CompuCellSetup.register_steppable(steppable=VolumeAnnealingSteppable(frequency=25))
CompuCellSetup.register_steppable(steppable=SecretionSteppable(frequency=50))


CompuCellSetup.run()

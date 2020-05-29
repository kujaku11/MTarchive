# -*- coding: utf-8 -*-
"""

Containers to hold the various groups Station, Run, Channel

Created on Fri May 29 15:09:48 2020

@author: jpeacock
"""
# =============================================================================
# Imports
# =============================================================================
import h5py
from mth5 import metadata

# =============================================================================
# 
# =============================================================================
class BaseGroup():
    """
    generic object that will have functionality for reading/writing groups, 
    including attributes and data.
    """
    
    def __init__(self, *args, **kwargs):
        self.relative_path = None
        self.mth5_obj = None
        
    def read_metadata(self):
        pass
    
    def write_metadata(self, meta_dict):
        pass
    
    def read_data(self):
        pass
    
    def write_data(self):
        pass
    
    
    

class StationGroup():
    """
    holds the station group
    
    """
    pass
    
class RunGroup():
    """
    holds the run group
    """
    pass
    
class ChannelGroup():
    """
    holds a channel
    """
    pass
    
class CalibrationGroup():
    """
    holds calibration group
    """
    pass
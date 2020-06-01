# -*- coding: utf-8 -*-
"""

Containers to hold the various groups Station, Run, Channel

Created on Fri May 29 15:09:48 2020

@author: jpeacock
"""
# =============================================================================
# Imports
# =============================================================================
import numpy as np
import weakref

from mth5 import metadata
from mth5.utils.helpers import to_numpy_type

# =============================================================================
# 
# =============================================================================
class BaseGroup():
    """
    generic object that will have functionality for reading/writing groups, 
    including attributes and data.
    """
    
    def __init__(self, group, *args, **kwargs):
        self.group = weakref.proxy(group)
        
    def __str__(self):
        lines = ['{0}:'.format(self.group.name)]
        for key, value in self.group.items():
            lines.append('\t{0}: {1}'.format(key, value))
        return '\n'.join(lines)
        
    def read_metadata(self):
        """
        read metadata
        
        :return: DESCRIPTION
        :rtype: TYPE

        """
        return dict([(key, value) for key, value in self.group.attrs.items()])
               
    def write_metadata(self, meta_dict):
        """
        Write metadata from a dictionary
        
        :param meta_dict: DESCRIPTION
        :type meta_dict: TYPE
        :return: DESCRIPTION
        :rtype: TYPE

        """
        
        for key, value in meta_dict.items():
            if value is None:
                value = 'none'
            self.group.attrs.create(key, to_numpy_type(value))

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
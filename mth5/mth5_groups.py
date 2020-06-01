# -*- coding: utf-8 -*-
"""

Containers to hold the various groups Station, Run, Channel

Created on Fri May 29 15:09:48 2020

@author: jpeacock
"""
# =============================================================================
# Imports
# =============================================================================
import inspect
import numpy as np
import weakref

from mth5 import metadata
from mth5.utils.helpers import to_numpy_type

meta_classes = dict(inspect.getmembers(metadata, inspect.isclass))
# =============================================================================
# 
# =============================================================================
class BaseGroup():
    """
    generic object that will have functionality for reading/writing groups, 
    including attributes and data.
    """
    
    def __init__(self, group, *args, **kwargs):
        self.group = weakref.ref(group)()
        self._class_name = self.__class__.__name__
        self.metadata = meta_classes[self._class_name.split('Group')[0]]
        
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
        meta_dict = dict([(key, value) for key, value in 
                          self.group.attrs.items()])
        
        self.metadata.from_dict({self.__class__.__name__: meta_dict})
               
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
    
    
    

class StationGroup(BaseGroup):
    """
    holds the station group
    
    """
    
    def __init__(self, *args, **kwargs):
        
        super(StationGroup, self).__init__(*args, **kwargs)
    
    
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
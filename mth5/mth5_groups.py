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
import logging
import h5py

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
    
    def __init__(self, group, **kwargs):
        
        if group is not None:
            self.group = weakref.ref(group)()
        self._class_name = self.__class__.__name__
        self.metadata = meta_classes[self._class_name.split('Group')[0]]()
        self.logger = logging.getLogger('{0}.{1}'.format(__name__, 
                                                         self._class_name))
        
        for key, value in kwargs.items():
            setattr(self, key, value)
        
    def __str__(self):
        return get_tree(self.group)
    
    def __eq__(self, other):
        pass
        
    def read_metadata(self):
        """
        read metadata
        
        :return: DESCRIPTION
        :rtype: TYPE

        """
        meta_dict = dict([(key, value) for key, value in 
                          self.group.attrs.items()])
        
        self.metadata.from_dict({self.__class__.__name__: meta_dict})
               
    def write_metadata(self):
        """
        Write metadata from a dictionary

        :return: DESCRIPTION
        :rtype: TYPE

        """
        meta_dict = self.metadata.to_dict()[self.metadata._class_name.lower()]
        for key, value in meta_dict.items():
            value = to_numpy_type(value)
            self.logger.debug('wrote metadata {0} = {1}'.format(key, value))
            self.group.attrs.create(key, value)

    def read_data(self):
        pass
    
    def write_data(self):
        pass
    
class SurveyGroup(BaseGroup):
    """
    holds the survey group
    
    """
    
    def __init__(self, group, **kwargs):
        
        super().__init__(group, **kwargs)
        
    def add_station(self, station):
        group_name = '{0}/{1}'.format('Stations', station)
        
        try:
            station_group = self.group.create_group(group_name)
            self.logger.debug("Created group {0}".format(station_group))
        except ValueError:
            msg = "Group {0} alread exists, returning existing group"
            self.logger.info(msg.format(group_name))
            station_group = self.group[group_name]
        
        station_obj = StationGroup(station_group)
        station_obj.write_metadata()
        return station_obj
    
        

class StationGroup(BaseGroup):
    """
    holds the station group
    
    """
    
    def __init__(self, group, **kwargs):
        
        super().__init__(group, **kwargs)
        
    @property
    def name(self):
        return self.metadata.archive_id
    
    @name.setter
    def name(self, name):
        self.metadata.archive_id = name
    
class RunGroup(BaseGroup):
    """
    holds the run group
    """
   
    def __init__(self, group, **kwargs):
        
        super().__init__(group, **kwargs)
    
class ChannelGroup(BaseGroup):
    """
    holds a channel
    """
    
    def __init__(self, group, **kwargs):
        
        super().__init__(group, **kwargs)
        
class ElectricGroup(BaseGroup):
    """
    holds a channel
    """
    
    def __init__(self, group, **kwargs):
        
        super().__init__(group, **kwargs)
        
class MagneticGroup(BaseGroup):
    """
    holds a channel
    """
    
    def __init__(self, group, **kwargs):
        
        super().__init__(group, **kwargs)
        
class AuxiliaryGroup(BaseGroup):
    """
    holds a channel
    """
    
    def __init__(self, group, **kwargs):
        
        super().__init__(group, **kwargs)
    
class CalibrationGroup(BaseGroup):
    """
    holds calibration group
    """
    
    def __init__(self, group, **kwargs):
        
        super().__init__(group, **kwargs)

def get_tree(parent):
    """
    Simple function to recursively print the contents of an hdf5 group
    Parameters
    ----------
    parent : :class:`h5py.Group`
        HDF5 (sub-)tree to print

    """
    lines = ['{0}:'.format(parent.name), '=' * 20]
    if not isinstance(parent, (h5py.File, h5py.Group)):
        raise TypeError('Provided object is not a h5py.File or h5py.Group '
                        'object')

    def fancy_print(name, obj):
        #lines.append(name)
        spacing = ' ' * 4 * (name.count('/') + 1)
        group_name = name[name.rfind('/') + 1:]

        lines.append('{0}|- {1}'.format(spacing, group_name))
        if isinstance(obj, h5py.Group):
            lines.append('{0}{1}'.format(spacing, 
                                         (len(group_name) + 5) * '-'))
            

    #lines.append(parent.name)
    parent.visititems(fancy_print) 
    return '\n'.join(lines)
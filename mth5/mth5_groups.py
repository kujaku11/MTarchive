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
import pandas as pd

from mth5 import metadata
from mth5.utils.helpers import to_numpy_type
from mth5.helpers import get_tree
from mth5.utils.exceptions import MTH5TableError


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
            # has to be a public or private attribute otherwise if its __ it
            # will not propagate
            self.hdf5_group = weakref.ref(group)()
        
        self.logger = logging.getLogger('{0}.{1}'.format(__name__, 
                                                         self._class_name))
        
        try:
            self.metadata = meta_classes[self._class_name.split('Group')[0]]()
        except KeyError:
            self.metadata = metadata.Base()
            
        self.logger.debug("setting metadata for {0} to {1}".format(
                self._class_name, type(self.metadata)))
            
        
        
        self._summary_defaults = {'name': 'Summary',
                                  'max_shape': (10000, ),
                                  'dtype': np.dtype([('default', np.float)])}
        
        for key, value in kwargs.items():
            setattr(self, key, value)
        
    def __str__(self):
        return get_tree(self.hdf5_group)
    
    def __eq__(self, other):
        pass
        
    @property
    def _class_name(self):
        return self.__class__.__name__
    
    def read_metadata(self):
        """
        read metadata
        
        :return: DESCRIPTION
        :rtype: TYPE

        """
        meta_dict = dict([(key, value) for key, value in 
                          self.hdf5_group.attrs.items()])
        
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
            self.hdf5_group.attrs.create(key, value)

    def read_data(self):
        pass
    
    def write_data(self):
        pass
    
    def initialize_summary_table(self):
        """
        Initialize summary table based on default values
        :return: DESCRIPTION
        :rtype: TYPE

        """
        
        self.hdf5_group.create_dataset(
            self._summary_defaults['name'], 
            (1, ),
            maxshape=self._summary_defaults['max_shape'],
            dtype=self._summary_defaults['dtype'])
        
        self.logger.debug(
            "Created {0} table with max_shape = {1}, dtype={2}".format(
                self._summary_defaults['name'],
                self._summary_defaults['max_shape'],
                self._summary_defaults['dtype']))
        
   
class SurveyGroup(BaseGroup):
    """
    holds the survey group
    
    """
    
    def __init__(self, group, **kwargs):
        
        super().__init__(group, **kwargs)
        
    def add_station(self, station):
        group_name = '{0}/{1}'.format('Stations', station)
        
        try:
            station_group = self.hdf5_group.create_group(group_name)
            self.logger.debug("Created group {0}".format(station_group))
        except ValueError:
            msg = "Group {0} alread exists, returning existing group"
            self.logger.info(msg.format(group_name))
            station_group = self.hdf5_group[group_name]
        
        station_obj = StationGroup(station_group)
        station_obj.write_metadata()
        return station_obj
    
class StationGroup(BaseGroup):
    """
    holds the station group
    
    """
    
    def __init__(self, group, **kwargs):
        
        super().__init__(group, **kwargs)
        self._summary_defaults = {'name': 'Summary',
                                  'max_shape': (1000,),
                                  'dtype': np.dtype([('name', 'S5'),
                                                     ('start', 'S32'),
                                                     ('end', 'S32'),
                                                     ('components', 'S100'),
                                                     ('measurement_type',
                                                      'S12'),
                                                     ('location.latitude',
                                                      np.float),
                                                     ('location.longitude',
                                                      np.float)])}
        
    @property
    def name(self):
        return self.metadata.archive_id
    
    @name.setter
    def name(self, name):
        self.metadata.archive_id = name
        
    @property
    def summary_table(self):
        return self.hdf5_group['Summary']
    

        
class ReportsGroup(BaseGroup):
    """
    holds the reports group
    
    """
    
    def __init__(self, group, **kwargs):
        
        super().__init__(group, **kwargs)
        
class StandardsGroup(BaseGroup):
    """
    holds the standards group
    
    """
    
    def __init__(self, group, **kwargs):
        
        super().__init__(group, **kwargs) 
        
class FiltersGroup(BaseGroup):
    """
    holds calibration group
    """
    
    def __init__(self, group, **kwargs):
        
        super().__init__(group, **kwargs)
    
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
        
class MTH5Table():
    """
    we will try to use Pandas as the table container.
    
    All functionality of pandas.Dataframe will be provided in 
    MTH5Table.dataframe.  Some helper functions are provided for convenience.
    
    """
    
    def __init__(self, hdf5_dataset):
        self.logger = logging.getLogger('{0}.{1}'.format(
            __name__, self.__class__.__name__))
        
        if isinstance(hdf5_dataset, h5py.Dataset):
            self.dataframe = pd.DataFrame(np.array(hdf5_dataset,
                                                 dtype=hdf5_dataset.dtype))
        else:
            msg = "Input must be a h5py.Dataset not {0}".format(
                type(hdf5_dataset))
            self.logger.error(msg)
            raise MTH5TableError(msg)
            
    @property
    def dtypes(self):
        try:
            return self.dataframe.dtypes
        except AttributeError as error:
            msg = '{0}, dataframe is not initiated yet'.format(error)
            self.logger.warning(msg)
            return None
            
    def add_row(self, row):
        """
        Add a row to the table.
        
        row must be of the same data type as the table, can be a DataFrame
        or numpy.ndarray with correct data type
        
        
        :param row: row entry for the table
        :type row: TYPE
        :return: DESCRIPTION
        :rtype: TYPE

        """
        
        if not isinstance(row, (np.ndarray, pd.DataFrame)):
            msg = ("Input must be an numpy.ndarray or pandas.DataFrame" + 
                   "not {0}".format(type(row)))
        if isinstance(row, np.ndarray):
            row = pd.DataFrame(row)
        
        try:
            compare = row.dtypes == self.dataframe.dtypes
        except ValueError as error:
            msg = '{0}\ninput dtypes:\n{1}\n\nTable dtypes:\n{2}'.format(
                error, row.dtypes, self.dtypes)
            self.logger.exception(msg)
            raise ValueError(msg)
        if not compare.all(axis=None):
            msg = ("Row is not the correct data type, should be \n{0}\n " +
                   " not \n{1}")

            self.logger.error(msg.format(row.dtypes, self.dtypes))
            raise ValueError(msg.format(row.dtypes, self.dtypes))
        self.dataframe = self.dataframe.append(row, ignore_index=True)
        
    def remove_row(self, key, value):
        """
        Delete a row based on a key and given value
        
        
        :param key: DESCRIPTION
        :type key: TYPE
        :param value: DESCRIPTION
        :type value: TYPE
        :return: DESCRIPTION
        :rtype: TYPE

        """
        if key not in list(self.dtypes.keys()):
            msg = "{0} not in dtype:\n{1}".format(key,
                                                  list(self.dtypes.keys()))
            self.logger.error(msg)
            raise ValueError(msg)
            
        remove_index = self.dataframe.index[getattr(self.dataframe,
                                                    key) == value]
        if len(remove_index) == 1:
            self.logger.debug("found {0} = {1} at index {2}, removing".format(
                key, value, remove_index))
        elif len(remove_index) > 1:
            self.logger.info("found {0} = {1} at indexes {2}, removing".format(
                key, value, remove_index))
        else:
            self.logger.info("did not find {0} = {1}".format(key, value))
        
        self.dataframe.drop(remove_index, inplace=True)
        
    def to_nparray(self):
        return np.array([tuple(v) for v in self.dataframe.values.tolist()], 
                 dtype=self.dtypes)
        
        
        
          



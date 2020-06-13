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
        
        self.metadata = metadata.Base()
        if self._class_name not in ['Standards']:
            try:
                self.metadata = meta_classes[self._class_name]()
            except KeyError:
                self.metadata = metadata.Base()
            
        self.metadata.add_base_attribute('mth5_type', 
                                         self._class_name.split('Group')[0],
                                         {'type':str, 
                                          'required':True,
                                          'style':'free form',
                                          'description': 'type of group', 
                                          'units':None,
                                          'options':[],
                                          'alias':[],
                                          'example':'group_name'})
            
        self.logger.debug("setting metadata for {0} to {1}".format(
                self._class_name, type(self.metadata)))
            
        
        
        self._defaults_summary_attrs = {'name': 'Summary',
                                  'max_shape': (10000, ),
                                  'dtype': np.dtype([('default', np.float)])}
        
        
        for key, value in kwargs.items():
            setattr(self, key, value)
        
    def __str__(self):
        try: 
            self.hdf5_group.ref
            
            return get_tree(self.hdf5_group)
        except ValueError:
            msg = 'MTH5 file is closed and cannot be accessed.'
            self.logger.warning(msg)
            return msg
    
    def __repr__(self):
        return self.__str__()
    
    def __eq__(self, other):
        pass
        
    @property
    def _class_name(self):
        return self.__class__.__name__.split('Group')[0]
    
    @property
    def summary_table(self):
        return MTH5Table(self.hdf5_group['Summary'])
    
    def read_metadata(self):
        """
        read metadata
        
        :return: DESCRIPTION
        :rtype: TYPE

        """
        meta_dict = dict([(key, value) for key, value in 
                          self.hdf5_group.attrs.items()])
        
        self.metadata.from_dict({self._class_name: meta_dict})
               
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
        
        summary_table = self.hdf5_group.create_dataset(
            self._defaults_summary_attrs['name'], 
            (1, ),
            maxshape=self._defaults_summary_attrs['max_shape'],
            dtype=self._defaults_summary_attrs['dtype'])
        
        summary_table.attrs.update({'type': 'summary table',
                                    'last_updated': 'date_time',
                                    'reference': summary_table.ref})
        
        self.logger.debug(
            "Created {0} table with max_shape = {1}, dtype={2}".format(
                self._defaults_summary_attrs['name'],
                self._defaults_summary_attrs['max_shape'],
                self._defaults_summary_attrs['dtype']))
        
   
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
    

class MasterStationGroup(BaseGroup):
    """
    holds the station group
    
    """
    
    def __init__(self, group, **kwargs):
        
        super().__init__(group, **kwargs)
        
        self.metadata = metadata.Base()
        
        self._default_group_attr = {'type': self._class_name.split('Group')[0],
                                    'h5_reference': self.hdf5_group.ref}
        
        self._defaults_summary_attrs = {'name': 'Summary',
                                  'max_shape': (1000,),
                                  'dtype': np.dtype([('archive_id', 'S5'),
                                                     ('start', 'S32'),
                                                     ('end', 'S32'),
                                                     ('components', 'S100'),
                                                     ('measurement_type',
                                                      'S12'),
                                                     ('location.latitude',
                                                      np.float),
                                                     ('location.longitude',
                                                      np.float),
                                                     ('hdf5_reference', 
                                                      h5py.ref_dtype)])}
        
    @property
    def name(self):
        return self.metadata.archive_id
    
    @name.setter
    def name(self, name):
        self.metadata.archive_id = name
        
class StationGroup(BaseGroup):
    """
    holds the station group
    
    """
    
    def __init__(self, group, **kwargs):
        
        super().__init__(group, **kwargs)
        
        self._defaults_summary_attrs = {'name': 'Summary',
                                        'max_shape': (1000,),
                                        'dtype': np.dtype([
                                            ('id', 'S5'),
                                            ('start', 'S32'),
                                            ('end', 'S32'),
                                            ('components', 'S100'),
                                            ('measurement_type', 'S12'),
                                            ('sample_rate', np.float)])}
        
    @property
    def name(self):
        return self.metadata.archive_id
    
    @name.setter
    def name(self, name):
        self.metadata.archive_id = name

class ReportsGroup(BaseGroup):
    """
    holds the reports group
    
    """
    
    def __init__(self, group, **kwargs):
        
        super().__init__(group, **kwargs)
        
        self._defaults_summary_attrs = {'name': 'Summary',
                                  'max_shape': (1000,),
                                  'dtype': np.dtype([('name', 'S5'),
                                                     ('type', 'S32'),
                                                     ('summary', 'S200')])}
        
class StandardsGroup(BaseGroup):
    """
    holds the standards group
    
    """
    
    def __init__(self, group, **kwargs):
        
        super().__init__(group, **kwargs)
        
        self._defaults_summary_attrs = {'name': 'Summary',
                                  'max_shape': (500,),
                                  'dtype': np.dtype([('attribute', 'S72'),
                                                     ('type', 'S15'),
                                                     ('required', np.bool_),
                                                     ('style', 'S72'),
                                                     ('units', 'S32'),
                                                     ('description', 'S300'),
                                                     ('options', 'S150'),
                                                     ('alias', 'S72'),
                                                     ('example', 'S72')])} 
    
    def from_dict(self, summary_dict):
        """
        Fill summary table from a dictionary 
        
        :param summary_dict: DESCRIPTION
        :type summary_dict: TYPE
        :return: DESCRIPTION
        :rtype: TYPE

        """
        
        for key, v_dict in summary_dict.items():
            key_list = [key]
            for dkey in self.summary_table.dtype.names[1:]:
                value = v_dict[dkey]
                
                if isinstance(value, list):
                    if len(value) == 0:
                        value = ''
                        
                    else:
                        value = ','.join(['{0}'.format(ii) for ii in 
                                                  value])
                if value is None:
                    value = ''
                    
                key_list.append(value)
            
            key_list = np.array([tuple(key_list)], self.summary_table.dtype)
            index = self.summary_table.add_row(key_list)
        
        
        
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
    Use the underlying NumPy basics, there are simple actions in this table, 
    if a user wants to use something more sophisticated for querying they 
    should try using a pandas table.  In this case entries in the table 
    are more difficult to change and datatypes need to be kept track of. 
    
    
    
    """
    
    def __init__(self, hdf5_dataset):
        self.logger = logging.getLogger('{0}.{1}'.format(
            __name__, self.__class__.__name__))
        
        if isinstance(hdf5_dataset, h5py.Dataset):
            self.array = weakref.ref(hdf5_dataset)()
        else:
            msg = "Input must be a h5py.Dataset not {0}".format(
                type(hdf5_dataset))
            self.logger.error(msg)
            raise MTH5TableError(msg)
            
    def __str__(self):
        """
        return a string that shows the table in text form
    
        :return: text representation of the table
        :rtype: string

        """
        length_dict = dict([(key, max([len(str(b)) for b in self.array[key]]))
                            for key in list(self.dtype.names)])
        lines = [' | '.join(['index']+['{0:^{1}}'.format(name, 
                                                         length_dict[name]) 
                             for name in list(self.dtype.names)])]
        lines.append('-' * len(lines[0]))
        for ii, row in enumerate(self.array):
            line = ['{0:^5}'.format(ii)]
            for element, key in zip(row, list(self.dtype.names)):
                if isinstance(element, (np.bytes_)):
                    element = element.decode()
                try:
                    line.append('{0:^{1}}'.format(element, length_dict[key]))
                
                except TypeError as error:
                    if isinstance(element, h5py.h5r.Reference):
                        msg = '{0}: Cannot represent h5 reference as a string'
                        self.logger.debug(msg.format(error))
                        line.append('{0:^{1}}'.format('<HDF5 object reference>',
                                                      length_dict[key]))
                    else:
                        self.logger.exception(f'{error}')
                        
            lines.append(' | '.join(line))
        return '\n'.join(lines)
    
    def __repr__(self):
        return self.__str__()
    
    def __eq__(self, other):
        if isinstance(other, MTH5Table): 
            return self.array == other.array
        elif isinstance(other, h5py.Dataset):
            return self.array == other
        else:
            msg = "Cannot compare type={0}".format(type(other))
            self.logger.error(msg)
            raise TypeError(msg)
            
    def __ne__(self, other):
        return not self.__eq__(other) 

    def __len__(self):
        return self.array.shape[0]                    
            
    @property
    def dtype(self):
        try:
            return self.array.dtype
        except AttributeError as error:
            msg = '{0}, dataframe is not initiated yet'.format(error)
            self.logger.warning(msg)
            return None
        
    def check_dtypes(self, other_dtype):
        """
        Check to make sure datatypes match
        """
        
        if self.dtype == other_dtype:
            return True
        
        return False
    
    @property
    def shape(self):
        return self.array.shape
    
    @property
    def nrows(self):
        return self.array.shape[0]
    
    def locate(self, column, value, test='eq'):
        """
        
        locate index where column is equal to value
        :param column: DESCRIPTION
        :type column: TYPE
        :param value: DESCRIPTION
        :type value: TYPE
        :type test: type of test to try
            * 'eq': equals
            * 'lt': less than
            * 'le': less than or equal to
            * 'gt': greater than
            * 'ge': greater than or equal to.
            * 'be': between or equal to
            * 'bt': between
            
        If be or bt input value as a list of 2 values
            
        :return: DESCRIPTION
        :rtype: TYPE

        """
        if isinstance(value, str):
            value = np.bytes_(value)
            
        # use numpy datetime for testing against time.    
        if column in ['start', 'end', 'start_date', 'end_date']:
            test_array = self.array[column].astype(np.datetime64)
            value = np.datetime64(value)
        else:
            test_array = self.array[column]
        
        if test == 'eq':
            index_values = np.where(test_array == value)[0] 
        elif test == 'lt':
            index_values = np.where(test_array < value)[0]
        elif test == 'le':
            index_values = np.where(test_array <= value)[0]
        elif test == 'gt':
            index_values = np.where(test_array > value)[0]
        elif test == 'ge':
            index_values = np.where(test_array >= value)[0]
        elif test == 'be':
            if not isinstance(value, (list, tuple, np.ndarray)):
                msg = ("If testing for between value must be an iterable of" +
                      " length 2.")
                self.logger.error(msg)
                raise ValueError(msg)
                
            index_values = np.where((test_array > value[0]) & 
                                    (test_array < value[1]))[0]
        else:
            raise ValueError('Test {0} not understood'.format(test))
            
        return index_values
            
    def add_row(self, row, index=None):
        """
        Add a row to the table.
        
        row must be of the same data type as the table
        
        
        :param row: row entry for the table
        :type row: TYPE
        
        :param index: index of row to add
        :type index: integer, if None is given then the row is added to the
                     end of the array
                     
        :return: index of the row added
        :rtype: integer

        """
        
        if not isinstance(row, (np.ndarray)):
            msg = ("Input must be an numpy.ndarray" + 
                   "not {0}".format(type(row)))
        if isinstance(row, np.ndarray):
            if not self.check_dtypes(row.dtype):
                msg = '{0}\nInput dtypes:\n{1}\n\nTable dtypes:\n{2}'.format(
                    'Data types are not equal:', row.dtype, self.dtype)
                self.logger.error(msg)
                raise ValueError(msg)

        if index is None:
            index = self.nrows
            new_shape = tuple([self.nrows + 1] + [ii for ii in self.shape[1:]])
            self.array.resize(new_shape)
        
        # add the row
        self.array[index] = row
        self.logger.debug('Added row as index {0} with values {1}'.format(
            index, row))
        
        return index
        

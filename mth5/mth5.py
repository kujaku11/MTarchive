# -*- coding: utf-8 -*-
"""
==================
MTH5
==================

This module deals with reading and writing MTH5 files, which are HDF5 files
developed for magnetotelluric (MT) data.  The code is based on h5py and
attributes use JSON encoding.

.. note:: Currently the convenience methods support read only.  
          Working on developing the write convenience methods.

Created on Sun Dec  9 20:50:41 2018

@author: J. Peacock
"""

# =============================================================================
# Imports
# =============================================================================
import os
import datetime
import time
import json
import dateutil
import logging
import weakref

import h5py
import pandas as pd
import numpy as np

from pathlib import Path
from platform import platform

from mth5.utils.exceptions import MTH5Error
from mth5 import __version__
from mth5.utils.mttime import get_now_utc
from mth5 import mth5_groups as m5groups 
from mth5.helpers import get_tree, close_open_files

# =============================================================================
# MT HDF5 file
# =============================================================================
class MTH5():
    """
    MT HDF5 file

    Class object to deal with reading and writing an MTH5 file.

    ======================= ===================================================
    Attribute               Description
    ======================= ===================================================
    copyright               Copyright object containing information on
                            copyright information
    field_notes             FieldNotes object containing information on how
                            the data was collected
    mth5_fn                 full path to MTH5 file
    mth5_obj                HDF5 object from h5py
    provenance              Provenance object containing information on when
                            and by whom the data was collected
    site                    Site object containing information about the
                            location of the station
    software                Software object containing information on the
                            software used to make the file
    schedule_##             Schedule object where ## is the number of the
                            schedule if a MTH5 file was read in
    calibration_##          Calibration object where ## is the component of
                            the calibration
    ======================= ===================================================

    .. seealso:: mth5.Copyright, mth5.FieldNotes, mth5.Provenance, mth5.Site
                 mth5.Software, mth5.Schedule, mth5.Calibration, h5py

    ============================ ==============================================
    Method                       Description
    ============================ ==============================================
    open_mth5                    load in a MTH5 file
    close_mth5                   flushes any changes and closes MTH5 file
    add_schedule                 add a schedule data set
    add_calibration              add instrument calibration to /root/calibrations
    write_metadata               write root metadata
    update_metadata_from_cfg     update metadata attributes from a cfg file
    update_metadata_from_series  update metadata attributes from pandas series
    h5_is_write                  check if MTH5 file is open and writeable
    ============================ ==============================================

    * Example: Load MTH5 File
    
    >>> import mth5.mth5 as mth5
    >>> data = mth5.MTH5.open_mth5(r"/home/mtdata/mt01.mth5")

    * Example: Update metadata from cfg file
    
    >>> data = mth5.MTH5()
    >>> # read in configuration file to update attributes
    >>> data.update_metadata_from_cfg(r"/home/survey_mth5.cfg")
    >>> data.write_metadata()
    
    * Example: Add schedule to MTH5 File
    
    >>> schedule_obj = mth5.Schedule()
    >>> # make schedule object from a pandas dataframe
    >>> import pandas as pd
    >>> sdf = df = pd.DataFrame(np.random.random((256*3600+1, 5)),
    ...                         columns=['ex', 'ey', 'hx', 'hy', 'hz'],
    ...                         index=pd.date_range(start='2018-01-01T01:00:00',
    ...                                             end='2018-01-01T02:00:00',
    ...                                             freq='{0:.0f}N'.format(1./256.*1E9)))
    >>> data.schedule_01 = schedule_obj.from_dataframe(sdf, 'schedule_01')
        
    * Example: Add calibration from structured numpy array

    >>> import numpy as np
    >>> cal = mth5.Calibration()
    >>> cal_dtype = [(name, np.float) for name in ['frequency', 'real', 'imaginary']]
    >>> cal.from_numpy_array(np.zeros(20), dtype=cal_dtype)
    >>> cal.frequency = np.logspace(-3, 3, 20)
    >>> cal.real = np.random.random(20)
    >>> cal.imaginary = np.random.random(20)
    >>> cal.name = 'hx'
    >>> cal.instrument_id = 2284
    >>> cal.calibration_date = '2018-01-01'
    >>> cal.calibration_person.name = 'tester name'
    >>> cal.calibration_person.organization = 'tester company'
    >>> data.calibrations.calibration_hx = data.add_calibration(cal, 'hx')
    
    * Example: Update data
    
    >>> data.schedule_01.ex[0:10] = np.nan
    >>> data.calibration_hx[...] = np.logspace(-4, 4, 20)
    
    .. note:: if replacing an entire array with a new one you need to use [...]
              otherwise the data will not be updated.  
              
    .. warning:: You can only replace entire arrays with arrays of the same 
                 size.  Otherwise you need to delete the existing data and 
                 make a new dataset.  
                 
    .. seealso:: https://www.hdfgroup.org/ and h5py()
    """

    def __init__(self, filename=None):
        self.__hdf5_obj = None
        
        self.__filename = filename
        if self.__filename:
            if not isinstance(self.__filename, Path):
                self.__filename = Path(self.__filename)

        self._class_name = self.__class__.__name__
        self.logger = logging.getLogger('{0}.{1}'.format(__name__, 
                                                         self._class_name))
        
        self._default_root_name = 'Survey'
        self._default_subgroup_names =['Stations', 'Reports', 'Filters',
                                       'Standards']
        
        self._file_attrs = {'file.type': 'MTH5',
                            'file.access.platform': platform(),
                            'file.access.time': get_now_utc(),
                            'MTH5.version': __version__,
                            'MTH5.software': 'pymth5'}
        
        
    def __str__(self):
        return get_tree(self.__hdf5_obj)
        
    @property
    def filename(self):
        if self.h5_is_write():
            return Path(self.__hdf5_obj.filename)
        else:
            msg = ('MTH5 file is not open or has not been created yet. ' +
                   'Returning default name')
            self.logger.warning(msg)
            return self.__filename

    @property
    def survey_group(self):
        if self.h5_is_write():
            return m5groups.SurveyGroup(self.__hdf5_obj['/Survey'])
        else:
            self.logger.info("File is closed cannot access /Survey")
            return None
        
    @property
    def reports_group(self):
        if self.h5_is_write():
            return m5groups.ReportsGroup(self.__hdf5_obj['/Survey/Reports'])
        else:
            self.logger.info("File is closed cannot access /Reports")
            return None

    @property
    def filters_group(self):
        if self.h5_is_write():
            return m5groups.FiltersGroup(self.__hdf5_obj['/Survey/Filters'])
        else:
            self.logger.info("File is closed cannot access /Filters")
            return None        

    @property
    def standards_group(self):
        if self.h5_is_write():
            return m5groups.StandardsGroup(
                self.__hdf5_obj['/Survey/Standards'])
        else:
            self.logger.info("File is closed cannot access /Standards")
            return None 

    @property
    def stations_group(self):
        if self.h5_is_write():
            return m5groups.StationGroup(self.__hdf5_obj['/Survey/Stations'])
        else:
            self.logger.info("File is closed cannot access /Reports")
            return None

    def open_mth5(self, filename, mode='a'):
        """
        open an mth5 file
        
        :return: Survey Group 
        :type: m5groups.SurveyGroup
        
        :Example: ::
            
            >>> from mth5 import mth5
            >>> mth5_object = mth5.MTH5()
            >>> survey_object = mth5_object.open_mth5('Test.mth5', 'w')
            
        
        """
        self.__filename = filename
        if not isinstance(self.__filename, Path):
            self.__filename = Path(filename)
            
        if self.__filename.exists():
            if mode in ['w']:
                self.logger.warning("{0} will be overwritten in 'w' mode".format(
                    self.__filename.name))
                try:
                    self.initialize_file(self.__filename)
                except OSError as error:
                    msg = ('{0}. Need to close any references to {1} first. ' +
                           'Then reopen the file in the preferred mode')
                    self.logger.exception(msg.format(error, self.__filename))
            elif mode in ['a', 'r', 'r+', 'w-', 'x']:
                self.__hdf5_obj = h5py.File(self.__filename, mode=mode)

            else:
                msg = "mode {0} is not understood".format(mode)
                self.logger.error(msg)
                raise MTH5Error(msg)
        else:
            if mode in ['a', 'w', 'w-', 'x']:
                self.initialize_file(self.__filename)
            else:
                msg = "Cannot open new file in mode {0} ".format(mode)
                self.logger.error(msg)
                raise MTH5Error(msg)

    def initialize_file(self, filename):
        """
        Initialize the default groups for the file
        
        :return: Survey Group
        :rtype: m5groups.SurveyGroup

        """
        
        self.__hdf5_obj = h5py.File(self.__filename, 'w')
        
        # write general metadata
        self.__hdf5_obj.attrs.update(self._file_attrs)
        
        survey_group = self.__hdf5_obj.create_group(self._default_root_name)
        survey_obj = m5groups.SurveyGroup(survey_group)
        survey_obj.write_metadata()
        
        for group_name in self._default_subgroup_names:
            grp = self.__hdf5_obj.create_group('{0}/{1}'.format(
                    self._default_root_name, group_name))
            if 'station' in group_name.lower():
                grp.create_dataset('Summary',
                                   (1, ),
                                   maxshape=self._station_summary['max_size'],
                                   dtype=self._station_summary['dtype'])
            
        self.logger.info("Initialized MTH5 file {0} in mode {1}".format(
            self.filename, 'w'))
        
        return survey_obj        

    def close_mth5(self):
        """
        close mth5 file to make sure everything is flushed to the file
        """
        fn = str(self.filename)
        self.__hdf5_obj.flush()       
        self.__hdf5_obj.close()
        self.logger.info("Flushed and closed {0}".format(fn))
        
    def h5_is_write(self):
        """
        check to see if the hdf5 file is open and writeable
        """
        if isinstance(self.__hdf5_obj, h5py.File):
            try:
                if 'w' in self.__hdf5_obj.mode or '+' in self.__hdf5_obj.mode:
                    return True
                elif self.__hdf5_obj.mode == 'r':
                    return False
            except ValueError:
                return False
        return False
    
    def add_station(self, name):
        """
        Add a station and returns the group container.  The station name
        needs to be the same as the archive_id name.  A 5 character 
        alphanumeric string.
        
        :param station: DESCRIPTION
        :type station: TYPE
        :return: DESCRIPTION
        :rtype: TYPE

        """
        
        try:
            station_group = self.stations_group.create_group(name)
            self.logger.debug("Created group {0}".format(station_group.name))
        except ValueError:
            msg = "Group {0} alread exists, returning existing group"
            self.logger.info(msg.format(name))
            station_group = self.station_group[name]
        
        return m5groups.StationGroup(station_group)
        
        
    
    def add_run(self, station, run):
        """
        add a run to the given station
        """
        pass
    
    def add_channel(self, station, run, channel):
        """
        add a channel to the given station/run
        """
        pass
    

    # def write_metadata(self, meta_dict):
    #     """
    #     Write metadata to the HDf5 file as json strings under the headings:
    #     """
    #     if self.h5_is_write():
    #         for attr in ['site', 'field_notes', 'copyright', 'provenance',
    #                      'software']:
    #             self.__hdf5_obj.attrs[attr] = getattr(self, attr).to_json()

#     def add_schedule(self, schedule_obj, compress=True):
#         """
#         add a schedule object to the HDF5 file

#         :param schedule_obj: container holding the time series data as a
#                              pandas.DataFrame with columns as components
#                              and indexed by time.
#         :type schedule_obj: mtf5.Schedule object
        
#         :param bool compress: [ True | False ] to internally compress the data
        
#         .. note:: will name the schedule according to schedule_obj.name.  
#                   Should be schedule_## where ## is the order of the schedule
#                   as a 2 character digit [0-9][0-9] 
#         """

#         if self.h5_is_write():
#             ### create group for schedule action
#             schedule = self.__hdf5_obj.require_group(schedule_obj.name)
#             ### add metadata
#             for attr in schedule_obj._attrs_list:
#                 schedule.attrs[attr] = getattr(schedule_obj, attr)

#             ### add datasets for each channel
#             for comp in schedule_obj.comp_list:
#                 if compress:
#                     schedule.create_dataset(comp.lower(),
#                                             data=getattr(schedule_obj, comp),
#                                             compression='gzip',
#                                             compression_opts=9)
#                 else:
#                     schedule.create_dataset(comp.lower(),
#                                             data=getattr(schedule_obj, comp))
#             ### set the convenience attribute to the schedule
#             setattr(self, schedule_obj.name, Schedule())
#             getattr(self, schedule_obj.name).from_mth5(self.__hdf5_obj, 
#                                                        schedule_obj.name)
            
#         else:
#             raise MTH5Error('{0} is not writeable'.format(self.mth5_fn))
            
#     def remove_schedule(self, schedule_name):
#         """
#         Remove a schedule item given schedule name.
        
#         :param str schedule_name: schedule name verbatim of the one you want
#                                   to delete.
                                  
#         .. note:: This does not free up memory, it just simply deletes the 
#                   link to the schedule item.  See
#                   http://docs.h5py.org/en/stable/high/group.html.  The best
#                   method would be to build a different file without the data
#                   your are trying to delete.
#         """
#         if self.h5_is_write():
#             try:
#                 delattr(self, schedule_name)
#                 del self.__hdf5_obj['/{0}'.format(schedule_name)]
#             except AttributeError:
#                 print("Could not find {0}, not an attribute".format(schedule_name))

#         else:
#             raise MTH5Error("File not open")
            
#     def add_calibration(self, calibration_obj, compress=True):
#         """
#         add calibrations for sensors

#         :param calibration_obj: calibration object that has frequency, real,
#                                 imaginary attributes
#         :type calibration_obj: mth5.Calibration

#         """

#         if self.h5_is_write():
#             cal = self.__hdf5_obj['/calibrations'].require_group(calibration_obj.name)
#             cal.attrs['metadata'] = calibration_obj.to_json()
#             for col in calibration_obj._col_list:
#                 if compress:
#                     cal.create_dataset(col.lower(),
#                                        data=getattr(calibration_obj, col),
#                                        compression='gzip',
#                                        compression_opts=9)
#                 else:
#                     cal.create_dataset(col.lower(),
#                                        data=getattr(calibration_obj, col))
            
#             ### set the convenience attribute to the calibration
#             setattr(self, calibration_obj.name, Calibration())
#             getattr(self, calibration_obj.name).from_mth5(self.__hdf5_obj, 
#                                                           calibration_obj.name)
#         else:
#             raise MTH5Error('{0} is not writeable'.format(self.mth5_fn))
            
#     def remove_calibration(self, calibration_name):
#         """
#         Remove a calibration item given calibration name.
        
#         :param str calibration_name: calibration name verbatim of the one you
#                                      want to delete.
                                  
#         .. note:: This does not free up memory, it just simply deletes the 
#                   link to the schedule item.  See
#                   http://docs.h5py.org/en/stable/high/group.html.  The best
#                   method would be to build a different file without the data
#                   your are trying to delete.
#         """
#         if self.h5_is_write():
#             try:
#                 delattr(self, calibration_name)
#                 del self.__hdf5_obj['calibrations/{0}'.format(calibration_name)]
#             except AttributeError:
#                 print("Could not find {0}, not an attribute".format(calibration_name))
#         else:
#             raise MTH5Error("File not open")
    
#     def update_schedule_metadata(self):
#         """
#         update schedule metadata on the HDF file
#         """
        
#         for key in self.__dict__.keys():
#             if 'sch' in key:
#                 for attr in getattr(self, key)._attrs_list:
#                     value = getattr(getattr(self, key), attr)
#                     self.__hdf5_obj[key].attrs[attr] = value

#     def read_mth5(self, mth5_fn):
#         """
#         Read MTH5 file and update attributes
        
#         :param str mth5_fn: full path to mth5 file
#         """
        
#         if not os.path.isfile(mth5_fn):
#             raise MTH5Error("Could not find {0}, check path".format(mth5_fn))

#         self.mth5_fn = mth5_fn
#         ### read in file and give write permissions in case the user wants to
#         ### change any parameters
#         self.__hdf5_obj = h5py.File(self.mth5_fn, 'r+')
#         for attr in ['site', 'field_notes', 'copyright', 'provenance',
#                      'software']:
#             getattr(self, attr).from_json(self.__hdf5_obj.attrs[attr])

#         for key in self.__hdf5_obj.keys():
#             if 'sch' in key:
#                 setattr(self, key, Schedule())
#                 getattr(self, key).from_mth5(self.__hdf5_obj, key)
#             elif 'cal' in key:
#                 try:
#                     for ckey in self.__hdf5_obj[key].keys():
#                         m_attr = 'calibration_{0}'.format(ckey)
#                         setattr(self, m_attr, Calibration())
#                         getattr(self, m_attr).from_mth5(self.__hdf5_obj, ckey)
#                 except KeyError:
#                     print('No Calibration Data')

#     def update_metadata_from_cfg(self, mth5_cfg_fn):
#         """
#         read a configuration file for all the mth5 attributes

#         :param mth5_cfg_fn: full path to configuration file for mth5 file
#         :type mth5_cfg_fn: string

#         The configuration file has the format::
            
#             ###===================================================###
#             ### Metadata Configuration File for Science Base MTH5 ###
#             ###===================================================###

#             ### Site information --> mainly for location
#             site.id = MT Test
#             site.coordinate_system = Geomagnetic North
#             site.datum = WGS84
#             site.declination = 15.5
#             site.declination_epoch = 1995
#             site.elevation = 1110
#             site.elev_units = meters
#             site.latitude = 40.12434
#             site.longitude = -118.345
#             site.survey = Test
#             site.start_date = 2018-05-07T20:10:00.0
#             site.end_date = 2018-07-07T10:20:30.0
#             #site._date_fmt = None

#             ### Field Notes --> for instrument setup
#             # Data logger information
#             field_notes.data_logger.id = ZEN_test
#             field_notes.data_logger.manufacturer = Zonge
#             field_notes.data_logger.type = 32-Bit 5-channel GPS synced
#         """
#         usgs_str = 'U.S. Geological Survey'
#         # read in the configuration file
#         with open(mth5_cfg_fn, 'r') as fid:
#             lines = fid.readlines()

#         for line in lines:
#             # skip comment lines
#             if line.find('#') == 0 or len(line.strip()) < 2:
#                 continue
#             # make a key = value pair
#             key, value = [item.strip() for item in line.split('=', 1)]

#             if value == 'usgs_str':
#                 value = usgs_str
#             if value.find('[') >= 0 and value.find(']') >= 0 and value.find('<') != 0:
#                 value = value.replace('[', '').replace(']', '')
#                 value = [v.strip() for v in value.split(',')]
#             if value.find('.') > 0:
#                 try:
#                     value = float(value)
#                 except ValueError:
#                     pass
#             else:
#                 try:
#                     value = int(value)
#                 except ValueError:
#                     pass

#             # if there is a dot, meaning an object with an attribute separate
#             if key.count('.') == 0:
#                 setattr(self, key, value)
#             elif key.count('.') == 1:
#                 obj, obj_attr = key.split('.')
#                 setattr(getattr(self, obj), obj_attr, value)
#             elif key.count('.') == 2:
#                 obj, obj_attr_01, obj_attr_02 = key.split('.')
#                 setattr(getattr(getattr(self, obj), obj_attr_01), obj_attr_02,
#                         value)

#     def update_metadata_from_series(self, station_series, update_time=False):
#         """
#         Update metadata from a pandas.Series with old keys as columns:
#             * station
#             * latitude
#             * longitude
#             * elevation
#             * declination
#             * start_date
#             * stop_date
#             * datum
#             * coordinate_system
#             * units
#             * instrument_id
#             * ex_azimuth
#             * ex_length
#             * ex_sensor
#             * ex_num
#             * ey_azimuth
#             * ey_length
#             * ey_sensor
#             * ey_num
#             * hx_azimuth
#             * hx_sensor
#             * hx_num
#             * hy_azimuth
#             * hy_sensor
#             * hy_num
#             * hz_azimuth
#             * hz_sensor
#             * hz_num
#             * quality

#         :param station_series: pandas.Series with the above index values
#         :type station_series: pandas.Series
        
#         :param update_time: boolean to update the start and stop time
#         :type update_time: [ True | False ]
#         """
#         if isinstance(station_series, pd.DataFrame):
#             station_series = station_series.iloc[0]

#         assert isinstance(station_series, pd.Series), \
#                 'station_series is not a pandas.Series'

#         for key in station_series.index:
#             value = getattr(station_series, key)
#             if key in self.site._attrs_list:
#                 setattr(self.site, key, value)
#             elif key == 'start_date':
#                 if not update_time:
#                     continue
#                 attr = key
#                 setattr(self.site, attr, value)
#             elif key == 'stop_date':
#                 if not update_time:
#                     continue
#                 attr = 'end_date'
#                 setattr(self.site, attr, value)
#             elif key == 'instrument_id':
#                 self.field_notes.data_logger.id = value
#             elif key == 'quality':
#                 self.field_notes.data_quality.rating = value
#             elif key == 'notes':
#                 self.field_notes.data_quality.comments = value
#             elif key == 'station':
#                 self.site.id = value
#             elif key == 'units':
#                 self.site.elev_units = value
#             elif key[0:2] in ['ex', 'ey', 'hx', 'hy', 'hz']:
#                 comp = key[0:2]
#                 attr = key.split('_')[1]
#                 if attr == 'num':
#                     attr = 'chn_num'
#                 if attr == 'sensor':
#                     attr = 'id'
#                 if 'e' in comp:
#                     setattr(getattr(self.field_notes, 'electrode_{0}'.format(comp)),
#                             attr, value)
#                 elif 'h' in comp:
#                     setattr(getattr(self.field_notes, 'magnetometer_{0}'.format(comp)),
#                             attr, value)

# # ==============================================================================
# #             Error
# # ==============================================================================


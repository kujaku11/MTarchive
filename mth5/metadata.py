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

import datetime
import json
import pandas as pd
import numpy as np
from dateutil import parser as dtparser
from pathlib import Path


# =============================================================================
#  global parameters
# =============================================================================
dt_fmt = '%Y-%m-%dT%H:%M:%S.%f %Z'

#==============================================================================
# Need a dummy utc time zone for the date time format
#==============================================================================
class UTC(datetime.tzinfo):
    """
    An class to hold information about UTC
    """
    def utcoffset(self, df):
        return datetime.timedelta(hours=0)
    def dst(self, df):
        return datetime.timedelta(0)
    def tzname(self, df):
        return "UTC"


class Generic(object):
    """
    A generic class that is common to most of the Metadata objects
    
    Includes:
        * to_json
        * from_json
        * to_dict
        * from_dict
    """
    
    def __init__(self, **kwargs):
        
        for key, value in kwargs.items():
            setattr(self, key, value)
            
    def to_json(self):
        """
        Write a json string from a given object, taking into account other
        class objects contained within the given object.
        """
        
        return to_json(self)

    def from_json(self, json_str):
        """
        read in a json string and update attributes of an object

        :param json_str: json string
        :type json_str: string
    
        """
        from_json(json_str, self)
        
    def to_dict(self):
        """
        make a dictionary from attributes, makes dictionary from _attr_list.
        """
        meta_dict = {}
        for key in list(self._attr_dict.keys()):
            meta_dict[key] = self.get_attribute(key)
                                                
        return meta_dict
                
    def from_dict(self, meta_dict):
        """
        fill attributes from a dictionary
        """
        for key, value in meta_dict.items():
            self.set_attribute(key, value)
    
    def get_attribute(self, key):
        if '/'  in key:
            if key.count('/') == 1:
                attr_class, attr_key = key.split('/')
                return getattr(getattr(self, attr_class), attr_key)
            elif key.count('/') == 2:
                attr_master, attr_class, attr_key = key.split('/')
                return getattr(getattr(getattr(self, attr_master), 
                                       attr_class), 
                               attr_key)
        else:
            return getattr(self, key)
        
    def set_attribute(self, key, value):
        if '/'  in key:
            if key.count('/') == 1:
                attr_class, attr_key = key.split('/')
                setattr(getattr(self, attr_class), attr_key, value)
            elif key.count('/') == 2:
                attr_master, attr_class, attr_key = key.split('/')
                setattr(getattr(getattr(self, attr_master), 
                                attr_class), attr_key, value)
        else:
            setattr(self, key, value)
        
            
# ==============================================================================
# Location class, be sure to put locations in decimal degrees, and note datum
# ==============================================================================       
class Declination(object):
    """
    declination container
    """
    def __init__(self, **kwargs):
        self.value_d = None
        self.units_s = None
        self.epoch_s = None
        self.model_s = None
        
class Location(Generic):
    """
    location details including:
        * latitude
        * longitude
        * elevation
        * datum
        * coordinate_system
        * declination
    """

    def __init__(self, **kwargs):
        #super(Location, self).__init__()
        self.datum_s = 'WGS84'
        self.declination = Declination()

        self._elevation = None
        self._latitude = None
        self._longitude = None

        self.elev_units = 'm'
        self.coordinate_system_s = 'Geographic North'

        for key, value in kwargs.items():
            setattr(self, key, value)

    @property
    def latitude_d(self):
        return self._latitude

    @latitude_d.setter
    def latitude_d(self, lat):
        self._latitude = self._assert_lat_value(lat)

    @property
    def longitude_d(self):
        return self._longitude

    @longitude_d.setter
    def longitude_d(self, lon):
        self._longitude = self._assert_lon_value(lon)

    @property
    def elevation_d(self):
        return self._elevation

    @elevation_d.setter
    def elevation_d(self, elev):
        self._elevation = self._assert_elevation_value(elev)
            
    def _assert_lat_value(self, latitude):
        """
        Make sure the latitude value is in decimal degrees, if not change it.
        And that the latitude is within -90 < lat > 90.
        
        :param latitude: latitude in decimal degrees or other format
        :type latitude: float or string
        """
        if latitude in [None, 'None']:
            return None
        try:
            lat_value = float(latitude)
    
        except TypeError:
            return None
    
        except ValueError:
            lat_value = self._convert_position_str2float(latitude)
    
        if abs(lat_value) >= 90:
            print("==> The lat_value =", lat_value)
            raise ValueError('|Latitude| > 90, unacceptable!')
    
        return lat_value
    
    def _assert_lon_value(self, longitude):
        """
        Make sure the longitude value is in decimal degrees, if not change it.
        And that the latitude is within -180 < lat > 180.
        
        :param latitude: longitude in decimal degrees or other format
        :type latitude: float or string
        """
        if longitude in [None, 'None']:
            return None
        try:
            lon_value = float(longitude)
    
        except TypeError:
            return None
    
        except ValueError:
            lon_value = self._convert_position_str2float(longitude)
    
        if abs(lon_value) >= 180:
            print("==> The longitude_value =", lon_value)
            raise ValueError('|Longitude| > 180, unacceptable!')
    
        return lon_value
    
    def _assert_elevation_value(self, elevation):
        """
        make sure elevation is a floating point number
        
        :param elevation: elevation as a float or string that can convert
        :type elevation: float or str
        """
    
        try:
            elev_value = float(elevation)
        except (ValueError, TypeError):
            elev_value = 0.0
    
        return elev_value
    
    def _convert_position_float2str(self, position):
        """
        Convert position float to a string in the format of DD:MM:SS.

        :param position: decimal degrees of latitude or longitude
        :type position: float
                           
        :returns: latitude or longitude in format of DD:MM:SS.ms
        """
    
        assert type(position) is float, 'Given value is not a float'
    
        deg = int(position)
        sign = 1
        if deg < 0:
            sign = -1
    
        deg = abs(deg)
        minutes = (abs(position) - deg) * 60.
        # need to round seconds to 4 decimal places otherwise machine precision
        # keeps the 60 second roll over and the string is incorrect.
        sec = np.round((minutes - int(minutes)) * 60., 4)
        if sec >= 60.:
            minutes += 1
            sec = 0
    
        if int(minutes) == 60:
            deg += 1
            minutes = 0
            
        position_str = '{0}:{1:02.0f}:{2:05.2f}'.format(sign * int(deg),
                                                        int(minutes),
                                                        sec)
    
        return position_str
    
    def _convert_position_str2float(self, position_str):
        """
        Convert a position string in the format of DD:MM:SS to decimal degrees
        
         :param position: latitude or longitude om DD:MM:SS.ms
        :type position: float
                           
        :returns: latitude or longitude as a float
        """
    
        if position_str in [None, 'None']:
            return None
        
        p_list = position_str.split(':')
        if len(p_list) != 3:
            raise ValueError('{0} not correct format, should be DD:MM:SS'.format(position_str))
    
        deg = float(p_list[0])
        minutes = self._assert_minutes(float(p_list[1]))
        sec = self._assert_seconds(float(p_list[2]))
    
        # get the sign of the position so that when all are added together the
        # position is in the correct place
        sign = 1
        if deg < 0:
            sign = -1
    
        position_value = sign * (abs(deg) + minutes / 60. + sec / 3600.)
    
        return position_value
    
    def _assert_minutes(self, minutes):
        assert 0 <= minutes < 60., \
            'minutes needs to be <60 and >0, currently {0:.0f}'.format(minutes)
    
        return minutes

    def _assert_seconds(self, seconds):
        assert 0 <= seconds < 60., \
            'seconds needs to be <60 and >0, currently {0:.3f}'.format(seconds)
        return seconds

# ==============================================================================
# Instrument
# ==============================================================================
class Instrument(Generic):
    """
    Information on an instrument that was used.

    Holds the following information:

    ================= =========== =============================================
    Attributes         Type        Explanation
    ================= =========== =============================================
    id                string      serial number or id number of data logger
    manufacturer      string      company whom makes the instrument
    type              string      Broadband, long period, something else
    ================= =========== =============================================

    More attributes can be added by inputing a key word dictionary

    >>> Instrument(**{'ports':'5', 'gps':'time_stamped'})
    """

    def __init__(self, **kwargs):
        super(Instrument, self).__init__()
        self.id_s = None
        self.manufacturer_s = None
        self.type_s = None

        for key, value in kwargs.items():
            setattr(self, key, value)
            

# ==============================================================================
# Data Quality
# ==============================================================================
class DataQuality(Generic):
    """
    Information on data quality.

    Holds the following information:

    ================= =========== =============================================
    Attributes         Type        Explanation
    ================= =========== =============================================
    comments          string      comments on data quality
    good_from_period  float       minimum period data are good
    good_to_period    float       maximum period data are good
    rating            int         [1-5]; 1 = poor, 5 = excellent
    warrning_comments string      any comments on warnings in the data
    warnings_flag     int         [0-#of warnings]
    ================= =========== =============================================

    More attributes can be added by inputing a key word dictionary

    >>> DataQuality(**{'time_series_comments':'Periodic Noise'})
    """

    def __init__(self, **kwargs):
        super(DataQuality, self).__init__()
        self.comments = None
        self.rating = None
        self.warnings_comments = None
        self.warnings_flag = 0
        self.author = None

        for key, value in kwargs.items():
            setattr(self, key, value)

# ==============================================================================
# Citation
# ==============================================================================
class Citation(Generic):
    """
    Information for a citation.

    Holds the following information:

    ================= =========== =============================================
    Attributes         Type        Explanation
    ================= =========== =============================================
    author            string      Author names
    title             string      Title of article, or publication
    journal           string      Name of journal
    doi               string      DOI number (doi:10.110/sf454)
    year              int         year published
    ================= =========== =============================================

    More attributes can be added by inputing a key word dictionary

    >>> Citation(**{'volume':56, 'pages':'234--214'})
    """

    def __init__(self, **kwargs):
        super(Citation, self).__init__()
        self.author_s = None
        self.title_s = None
        self.journal_s = None
        self.volume_s = None
        self.doi_s = None
        self.year_s = None

        for key, value in kwargs.items():
            setattr(self, key, value)

# ==============================================================================
# Copyright
# ==============================================================================
class Copyright(Generic):
    """
    Information of copyright, mainly about how someone else can use these
    data. Be sure to read over the conditions_of_use.

    Holds the following information:

    ================= =========== =============================================
    Attributes         Type        Explanation
    ================= =========== =============================================
    citation          Citation    citation of published work using these data
    conditions_of_use string      conditions of use of these data
    release_status    string      release status [ open | public | proprietary]
    ================= =========== =============================================

    More attributes can be added by inputing a key word dictionary

    >>> Copyright(**{'owner':'University of MT', 'contact':'Cagniard'})
    """

    def __init__(self, **kwargs):
        super(Copyright, self).__init__()
        self.citation = Citation()
        self.conditions_of_use = ''.join(['All data and metadata for this survey are ',
                                          'available free of charge and may be copied ',
                                          'freely, duplicated and further distributed ',
                                          'provided this data set is cited as the ',
                                          'reference. While the author(s) strive to ',
                                          'provide data and metadata of best possible ',
                                          'quality, neither the author(s) of this data ',
                                          'set, not IRIS make any claims, promises, or ',
                                          'guarantees about the accuracy, completeness, ',
                                          'or adequacy of this information, and expressly ',
                                          'disclaim liability for errors and omissions in ',
                                          'the contents of this file. Guidelines about ',
                                          'the quality or limitations of the data and ',
                                          'metadata, as obtained from the author(s), are ',
                                          'included for informational purposes only.'])
        self.release_status = None
        self.additional_info = None

        for key, value in kwargs.items():
            setattr(self, key, value)

# ==============================================================================
# Provenance
# ==============================================================================
class Provenance(Generic):
    """
    Information of the file history, how it was made

    Holds the following information:

    ====================== =========== ========================================
    Attributes             Type        Explanation
    ====================== =========== ========================================
    creation_time          string      creation time of file YYYY-MM-DD,hh:mm:ss
    creating_application   string      name of program creating the file
    creator                Person      person whom created the file
    submitter              Person      person whom is submitting file for
                                       archiving
    ====================== =========== ========================================

    More attributes can be added by inputing a key word dictionary

    >>> Provenance(**{'archive':'IRIS', 'reprocessed_by':'grad_student'})
    """

    def __init__(self, **kwargs):
        super(Provenance, self).__init__()
        self.creation_time_s = datetime.datetime.utcnow().isoformat()
        self.creating_application_s = 'MTH5'
        self.creator= Person()
        self.submitter = Person()
        self.software = Software()
        self.log_s = None
        self.notes_s = None

        for key, value in kwargs.items():
            setattr(self, key, value)

# ==============================================================================
# Person
# ==============================================================================
class Person(Generic):
    """
    Information for a person

    Holds the following information:

    ================= =========== =============================================
    Attributes         Type        Explanation
    ================= =========== =============================================
    email             string      email of person
    name              string      name of person
    organization      string      name of person's organization
    organization_url  string      organizations web address
    ================= =========== =============================================

    More attributes can be added by inputing a key word dictionary

    >>> Person(**{'phone':'650-888-6666'})
    """

    def __init__(self, **kwargs):
        super(Person, self).__init__()
        self.email_s = None
        self.author_s = None
        self.organization_s = None
        self.url_s = None

        for key, value in kwargs.items():
            setattr(self, key, value)

# ==============================================================================
# Software
# ==============================================================================
class Software(Generic):
    """
    software
    """

    def __init__(self, **kwargs):
        super(Software, self).__init__()
        self.name_s = None
        self.version_s = None
        self.author = Person()

        for key, value in kwargs.items():
            setattr(self, key, value)

    @property
    def author_s(self):
        return self.author.author_s
    
    @author_s.setter
    def author_s(self, value):
        self.author.author_s = value
# ==============================================================================
# Site details
# ==============================================================================
class Survey(Generic):
    """
    Information on the survey, including location, id, etc.
    

    """

    def __init__(self, **kwargs):
        
        super(Survey, self).__init__()
        self.acquired_by = Person()
        self._start_date = None
        self._end_date = None
        self.name_s = None
        self.id_s = None
        self.net_code_s = None
        self.northwest_corner = Location()
        self.southeast_corner = Location()
        self.datum_s = None
        self.location_s = None
        self.country_s = None
        self.summary_s = None
        self.notes_s = None
        self.acquired_by = Person()
        self.conditions_of_use_s = None
        self.release_status_s = None
        self.citation_dataset = Citation()
        self.citation_journal = Citation()
       
        self._attr_dict = {'name_s': {'type':str, 'required':True},
                           'id_s': {'type':str, 'required':True},
                           'net_code_s': {'type':str, 'required':True},
                           'start_date_s': {'type':str, 'required':True},
                           'end_date_s': {'type':str, 'required':True},
                           'northwest_corner/latitude_d': {'type':float,
                                                           'required':True},
                           'northwest_corner/longitude_d': {'type':float, 
                                                            'required':True},
                           'southeast_corner/latitude_d': {'type':float, 
                                                           'required':True},
                           'southeast_corner/longitude_d': {'type':float,
                                                           'required':True},
                           'datum_s': {'type':str, 'required':True},
                           'location_s': {'type':str, 'required':True},
                           'country_s': {'type':str, 'required':True},
                           'summary_s': {'type':str, 'required':True},
                           'notes_s': {'type':str, 'required':True},
                           'acquired_by/author_s': {'type':str,
                                                    'required':True},
                           'acquired_by/organization_s': {'type':str, 
                                                          'required':True},
                           'acquired_by/email_s': {'type':str, 
                                                   'required':True},
                           'acquired_by/url_s': {'type':str, 'required':True},
                           'release_status_s': {'type':str, 'required':True},
                           'conditions_of_use_s': {'type':str,
                                                   'required':True},
                           'citation_dataset/doi_s': {'type':str,
                                                      'required':True},
                           'citation_journal/doi_s': {'type':str, 
                                                      'required':True}}

        for key, value in kwargs.items():
            setattr(self, key, value)
            
    @property
    def start_date_s(self):
        try:
            return self._start_date.date().isoformat()
        except (TypeError, AttributeError):
            return None

    @start_date_s.setter
    def start_date_s(self, start_date):
        self._start_date = dtparser.parse(start_date)
        if self._start_date.tzname() is None:
            self._start_date = self._start_date.replace(tzinfo=UTC())

    @property
    def end_date_s(self):
        try:
            return self._stop_date.date().isoformat()
        except (TypeError, AttributeError):
            return None

    @end_date_s.setter
    def end_date_s(self, stop_date):
        self._stop_date = dtparser.parse(stop_date)
        if self._stop_date.tzname() is None:
            self._stop_date = self._stop_date.replace(tzinfo=UTC())

# =============================================================================
# Station Class
# =============================================================================
class Station(Location):
    """
    station object
    """
    def __init__(self, **kwargs):
        super(Station, self).__init__()
        self.sta_code_s = None
        self.name_s = None
        self.notes_s = None
        self.datum_s = None
        self.start_s = None
        self.end_s = None
        self.num_channels_i = None
        self.channels_recorded_s = None
        self.data_type_s = None
        self.station_orientation_s = None
        self.orientation_method_s = None
        self.acquired_by = Person()
        self.provenance = Provenance() 
        
        self._attr_dict = {'sta_code_s': {'type':str, 'required':True},
                           'name_s':{'type':str, 'required':True},
                           'latitude_d':{'type':str, 'required':True},
                           'longitude_d':{'type':float, 'required':True},
                           'elevation_d':{'type':float, 'required':True},
                           'notes_s':{'type':str, 'required':True},
                           'datum_s':{'type':str, 'required':True},
                           'start_s':{'type':str, 'required':True},
                           'end_s':{'type':str, 'required':True},
                           'num_channels_i':{'type':int, 'required':True},
                           'channels_recorded_s':{'type':str, 
                                                  'required':True},
                           'data_type_s':{'type':str, 'required':True},
                           'declination/value_d':{'type':float,
                                                  'required':True},
                           'declination/units_s':{'type':str,
                                                  'required':True},
                           'declination/epoch_s':{'type':str, 
                                                  'required':True},
                           'declination/model_s':{'type':str, 
                                                  'required':True},
                           'station_orientation_s':{'type':str,
                                                    'required':True},
                           'orientation_method_s':{'type':str,
                                                   'required':True},
                           'acquired_by/author_s':{'type':str,
                                                   'required':True},
                           'acquired_by/email_s':{'type':str,
                                                  'required':True},
                           'provenance/creation_time_s':{'type':str,
                                                         'required':True},
                           'provenance/software/name_s':{'type':str,
                                                         'required':True},
                           'provenance/software/version_s':{'type':str,
                                                            'required':True},
                           'provenance/software/author_s':{'type':str, 
                                                           'required':True},
                           'provenance/submitter/author_s':{'type':str, 
                                                            'required':True},
                           'provenance/submitter/organization_s':{'type':str, 
                                                                  'required':True},
                           'provenance/submitter/url_s':{'type':str, 
                                                         'required':True},
                           'provenance/submitter/email_s':{'type':str, 
                                                           'required':True},
                           'provenance/notes_s':{'type':str,
                                                 'required':True},
                           'provenance/log_s':{'type':str,
                                               'required':True}}
        
        
# =============================================================================
# schedule
# =============================================================================
class Schedule(object):
    """
    Container for a single schedule item

    :Metadata keywords:

          ===================== =======================================
          name                  description
          ===================== =======================================
          station               station name
          latitude              latitude of station (decimal degrees)
          longitude             longitude of station (decimal degrees)
          hx_azimuth            azimuth of HX (degrees from north=0)
          hy_azimuth            azimuth of HY (degrees from north=0)
          hz_azimuth            azimuth of HZ (degrees from horizon=0)
          ex_azimuth            azimuth of EX (degrees from north=0)
          ey_azimuth            azimuth of EY (degrees from north=0)
          hx_sensor             instrument id number for HX
          hy_sensor             instrument id number for HY
          hz_sensor             instrument id number for HZ
          ex_sensor             instrument id number for EX
          ey_sensor             instrument id number for EY
          ex_length             dipole length (m) for EX
          ey_length             dipole length (m) for EX
          ex_num                channel number of EX
          ey_num                channel number of EX
          hx_num                channel number of EX
          hy_num                channel number of EX
          hz_num                channel number of EX
          instrument_id         instrument id
          ===================== =======================================
    """

    def __init__(self, name=None, meta_df=None):

        self.ex = None
        self.ey = None
        self.hx = None
        self.hy = None
        self.hz = None
        self.dt_index = None
        self.name = name

        self._comp_list = ['ex', 'ey', 'hx', 'hy', 'hz']
        self._attrs_list = ['name',
                            'start_time',
                            'stop_time',
                            'start_seconds_from_epoch',
                            'stop_seconds_from_epoch',
                            'n_samples',
                            'n_channels',
                            'sampling_rate']

        #self.ts_df = time_series_dataframe
        self.meta_df = meta_df

    @property
    def start_time(self):
        """
        Start time in UTC string format
        """
        return '{0}'.format(self.dt_index[0].strftime(dt_fmt))

    @property
    def stop_time(self):
        """
        Stop time in UTC string format
        """
        return '{0}'.format(self.dt_index[-1].strftime(dt_fmt))

    @property
    def start_seconds_from_epoch(self):
        """
        Start time in epoch seconds
        """
        return self.dt_index[0].to_datetime64().astype(np.int64)/1e9

    @property
    def stop_seconds_from_epoch(self):
        """
        sopt time in epoch seconds
        """
        return self.dt_index[-1].to_datetime64().astype(np.int64)/1e9

    @property
    def n_channels(self):
        """
        number of channels
        """

        return len(self.comp_list)

    @property
    def sampling_rate(self):
        """
        sampling rate
        """
        return np.round(1.0e9/self.dt_index[0].freq.nanos, decimals=1)

    @property
    def n_samples(self):
        """
        number of samples
        """
        return self.dt_index.shape[0]

    @property
    def comp_list(self):
        """
        component list for the given schedule
        """
        return [comp for comp in self._comp_list
                if getattr(self, comp) is not None]

    def make_dt_index(self, start_time, sampling_rate, stop_time=None,
                      n_samples=None):
        """
        make time index array

        .. note:: date-time format should be YYYY-M-DDThh:mm:ss.ms UTC

        :param start_time: start time
        :type start_time: string

        :param end_time: end time
        :type end_time: string

        :param sampling_rate: sampling_rate in samples/second
        :type sampling_rate: float
        """

        # set the index to be UTC time
        dt_freq = '{0:.0f}N'.format(1./(sampling_rate)*1E9)
        if stop_time is not None:
            dt_index = pd.date_range(start=start_time,
                                     end=stop_time,
                                     freq=dt_freq,
                                     closed='left',
                                     tz='UTC')
        elif n_samples is not None:
            dt_index = pd.date_range(start=start_time,
                                     periods=n_samples,
                                     freq=dt_freq,
                                     tz='UTC')
        else:
            raise ValueError('Need to input either stop_time or n_samples')

        return dt_index

    def from_dataframe(self, ts_dataframe):
        """
        update attributes from a pandas dataframe.

        Dataframe should have columns:
            * ex
            * ey
            * hx
            * hy
            * hz
        and should be indexed by time.

        :param ts_dataframe: dataframe holding the data
        :type ts_datarame: pandas.DataFrame
        """
        try:
            assert isinstance(ts_dataframe, pd.DataFrame) is True
        except AssertionError:
            raise TypeError('ts_dataframe is not a pandas.DataFrame object.\n',
                            'ts_dataframe is {0}'.format(type(ts_dataframe)))

        for col in ts_dataframe.columns:
            try:
                setattr(self, col.lower(), ts_dataframe[col])
            except AttributeError:
                print("\t xxx skipping {0} xxx".format(col))
        self.dt_index = ts_dataframe.index

        return

    def from_mth5(self, mth5_obj, name):
        """
        make a schedule object from mth5 file

        :param mth5_obj: an open mth5 object
        :type mth5_obj: mth5.MTH5 open object

        :param name: name of schedule to use
        :type name: string
        """
        mth5_schedule = mth5_obj[name]

        self.name = name

        for comp in self._comp_list:
            try:
                setattr(self, comp, mth5_schedule[comp])
            except KeyError:
                print('\t xxx No {0} data for {1} xxx'.format(comp, self.name))
                continue

        self.dt_index = self.make_dt_index(mth5_schedule.attrs['start_time'],
                                           mth5_schedule.attrs['sampling_rate'],
                                           n_samples=mth5_schedule.attrs['n_samples'])
        assert self.dt_index.shape[0] == getattr(self, self.comp_list[0]).shape[0]
        return

    def from_numpy_array(self, schedul_np_array, start_time, stop_time,
                         sampling_rate):
        """
        TODO
        update attributes from a numpy array
        """
        pass


    def write_metadata_csv(self, csv_dir):
        """
        write metadata to a csv file
        """
        csv_fn = self._make_csv_fn(csv_dir)
        self.meta_df.to_csv(csv_fn, header=False)

        return csv_fn

    def _make_csv_fn(self, csv_dir):
        """
        create csv file name from data.
        """
        if not isinstance(self.meta_df, pd.Series):
            raise ValueError('meta_df is not a Pandas Series, {0}'.format(type(self.meta_df)))
        csv_fn = '{0}_{1}_{2}_{3}.csv'.format(self.meta_df.station,
                                              self.dt_index[0].strftime('%Y%m%d'),
                                              self.dt_index[0].strftime('%H%M%S'),
                                              int(self.sampling_rate))

        return Path(csv_dir).joinpath(csv_fn)

# =============================================================================
# Calibrations
# =============================================================================
class Calibration(Generic):
    """
    container for insturment calibrations

    Each instrument should be a separate class

    Metadata should be:
        * instrument_id
        * calibration_date
        * calibration_person
        * units
    """

    def __init__(self, name=None):
        super(Calibration, self).__init__()
        self.name = name
        self.instrument_id = None
        self.units = None
        self.calibration_date = None
        self.calibration_person = Person()
        self.frequency = None
        self.real = None
        self.imaginary = None
        self._col_list = ['frequency', 'real', 'imaginary']
        self._attrs_list = ['name',
                           'instrument_id',
                           'units',
                           'calibration_date',
                           'calibration_person']
        


    def from_dataframe(self, cal_dataframe, name=None):
        """
        updated attributes from a pandas DataFrame

        :param cal_dataframe: dataframe with columns frequency, real, imaginary
        :type cal_dataframe: pandas.DataFrame

        """
        assert isinstance(cal_dataframe, pd.DataFrame) is True

        if name is not None:
            self.name = name

        for col in cal_dataframe.columns:
            setattr(self, col, cal_dataframe[col])

    def from_numpy_array(self, cal_np_array, name=None):
        """
        update attributes from a numpy array

        :param cal_np_array: array of values for calibration, see below
        :type cal_np_array: numpy.ndarray

        if array is a numpy structured array names need to be:
            * frequency
            * real
            * imaginary

        if array is just columns, needs to be ordered:
            * frequency (index 0)
            * real (index 1)
            * imaginary (index 2)

        """
        if name is not None:
            self.name = name

        ### assume length of 1 is a structured array
        if len(cal_np_array.shape) == 1:
            assert cal_np_array.dtype.names == ('frequency', 'real', 'imaginary')
            for key in cal_np_array.dtype.names:
                setattr(self, key, cal_np_array[key])

        ### assume an unstructured array (f, r, i)
        if len(cal_np_array.shape) == 2 and cal_np_array.shape[0] == 3:
            for ii, key in enumerate(['frequency', 'real', 'imaginary']):
                setattr(self, key, cal_np_array[ii, :])

        return

    def from_mth5(self, mth5_obj, name):
        """
        update attribues from mth5 file
        """
        self.name = name
        for key in mth5_obj['/calibrations/{0}'.format(self.name)].keys():
            setattr(self, key, mth5_obj['/calibrations/{0}/{1}'.format(self.name,
                                                                       key)])

        ### read in attributes
        self.from_json(mth5_obj['/calibrations/{0}'.format(self.name)].attrs['metadata'])
        
    def from_csv(self, cal_csv, name=None, header=False):
        """
        Read a csv file that is in the format frequency,real,imaginary
        
        :param cal_csv: full path to calibration csv file
        :type cal_csv: string
        
        :param name: instrument id
        :type name: string
        
        :param header: boolean if there is a header in the csv file
        :type header: [ True | False ]
        
        """
        if not header:
            cal_df = pd.read_csv(cal_csv, header=None, names=self._col_list)
        else:
            cal_df = pd.read_csv(cal_csv, names=self._col_list)
            
        if name is not None:
            self.name
        self.from_dataframe(cal_df)
        
class NumpyEncoder(json.JSONEncoder):
    """
    Need to encode numpy ints and floats for json to work
    """
    def default(self, obj):
        if isinstance(obj, (np.int_, np.intc, np.intp, np.int8,
                            np.int16, np.int32, np.int64, np.uint8,
                            np.uint16, np.uint32, np.uint64)):
            return int(obj)

        elif isinstance(obj, (np.float_, np.float16, np.float32, np.float64)):
            return float(obj)

        elif isinstance(obj,(np.ndarray)):
            return obj.tolist()

        return json.JSONEncoder.default(self, obj)

def to_json(obj):
    """
    write a json string from a given object, taking into account other class
    objects contained within the given object.

    :param obj: class object to transform into string
    """
    if isinstance(obj, (Station, Calibration)):
        keys = obj._attrs_list
    else:
        keys = obj.__dict__.keys()

    obj_dict = {}
    for key in keys:
        if key.find('_') == 0:
            continue
        value = getattr(obj, key)

        if isinstance(value, (Instrument, DataQuality, Citation, 
                              Provenance, Person, Software)):
            obj_dict[key] = {}
            for o_key, o_value in value.__dict__.items():
                if o_key.find('_') == 0:
                    continue
                obj_dict[key][o_key] = o_value

        elif isinstance(value, (Station, Calibration)):
            obj_dict[key] = {}
            for o_key in value._attrs_list:
                if o_key.find('_') == 0:
                    continue
                obj_dict[key][o_key] = getattr(obj, o_key)
        else:
            obj_dict[key] = value

    return json.dumps(obj_dict, cls=NumpyEncoder)

def from_json(json_str, obj):
    """
    read in a json string and update attributes of an object

    :param json_str: json string
    :type json_str:string

    :param obj: class object to update
    :type obj: class object

    :returns obj:
    """

    obj_dict = json.loads(json_str)

    for key, value in obj_dict.items():
        if isinstance(value, dict):
            for o_key, o_value in value.items():
                setattr(getattr(obj, key), o_key, o_value)
        else:
            setattr(obj, key, value)

    return obj
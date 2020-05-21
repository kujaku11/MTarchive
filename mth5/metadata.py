# -*- coding: utf-8 -*-
"""
==================
metadata
==================

This module deals with metadata as defined by the MT metadata standards.

There are multiple containers for each type of metadata, named appropriately.

Each container will be able to read and write:
    * dictionary
    * json
    * xml?
    * csv
    * pandas
    * anything else?

Because a lot of the name words in the metadata are split by '.' there are some
issues we need to deal with.  I wrote in get and set attribute functions
to handle these types of names so the user shouldn't have to work about
splitting the names themselves.

These containers will be the building blocks for the metadata and how they are
interchanged between the HDF5 file and the user.  A lot of the metadata you
can get directly from the raw time series files, but the user will need to
input a decent amount on their own.  Dictionaries are the most fundamental
type we should be dealing with.

Each container has an attribute called _attr_dict which dictates if the
attribute is included in output objects, the data type, whether it is a
required parameter, and the style of output.  This should help down the road
with validation and keeping the data types consistent.  And if things change
you should only have to changes these dictionaries.

self._attr_dict = {'nameword':{'type': str, 'required': True, 'style': 'name'}}

Created on Sun Apr 24 20:50:41 2020

@author: J. Peacock
@email: jpeacock@usgs.gov


"""
# =============================================================================
# Imports
# =============================================================================
import json
import pandas as pd
import numpy as np
import logging
import re

from collections import OrderedDict
from operator import itemgetter

from mth5.standards.schema import (ATTR_DICT, validate_attribute,
                                   validate_type)
from mth5.utils.mttime import MTime
from mth5.utils.exceptions import MTSchemaError

# =============================================================================
#  Base class that everything else will inherit
# =============================================================================
class Base():
    """
    A Base class that is common to most of the Metadata objects

    Includes:
        * to_json
        * from_json
        * to_dict
        * from_dict
        * to_series
        * from_series
    """

    def __init__(self, **kwargs):

        self.notes_s = None
        self._attr_dict = {}
        self.logger = logging.getLogger('{0}.{1}'.format(__name__, 
                                                     self.__class__.__name__))

        for name, value in kwargs.items():
            self.set_attr_from_name(name, value)

    def __str__(self):
        lines = []
        for name, value in self.to_dict().items():
            lines.append('{0} = {1}'.format(name, value))
        return '\n'.join(lines)

    def __repr__(self):
        return self.to_json()


    def _validate_name(self, name):
        """
        validate the name to conform to the standards
        name must be:
            * all lower case {a-z; 1-9}
            * must start with a letter
            * categories are separated by '.'
            * words separated by '_'

        {object}.{name_name}

        '/' will be replaced with '.'
        converted to all lower case

        :param name: name name
        :type name: string
        :return: valid name name
        :rtype: string

        """
        return validate_attribute(name)

    def __setattr__(self, name, value):
        """
        set attribute based on metadata standards

        """
        # skip these attribute because they are validated in the property 
        # setter.
        skip_list = ['latitude_d', 'longitude_d',  'elevation_d',
                     'start_date_s', 'end_date_s', 'start_s', 'end_s',
                     'name_s', 'applied_b', 'logger']
        if hasattr(self, '_attr_dict'):
            if name[0] != '_':
                if not name in skip_list: 
                    self.logger.debug('Setting {0} to {1}'.format(name, 
                                                                  value))
                    v_type = self._get_standard_type(name)
                    value = self._validate_type(value, v_type)

        super().__setattr__(name, value)

    def _get_standard_type(self, name):
        """
        helper function to get the standard type for the given name
        """
        name = self._validate_name(name)
        try:
            standards = self._attr_dict[name]
            return standards['type']
        except KeyError:
            if name[0] != '_':
                msg = ('{0} is not defined in the standards. ' +
                      ' Should add attribute information with ' +
                      'add_base_attribute if the attribute is going to ' +
                      'propogate via to_dict, to_json, to_series')
                self.logger.info(msg.format(name))
            return None

    def get_attr_from_name(self, name):
        """
        Access attribute from the given name.

        The name can contain the name of an object which must be separated
        by a '.' for  e.g. {object_name}.{name} --> location.latitude

        ..note:: this is a helper function for names with '.' in the name for
                 easier getting when reading from dictionary.

        :param name: name of attribute to get.
        :type name: string
        :return: attribute value
        :rtype: type is defined by the attribute name

        :Example: ::

            >>> b = Base(**{'category.test_attr':10})
            >>> b.get_attr_from_name('category.test_attr')
            10

        """
        name = self._validate_name(name)
        v_type = self._get_standard_type(name)

        if '.'  in name:
            if name.count('.') == 1:
                attr_class, attr_name = name.split('.')
                value = getattr(getattr(self, attr_class), attr_name)

            elif name.count('.') == 2:
                attr_master, attr_class, attr_name = name.split('.')
                value = getattr(getattr(getattr(self, attr_master),
                                        attr_class),
                                attr_name)
        else:
            value = getattr(self, name)

        return self._validate_type(value, v_type)

    def set_attr_from_name(self, name, value):
        """
        Helper function to set attribute from the given name.

        The name can contain the name of an object which must be separated
        by a '.' for  e.g. {object_name}.{name} --> location.latitude

        ..note:: this is a helper function for names with '.' in the name for
                 easier getting when reading from dictionary.

        :param name: name of attribute to get.
        :type name: string
        :param value: attribute value
        :type value: type is defined by the attribute name

        :Example: ::

            >>> b = Base(**{'category.test_attr':10})
            >>> b.set_attr_from_name('category.test_attr', '10')
            >>> print(b.category.test_attr)
            '10'
        """
        if '.'  in name:
            if name.count('.') == 1:
                attr_class, attr_name = name.split('.')
                setattr(getattr(self, attr_class), attr_name, value)
            elif name.count('.') == 2:
                attr_master, attr_class, attr_name = name.split('.')
                setattr(getattr(getattr(self, attr_master),
                                attr_class), attr_name, value)
        else:
            setattr(self, name, value)

    def add_base_attribute(self, name, value, value_dict):
        """
        Add an attribute to _attr_dict so it will be included in the
        output dictionary
        
        :param name: name of attribute
        :type name: string
        
        :param value: value of the new attribute
        :type value: described in value_dict
        
        :param value_dict: dictionary describing the attribute, must have keys
                           ['type', 'required', 'style', 'units']
        :type name: string
    
        * type --> the data type [ str | int | float | bool ]
        * required --> required in the standards [ True | False ]
        * style --> style of the string
        * units --> units of the attribute, must be a string
        
        :return: DESCRIPTION
        :rtype: TYPE
        
        :Example: ::
            
            >>> extra = {'type': str, 'style': 'name',
            >>> ...      'required': False, 'units': None}
            >>> r = Run()
            >>> r.add_base_attribute('weather', 'fair', extra)

        """
        name = self._validate_name(name)
        self._attr_dict.update({name: value_dict})
        self.set_attr_from_name(name, value)
        self.logger.debug('Added {0} to _attr_dict with {1}'.format(name,
                                                                    value_dict))
        self.logger.debug('set {0} to {1} as type {2}'.format(name, value,
                                                              value_dict['type']))

    def _validate_type(self, value, v_type, style=None):
        """
        validate type from standards
        """

        if value is None or v_type is None:
            return value

        type_dict = {'string': str,
                     'integer': int,
                     'float': float,
                     'boolean': bool}
        v_type = type_dict[validate_type(v_type)]
        

        if isinstance(value, v_type):
            return value

        else:
            msg = 'value={0} must be {1} not {2}'
            info = 'converting {0} to {1}'
            if isinstance(value, str):
                if v_type is int:
                    try:
                        self.logger.debug(info.format(type(value), v_type))
                        return int(value)
                    except ValueError as error:
                        self.logger.exception(error)
                        raise MTSchemaError(msg.format(value, v_type,
                                                       type(value)))
                elif v_type is float:
                    try:
                        self.logger.debug(info.format(type(value), v_type))
                        return float(value)
                    except ValueError as error:
                        self.logger.exception(error)
                        raise MTSchemaError(msg.format(value, 
                                                       v_type, type(value)))
                elif v_type is bool:
                    if value.lower() in ['false']:
                        self.logger.debug(info.format(value, False))
                        return False
                    elif value.lower() in ['true']:
                        self.logger.debug(info.format(value, True))
                        return True
                    else:
                        self.logger.exception(msg.format(value, 
                                                         v_type,
                                                         type(value)))
                        raise MTSchemaError(msg.format(value, 
                                                       v_type,
                                                       type(value)))
                elif v_type is str:
                    return value
            
            elif isinstance(value, int):
                if v_type is float:
                    self.logger.debug(info.format(type(value), v_type))
                    return float(value)
                elif v_type is str:
                    self.logger.debug(info.format(type(value), v_type))
                    return '{0:.0f}'.format(value)
            
            elif isinstance(value, float):
                if v_type is int:
                    self.logger.debug(info.format(type(value), v_type))
                    return int(value)
                elif v_type is str:
                    self.logger.debug(info.format(type(value), v_type))
                    return '{0}'.format(value)
            elif isinstance(value, list):
                return value
                
            else:
                self.logger.exception(msg.format(value, 
                                                 v_type,
                                                 type(value)))
                raise MTSchemaError(msg.format(value, 
                                               v_type, 
                                               type(value)))
                
    def to_dict(self):
        """
        make a dictionary from attributes, makes dictionary from _attr_list.
        """
        meta_dict = {}
        for name in list(self._attr_dict.keys()):
            try:
                meta_dict[name] = self.get_attr_from_name(name)
            except AttributeError as error:
                msg = ('{0}: setting {1} to None.  '.format(error, name) + 
                       'Try setting {0} to the desired value'.format(name))
                self.logger.info(msg)
                meta_dict[name] = None

        # sort the output dictionary for convience
        key = itemgetter(0)
        meta_dict = OrderedDict(sorted(meta_dict.items(), key=key))
        return meta_dict

    def from_dict(self, meta_dict):
        """
        fill attributes from a dictionary
        
        :param meta_dict: dictionary with keys equal to metadata.
        :type meta_dict: dictionary
        
        """
        if not isinstance(meta_dict, (dict, OrderedDict)):
            msg = "Input must be a dictionary not {0}".format(type(meta_dict))
            self.logger.error(msg)
            raise MTSchemaError(msg)
            
        for name, value in meta_dict.items():
            self.set_attr_from_name(name, value)
                
    def to_json(self, structured=False):
        """
        Write a json string from a given object, taking into account other
        class objects contained within the given object.
        """
        if not structured:
            return json.dumps(self.to_dict(), cls=NumpyEncoder)
        
        elif structured:
            meta_dict = self.to_dict()
            structured_dict = {}
            for key, value in meta_dict.items():
                if '.' in key:
                    category, names = key.split('.', 1)
                    n = names.count('.')
                    try:
                        category_dict = structured_dict[category]
                    except KeyError:
                        category_dict = {}
                    n = names.count('.')
                    if n == 0:
                        category_dict[names] = value
                        structured_dict[category] = category_dict
                    elif n == 1:
                        name, sub = names.split('.')
                        try:
                            name_dict = category_dict[name]
                        except KeyError:
                            name_dict = {}
                        name_dict[sub] = value
                        category_dict[name] = name_dict
                        structured_dict[category] = category_dict
                    else:
                        raise ValueError('Have not implemented 3 levels yet')
                else:
                    structured_dict[key] = value
            return json.dumps(structured_dict, cls=NumpyEncoder)

    def from_json(self, json_str):
        """
        read in a json string and update attributes of an object

        :param json_str: json string
        :type json_str: string

        """
        if not isinstance(json_str, str):
            msg = "Input must be valid JSON string not {0}".format(
                type(json_str))
            self.logger.error(msg)
            raise MTSchemaError(msg)
        read_dict = json.loads(json_str)
        meta_dict = {}
        for key, value in read_dict.items():
            if isinstance(value, dict):
                for key_01, value_01 in value.items():
                    if isinstance(value_01, dict):
                        for key_02, value_02 in value_01.items():
                            m_key = '.'.join([key, key_01, key_02])
                            meta_dict[m_key] = value_02
                    else:
                        m_key = '.'.join([key, key_01])
                        meta_dict[m_key] = value_01
            else:
                meta_dict[key] = value
        
        self.from_dict(meta_dict)

    def from_series(self, pd_series):
        """
        Fill attributes from a Pandas series
        
        :param pd_series: Series containing metadata information
        :type pd_series: pandas.Series
        
        ..todo:: Force types in series
        """
        assert isinstance(pd_series, pd.Series), "Input must be a Pandas.Series"
        for key, value in pd_series.iteritems():
            self.set_attr_from_name(key, value)
            
    def to_series(self):
        """
        Convert attribute list to a pandas.Series
        
        :return: pandas.Series
        :rtype: pandas.Series

        """
        
        return pd.Series(self.to_dict())


# ==============================================================================
# Location class, be sure to put locations in decimal degrees, and note datum
# ==============================================================================
class Declination(Base):
    """
    declination container
    """
    def __init__(self, **kwargs):

        self.value_d = None
        self.units_s = None
        self.epoch_s = None
        self.model_s = None
        super(Declination, self).__init__(**kwargs)

        self._attr_dict = ATTR_DICT['declination']

class Location(Base):
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

        self.datum_s = 'WGS84'
        self.declination = Declination()

        self._elevation = None
        self._latitude = None
        self._longitude = None

        super(Location, self).__init__(**kwargs)

        self._attr_dict = ATTR_DICT['location']

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
            self.logger.info('Could not convert {0} setting to None'.format(
                             latitude))
            return None

        except ValueError:
            self.logger.debug('Latitude is a string {0}'.format(latitude))
            lat_value = self._convert_position_str2float(latitude)

        if abs(lat_value) >= 90:
            msg = ('latitude value = {0} is unacceptable!'.format(lat_value) +
                   '.  Must be |Latitude| > 90')
            self.logger.error(msg)
            raise ValueError(msg)

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
            self.logger.info('Could not convert {0} setting to None'.format(
                             longitude))
            return None

        except ValueError:
            self.logger.debug('Longitude is a string {0}'.format(longitude))
            lon_value = self._convert_position_str2float(longitude)

        if abs(lon_value) >= 180:
            msg = ('longitude value = {0} is unacceptable!'.format(lon_value) +
                   '.  Must be |longitude| > 180')
            self.logger.error(msg)
            raise ValueError(msg)

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
            msg = 'Could not convert {0} to a number setting to 0'.format(
                    elevation)
            self.logger.info(msg)
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
        self.logger.debug('Converted {0} to {1}'.format(position,
                                                        position_str))

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
        
        self.logger.debug('Converted {0} to {1}'.format(position_str, 
                                                        position_value))

        return position_value

    def _assert_minutes(self, minutes):
        if not 0 <= minutes < 60.:
            msg = ('minutes should be 0 < > 60, currently {0:.0f}'.format(
                    minutes) + ' conversion will account for non-uniform' +
                    'timne. Be sure to check accuracy.')
            self.logger.warning(msg)

        return minutes

    def _assert_seconds(self, seconds):
        if not 0 <= seconds < 60.:
            msg = ('seconds should be 0 < > 60, currently {0:.0f}'.format(
                    seconds) + ' conversion will account for non-uniform' +
                    'timne. Be sure to check accuracy.')
            self.logger.warning(msg)
            
        return seconds

# ==============================================================================
# Instrument
# ==============================================================================
class Instrument(Base):
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

    More attributes can be added by inputing a name word dictionary

    >>> Instrument(**{'ports':'5', 'gps':'time_stamped'})
    """

    def __init__(self, **kwargs):

        self.id_s = None
        self.manufacturer_s = None
        self.type_s = None
        super(Instrument, self).__init__(**kwargs)

        self._attr_dict = ATTR_DICT['instrument']


# ==============================================================================
# Data Quality
# ==============================================================================
class DataQuality(Base):
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

    More attributes can be added by inputing a name word dictionary

    >>> DataQuality(**{'time_series_comments':'Periodic Noise'})
    """

    def __init__(self, **kwargs):

        self.rating_i = None
        self.warning_notes_s = None
        self.warning_flags_s = None
        self.author_s = None
        super(DataQuality, self).__init__(**kwargs)

        self._attr_dict = ATTR_DICT['data_quality']

# ==============================================================================
# Citation
# ==============================================================================
class Citation(Base):
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

    More attributes can be added by inputing a name word dictionary

    >>> Citation(**{'volume':56, 'pages':'234--214'})
    """

    def __init__(self, **kwargs):
        self.author_s = None
        self.title_s = None
        self.journal_s = None
        self.volume_s = None
        self.doi_s = None
        self.year_s = None
        super(Citation, self).__init__(**kwargs)

        self._attr_dict = ATTR_DICT['citation']

# ==============================================================================
# Copyright
# ==============================================================================
class Copyright(Base):
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

    More attributes can be added by inputing a name word dictionary

    >>> Copyright(**{'owner':'University of MT', 'contact':'Cagniard'})
    """

    def __init__(self, **kwargs):
        self.citation = Citation()
        self.conditions_of_use_s = ''.join(['All data and metadata for this survey are ',
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
        self.release_status_s = None
        self.additional_info_s = None
        super(Copyright, self).__init__(**kwargs)

        self._attr_dict = ATTR_DICT['copyright']

# ==============================================================================
# Provenance
# ==============================================================================
class Provenance(Base):
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

    More attributes can be added by inputing a name word dictionary

    >>> Provenance(**{'archive':'IRIS', 'reprocessed_by':'grad_student'})
    """

    def __init__(self, **kwargs):

        self._creation_dt = MTime()
        self.creating_application_s = 'MTH5'
        self.creator = Person()
        self.submitter = Person()
        self.software = Software()
        self.log_s = None
        super(Provenance, self).__init__(**kwargs)

        self._attr_dict = ATTR_DICT['provenance']

    @property
    def creation_time_s(self):
        return self._creation_dt.iso_str

    @creation_time_s.setter
    def creation_time_s(self, dt_str):
        self._creation_dt.dt_object = self._creation_dt.from_str(dt_str)

# ==============================================================================
# Person
# ==============================================================================
class Person(Base):
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

    More attributes can be added by inputing a name word dictionary

    >>> Person(**{'phone':'650-888-6666'})
    """

    def __init__(self, **kwargs):

        self.email_s = None
        self.author_s = None
        self.organization_s = None
        self.url_s = None
        super(Person, self).__init__(**kwargs)

        self._attr_dict = ATTR_DICT['person']

# =============================================================================
# diagnostic
# =============================================================================
class Diagnostic(Base):
    """
    diagnostic measurements like voltage, contact resistance, etc.
    """

    def __init__(self, **kwargs):
        self.units_s = None
        self.start_d = None
        self.end_d = None
        super(Diagnostic, self).__init__(**kwargs)

        self._attr_dict = ATTR_DICT['diagnostic']


# =============================================================================
# Battery
# =============================================================================
class Battery(Base):
    """
    Batter information
    """

    def __init__(self, **kwargs):

        self.type_s = None
        self.id_s = None
        self.voltage = Diagnostic()
        super(Battery, self).__init__(**kwargs)

        self._attr_dict = ATTR_DICT['battery']

# =============================================================================
# Electrode
# =============================================================================
class Electrode(Location, Instrument):
    """
    electrode container
    """

    def __init__(self, **kwargs):

        super(Electrode, self).__init__(**kwargs)

        self._attr_dict = ATTR_DICT['electrode']

# =============================================================================
# Timing System
# =============================================================================
class TimingSystem(Base):
    """
    Timing System
    """

    def __init__(self, **kwargs):

        self.type_s = None
        self.drift_d = None
        self.drift_units_d = None
        self.uncertainty_d = None
        self.uncertainty_units_d = None
        self.notes_s = None
        super(TimingSystem, self).__init__(**kwargs)

        self._attr_dict = ATTR_DICT['timing_system']

# ==============================================================================
# Software
# ==============================================================================
class Software(Base):
    """
    software
    """

    def __init__(self, **kwargs):
        self.name_s = None
        self.version_s = None
        self.author = Person()

        super(Software, self).__init__(**kwargs)

        self._attr_dict = ATTR_DICT['timing_system']

    @property
    def author_s(self):
        return self.author.author_s

    @author_s.setter
    def author_s(self, value):
        self.author.author_s = value

# =============================================================================
# filter
# =============================================================================
class Filter(Base):
    """
    container for filters
    
    .. note:: name_s and applied_b should be input as a list or comma 
              separated string.  applied can be a single true, false for all 
              or needs to be the same length as name
              
    """

    def __init__(self, **kwargs):
        self._name_s = None
        self._applied_b = None
        super().__init__()

        self._attr_dict = ATTR_DICT['filter']
        
    @property
    def name_s(self):
        return self._name_s
    
    @name_s.setter
    def name_s(self, names):
        if names is None:
            return
        
        if isinstance(names, str):
            self._name_s = [ss.strip().lower() for ss in names.split(',')]
        elif isinstance(names, list):
            self._name_s = [ss.strip().lower() for ss in names]
        else:
            msg = 'names must be a string or list of strings not {0}'
            self.logger.error(msg.format(names))
            raise MTSchemaError(msg.format(names))
            
        check = self._check_consistency()
        if not check:
            self.logger.info('Filter names and applied lists are not the ' +
                             'same size Be sure to check the inputs.' +
                             '. names = {0}, applied = {1}'.format(
                                 self._name_s, self._applied_b))
            
    @property
    def applied_b(self):
        return self._applied_b
    
    @applied_b.setter
    def applied_b(self, applied):
        if applied is None:
            return 
        
        if isinstance(applied, str):
            applied_list = [ss.strip().lower() for ss in applied.split(',')] 
        elif isinstance(applied, list):
            applied_list = applied
        elif isinstance(applied, bool):
            applied_list = [applied]
        else:
            msg = 'applied must be a string or list of strings not {0}'
            self.logger.error(msg.format(applied))
            raise MTSchemaError(msg.format(applied))       

        bool_list = []
        for app_bool in applied_list:
            if isinstance(app_bool, str):
                if app_bool.lower() in ['false']:
                    bool_list.append(False)
                elif app_bool.lower() in ['true']:
                    bool_list.append(True)
                else:
                    msg = 'Filter.applied must be [True | False], not {0}'
                    self.logger.error(msg.format(app_bool))
                    raise MTSchemaError(msg.format(app_bool))
            elif isinstance(app_bool, bool):
                bool_list.append(app_bool)
            else:
                msg = 'Filter.applied must be [True | False], not {0}'
                self.logger.error(msg.format(app_bool))
        self._applied_b = bool_list
        
        # check for consistency
        check = self._check_consistency()
        if not check:
            self.logger.info('Filter names and applied lists are not the ' +
                             'same size Be sure to check the inputs.' +
                             '. names = {0}, applied = {1}'.format(
                                 self._name_s, self._applied_b))
                        
    def _check_consistency(self):
        # check for consistency
        if self._name_s is not None:
            if self._applied_b is None:
                self.logger.warning('Need to input filter.applied')
                return False
            if len(self._name_s) == 1:
                if len(self._applied_b) == 1:
                    return True
            elif len(self._name_s) > 1:
                if len(self._applied_b) == 1:
                    self.logger.info('Assuming all filters have been ' +
                                     'applied as {0}'.format(self._applied_b[0]))
                    return True
                elif len(self._applied_b) > 1:
                    if len(self._applied_b) != len(self._name_s):
                        self.logger.waring('Applied and filter names ' +
                                           'should be the same length. '+
                                           'Appied={0}, names={1}'.format(
                                               len(self._applied_b), 
                                               len(self._name_s)))
                        return False
        else:
            return False


# ==============================================================================
# Site details
# ==============================================================================
class Survey(Base):
    """
    Information on the survey, including location, id, etc.


    """

    def __init__(self, **kwargs):

        self.acquired_by = Person()
        self._start_dt = MTime()
        self._end_dt = MTime()
        self.name_s = None
        self.id_s = None
        self.net_code_s = None
        self.northwest_corner = Location()
        self.southeast_corner = Location()
        self.datum_s = None
        self.location_s = None
        self.country_s = None
        self.summary_s = None
        self.acquired_by = Person()
        self.conditions_of_use_s = None
        self.release_status_s = None
        self.citation_dataset = Citation()
        self.citation_journal = Citation()
        super(Survey, self).__init__()

        self._attr_dict = ATTR_DICT['survey']

    @property
    def start_date_s(self):
        return self._start_dt.date

    @start_date_s.setter
    def start_date_s(self, start_date):
        self._start_dt.dt_object = self._start_dt.from_str(start_date)

    @property
    def end_date_s(self):
        return self._end_dt.date

    @end_date_s.setter
    def end_date_s(self, stop_date):
        self._end_dt.dt_object = self._end_dt.from_str(stop_date)

# =============================================================================
# Station Class
# =============================================================================
class Station(Location):
    """
    station object
    """
    def __init__(self, **kwargs):
        self.sta_code_s = None
        self.name_s = None
        self.datum_s = None
        self._start_dt = MTime()
        self._end_dt = MTime()
        self.num_channels_i = None
        self.channels_recorded_s = None
        self.data_type_s = None
        self.station_orientation_s = None
        self.orientation_method_s = None
        self.acquired_by = Person()
        self.provenance = Provenance()

        super(Station, self).__init__()

        self._attr_dict = ATTR_DICT['station']

    @property
    def start_s(self):
        return self._start_dt.iso_str

    @start_s.setter
    def start_s(self, start_date):
        self._start_dt.dt_object = self._start_dt.from_str(start_date)

    @property
    def end_s(self):
        return self._end_dt.iso_str

    @end_s.setter
    def end_s(self, stop_date):
        self._end_dt.dt_object = self._end_dt.from_str(stop_date)

# =============================================================================
# Run
# =============================================================================
class Run(Base):
    """
    container to hold run metadata
    
    .. note:: num_channels_i is derived from channels_recorded_s assuming that
              the channels are comma separated. e.g. 'EX, EY, HX'
    """

    def __init__(self, **kwargs):
        self.id_s = None
        self._start_dt = MTime()
        self._end_dt = MTime()
        self.sampling_rate_d = None
        self.channels_recorded_s = None
        self.data_type_s = None
        self.acquired_by = Person()
        self.provenance = Provenance()

        super(Run, self).__init__()

        self._attr_dict = ATTR_DICT['run']

    @property
    def start_s(self):
        return self._start_dt.iso_str

    @start_s.setter
    def start_s(self, start_date):
        self._start_dt.dt_object = self._start_dt.from_str(start_date)

    @property
    def end_s(self):
        return self._end_dt.iso_str

    @end_s.setter
    def end_s(self, stop_date):
        self._end_dt.dt_object = self._end_dt.from_str(stop_date)
        
    @property
    def num_channels_i(self):
        if self.channels_recorded_s is None:
            return None
        return len(self.channels_recorded_s.split(','))

# =============================================================================
# Data logger
# =============================================================================
class DataLogger(Instrument):
    """
    """
    def __init__(self, **kwargs):
        self.timing_system = TimingSystem()
        self.firmware = Software()
        self.power_source = Battery()
        super().__init__(**kwargs)
        
        self._attr_dict = ATTR_DICT['datalogger']
        
# =============================================================================
# Base Channel
# =============================================================================
class Channel(Location):
    """
    Base channel container
    """

    def __init__(self, **kwargs):
        self.type_s = None
        self.units_s = None
        self.channel_number_i = None
        self.component_s = None
        self.sample_rate_d = None
        self.azimuth_d = 0.0
        self.data_quality = DataQuality()
        self.filter = Filter()
        self._start_dt = MTime()
        self._end_dt = MTime()

        super(Channel, self).__init__(**kwargs)
        self._attr_dict = ATTR_DICT['channel']
        
    @property
    def start_s(self):
        return self._start_dt.iso_str

    @start_s.setter
    def start_s(self, start_date):
        self._start_dt.dt_object = self._start_dt.from_str(start_date)

    @property
    def end_s(self):
        return self._end_dt.iso_str

    @end_s.setter
    def end_s(self, stop_date):
        self._end_dt.dt_object = self._end_dt.from_str(stop_date)

# =============================================================================
# Electric Channel
# =============================================================================
class Electric(Channel):
    """
    electric channel
    """

    def __init__(self, **kwargs):
        self.dipole_length_d = 0.0
        self.positive = Electrode()
        self.negative = Electrode()
        self.contact_resistance_1 = Diagnostic()
        self.contact_resistance_2 = Diagnostic()
        self.ac = Diagnostic()
        self.dc = Diagnostic()
        self.units_s = None

        super(Electric, self).__init__(**kwargs)

        self._attr_dict = ATTR_DICT['electric']


# =============================================================================
# Magnetic Channel
# =============================================================================
class Magnetic(Channel):
    """

    """

    def __init__(self, **kwargs):
        self.sensor = Instrument()
        self.h_field_min = Diagnostic()
        self.h_field_max = Diagnostic()

        super().__init__(**kwargs)

        self._attr_dict = ATTR_DICT['magnetic']

# =============================================================================
# Helper function to be sure everything is encoded properly
# =============================================================================
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

        elif isinstance(obj, (np.ndarray)):
            return obj.tolist()

        return json.JSONEncoder.default(self, obj)

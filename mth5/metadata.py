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
    * csv?
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

from collections import OrderedDict
from operator import itemgetter

from mth5.standards.schema import (ATTR_DICT, validate_attribute,
                                   validate_type)
from mth5.utils.mttime import MTime
from mth5.utils.exceptions import MTSchemaError
from mth5.utils import helpers

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

        self.notes = None
        self._attr_dict = {}
        
        self._class_name = self.__class__.__name__
        
        self.logger = logging.getLogger('{0}.{1}'.format(__name__, 
                                                         self._class_name))

        for name, value in kwargs.items():
            self.set_attr_from_name(name, value)

    def __str__(self):
        lines = []
        for name, value in self.to_dict().items():
            lines.append('{0} = {1}'.format(name, value))
        return '\n'.join(lines)

    def __repr__(self):
        return self.to_json()
    
    def __eq__(self, other):
        if isinstance(other, (Base, dict, str, pd.Series)):
            home_dict = self.to_dict()
            if isinstance(other, Base):
                other_dict = other.to_dict()
            elif isinstance(other, dict):
                other_dict = other
            elif isinstance(other, str):
                other_dict = OrderedDict(sorted(json.loads(other).items(), 
                                                key=itemgetter(0)))
            elif isinstance(other, pd.Series):
                other_dict = OrderedDict(sorted(other.to_dict().items(), 
                                                key=itemgetter(0)))
            if other_dict == self.to_dict():
                return True
            else:
                for key, value in home_dict.items():
                    try:
                        other_value = other_dict[key]
                        if value != other_value:
                            msg = ('Key is the same but values are different' +
                                   '\n\thome[{0}] = {1} != '.format(key, value) + 
                                   'other[{0}] = {1}'.format(key, other_value))
                            self.logger.info(msg)
                    except KeyError:
                        msg = 'Cannot find {0} in other'.format(key)
                        self.logger.info(msg)
                        
                return False
        
            
            

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
        skip_list = ['latitude', 'longitude',  'elevation',
                     'start_date', 'end_date', 'start', 'end',
                     'name', 'applied', 'logger']
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
                try:
                    setattr(getattr(self, attr_class), attr_name, value)
                except AttributeError as error:
                    msg = ("must set {0} to a class in metadata first " +
                           "before setting {1}.")
                    self.logger.info(msg.format(attr_class, name))
                    self.logger.exception(error)
                    raise AttributeError(error)
            elif name.count('.') == 2:
                attr_master, attr_class, attr_name = name.split('.')
                try:
                    setattr(getattr(getattr(self, attr_master),
                                    attr_class), attr_name, value)
                except AttributeError as error:
                    msg = ("must set {0} to a class in metadata first " +
                           "before setting {1}.")
                    self.logger.info(msg.format(attr_class, name))
                    self.logger.exception(error)
                    raise AttributeError(error)
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

        if value in [None, 'None', 'none']:
            return None
        
        if v_type is None:
            msg = ('standards data type is unknown, if you want to ' +
                   'propogate this attribute using to_dict, to_json or ' +
                   'to_series, you need to add attribute description using ' +
                   'class function add_base_attribute.' +\
                   'Example: \n\t>>> Run.add_base_attribute(new, 10, ' +
                   '{"type":float, "required": True, "units": None, ' +
                   '"style": number})')
            self.logger.info(msg)
            return value
        
        if not isinstance(v_type, type) and isinstance(v_type, str):
            type_dict = {'string': str,
                         'integer': int,
                         'float': float,
                         'boolean': bool}
            v_type = type_dict[validate_type(v_type)]
        else:
            msg = 'v_type must be a string or type not {0}'.format(v_type)

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
                if v_type is str:
                    value = ['{0}'.format(v) for v in value]
                elif v_type is int:
                    value = [int(float(v)) for v in value]
                elif v_type is float:
                    value = [float(v) for v in value]
                elif v_type is bool:
                    value_list = []
                    for v in value:
                        if v in [True, 'true', 'True', 'TRUE']:
                            value_list.append(True)
                        elif v in [False, 'false', 'False', 'FALSE']:
                            value_list.append(False)
                    value = value_list
                return value
                
            else:
                self.logger.exception(msg.format(value, 
                                                 v_type,
                                                 type(value)))
                raise MTSchemaError(msg.format(value, 
                                               v_type, 
                                               type(value)))
        return None
                
    def to_dict(self, structured=False):
        """
        make a dictionary from attributes, makes dictionary from _attr_list.
        
        :param structured: make the returned dictionary nested
        :type structured: [ True | False ] , default is False
        
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

        if structured:
           meta_dict = helpers.structure_dict(meta_dict)

        meta_dict = {self._class_name.lower(): meta_dict}
        # sort the output dictionary for convience
        meta_dict = OrderedDict(sorted(meta_dict.items(), key=itemgetter(0)))
        
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
            
        class_name = list(meta_dict.keys())[0]
        if class_name.lower() != self._class_name.lower():
            msg = ('name of input dictionary is not the same as class type' +
                   'input = {0}, class type = {1}'.format(class_name, 
                                                          self._class_name))
        
        # be sure to flatten the dictionary first for easier transform
        meta_dict = helpers.flatten_dict(meta_dict[class_name])
        for name, value in meta_dict.items():
            self.set_attr_from_name(name, value)
                
    def to_json(self, structured=False, indent=' '*4):
        """
        Write a json string from a given object, taking into account other
        class objects contained within the given object.
        
        :param structured: make the returned json nested
        :type structured: [ True | False ] , default is False
        
        """

        return json.dumps(self.to_dict(structured=structured),
                          cls=NumpyEncoder,
                          indent=indent)

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
            
        self.from_dict(json.loads(json_str))

    def from_series(self, pd_series):
        """
        Fill attributes from a Pandas series
        
        .. note:: Currently, the series must be single layered with key names
                  separated by dots. (location.latitude)
        
        :param pd_series: Series containing metadata information
        :type pd_series: pandas.Series
        
        ..todo:: Force types in series
        
        """
        if not isinstance(pd_series, pd.Series):
            msg = ("Input must be a Pandas.Series not type {0}".format(
                    type(pd_series)))
            self.logger.error(msg)
            MTSchemaError(msg)
        for key, value in pd_series.iteritems():
            self.set_attr_from_name(key, value)
            
    def to_series(self):
        """
        Convert attribute list to a pandas.Series
        
        .. note:: this is a flattened version of the metadata
        
        :return: pandas.Series
        :rtype: pandas.Series

        """
        
        return pd.Series(self.to_dict()[self._class_name.lower()])
    
    def to_xml(self, string=False):
        """
        make an xml element for the attribute that will add types and 
        units.  
        
        :param string: output a string instead of an XML element
        :type string: [ True | False ], default is False
        
        :return: XML element or string

        """
        element = helpers.dict_to_xml(self.to_dict(structured=True),
                                      self._attr_dict)
        if not string:
            return element
        else:
            return helpers.element_to_string(element)
    
    def from_xml(self, xml_element):
        """
        
        :param xml_element: XML element
        :type xml_element: etree.Element
        
        :return: Fills attributes accordingly

        """
        
        self.from_dict(helpers.element_to_dict(xml_element))

# ============================================================================
# Location class, be sure to put locations in decimal degrees, and note datum
# ============================================================================
class Declination(Base):
    """
    Declination container
    
    =================== ========================================= ============
    Default Attributes  Description                               type
    =================== ========================================= ============
    value               value of declination in degrees           float
    units                 
    =================== ========================================= ============
    """
    def __init__(self, **kwargs):

        self.value = None
        self.epoch = None
        self.model = None
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

        self.datum = 'WGS84'
        self.declination = Declination()

        self._elevation = None
        self._latitude = None
        self._longitude = None

        super(Location, self).__init__(**kwargs)

        self._attr_dict = ATTR_DICT['location']

    @property
    def latitude(self):
        return self._latitude

    @latitude.setter
    def latitude(self, lat):
        self._latitude = self._assert_lat_value(lat)

    @property
    def longitude(self):
        return self._longitude

    @longitude.setter
    def longitude(self, lon):
        self._longitude = self._assert_lon_value(lon)

    @property
    def elevation(self):
        return self._elevation

    @elevation.setter
    def elevation(self, elev):
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
            msg = ('{0} not correct format, should be DD:MM:SS'.format(
                position_str))
            self.logger.error(msg)
            raise ValueError(msg)

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

        self.id = None
        self.manufacturer = None
        self.type = None
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

        self.rating = None
        self.warning_notes = None
        self.warning_flags = None
        self.author = None
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
        self.author = None
        self.title = None
        self.journal = None
        self.volume = None
        self.doi = None
        self.year = None
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
        self.conditions_of_use = ''.join(
            ['All data and metadata for this survey are ',
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
        self.creating_application = 'MTH5'
        self.creator = Person()
        self.submitter = Person()
        self.software = Software()
        self.log = None
        super(Provenance, self).__init__(**kwargs)

        self._attr_dict = ATTR_DICT['provenance']

    @property
    def creation_time(self):
        return self._creation_dt.iso_str

    @creation_time.setter
    def creation_time(self, dt_str):
        self._creation_dt.from_str(dt_str)

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

        self.email = None
        self.author = None
        self.organization = None
        self.url = None
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
        self.units = None
        self.start = None
        self.end = None
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

        self.type = None
        self.id = None
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

        self.type = None
        self.drift = None
        self.drift_units = None
        self.uncertainty = None
        self.uncertainty_units = None
        self.notes = None
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
        self.name = None
        self.version = None
        self._author = Person()

        super(Software, self).__init__(**kwargs)

        self._attr_dict = ATTR_DICT['software']

    @property
    def author(self):
        return self._author.author

    @author.setter
    def author(self, value):
        self._author.author= value

# =============================================================================
# filter
# =============================================================================
class Filter(Base):
    """
    container for filters
    
    .. note:: name_s and applied should be input as a list or comma 
              separated string.  applied can be a single true, false for all 
              or needs to be the same length as name
              
    """

    def __init__(self, **kwargs):
        self._name = None
        self._applied = None
        super().__init__()

        self._attr_dict = ATTR_DICT['filter']
        
    @property
    def name(self):
        return self._name
    
    @name.setter
    def name(self, names):
        if names is None:
            return
        
        if isinstance(names, str):
            self._name = [ss.strip().lower() for ss in names.split(',')]
        elif isinstance(names, list):
            self._name = [ss.strip().lower() for ss in names]
        else:
            msg = 'names must be a string or list of strings not {0}'
            self.logger.error(msg.format(names))
            raise MTSchemaError(msg.format(names))
            
        check = self._check_consistency()
        if not check:
            self.logger.info('Filter names and applied lists are not the ' +
                             'same size Be sure to check the inputs.' +
                             '. names = {0}, applied = {1}'.format(
                                 self._name, self._applied))
            
    @property
    def applied(self):
        return self._applied
    
    @applied.setter
    def applied(self, applied):
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
        self._applied = bool_list
        
        # check for consistency
        check = self._check_consistency()
        if not check:
            self.logger.info('Filter names and applied lists are not the ' +
                             'same size Be sure to check the inputs.' +
                             '. names = {0}, applied = {1}'.format(
                                 self._name, self._applied))
                        
    def _check_consistency(self):
        # check for consistency
        if self._name is not None:
            if self._applied is None:
                self.logger.warning('Need to input filter.applied')
                return False
            if len(self._name) == 1:
                if len(self._applied) == 1:
                    return True
            elif len(self._name) > 1:
                if len(self._applied) == 1:
                    self.logger.info('Assuming all filters have been ' +
                                     'applied as {0}'.format(self._applied[0]))
                    return True
                elif len(self._applied) > 1:
                    if len(self._applied) != len(self._name):
                        self.logger.waring('Applied and filter names ' +
                                           'should be the same length. '+
                                           'Appied={0}, names={1}'.format(
                                               len(self._applied), 
                                               len(self._name)))
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
        self.short_name = None
        self.long_name = None
        self.net_code = None
        self.northwest_corner = Location()
        self.southeast_corner = Location()
        self.datum = None
        self.location = None
        self.country = None
        self.summary = None
        self.acquired_by = Person()
        self.conditions_of_use = None
        self.release_status = None
        self.citation_dataset = Citation()
        self.citation_journal = Citation()
        super(Survey, self).__init__()

        self._attr_dict = ATTR_DICT['survey']

    @property
    def start_date(self):
        return self._start_dt.date

    @start_date.setter
    def start_date(self, start_date):
        self._start_dt.from_str(start_date)

    @property
    def end_date(self):
        return self._end_dt.date

    @end_date.setter
    def end_date(self, stop_date):
        self._end_dt.from_str(stop_date)

# =============================================================================
# Station Class
# =============================================================================
class Station(Base):
    """
    station object
    """
    def __init__(self, **kwargs):
        self.sta_code = None
        self.name = None
        self.datum = None
        self._start_dt = MTime()
        self._end_dt = MTime()
        self.num_channels = None
        self.channels_recorded = None
        self.data_type = None
        self.station_orientation = None
        self.orientation_method = None
        self.acquired_by = Person()
        self.provenance = Provenance()
        self.location = Location()

        super(Station, self).__init__()

        self._attr_dict = ATTR_DICT['station']

    @property
    def start(self):
        return self._start_dt.iso_str

    @start.setter
    def start(self, start_date):
        self._start_dt.from_str(start_date)

    @property
    def end(self):
        return self._end_dt.iso_str

    @end.setter
    def end(self, stop_date):
        self._end_dt.from_str(stop_date)

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
        self.id = None
        self._start_dt = MTime()
        self._end_dt = MTime()
        self.sampling_rate = None
        self.channels_recorded = None
        self._n_chan = None
        self.data_type = None
        self.acquired_by = Person()
        self.provenance = Provenance()

        super(Run, self).__init__()

        self._attr_dict = ATTR_DICT['run']

    @property
    def start(self):
        return self._start_dt.iso_str

    @start.setter
    def start(self, start_date):
        self._start_dt.from_str(start_date)

    @property
    def end(self):
        return self._end_dt.iso_str

    @end.setter
    def end(self, stop_date):
        self._end_dt.from_str(stop_date)
        
    @property
    def num_channels(self):
        if self.channels_recorded is None:
            return None
        else:
            return len(self.channels_recorded.split(','))

            

        

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
        self.type = None
        self.units = None
        self.channel_number = None
        self.component = None
        self.sample_rate = None
        self.azimuth = 0.0
        self.data_quality = DataQuality()
        self.filter = Filter()
        self._start_dt = MTime()
        self._end_dt = MTime()

        super(Channel, self).__init__(**kwargs)
        self._attr_dict = ATTR_DICT['channel']
        
    @property
    def start(self):
        return self._start_dt.iso_str

    @start.setter
    def start(self, start_date):
        self._start_dt.from_str(start_date)

    @property
    def end(self):
        return self._end_dt.iso_str

    @end.setter
    def end(self, stop_date):
        self._end_dt.from_str(stop_date)

# =============================================================================
# Electric Channel
# =============================================================================
class Electric(Channel):
    """
    electric channel
    """

    def __init__(self, **kwargs):
        self.dipole_length = 0.0
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

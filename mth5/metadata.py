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

from pathlib import Path
from collections import OrderedDict
from operator import itemgetter

from mth5.standards.schema import ATTR_DICT
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
        validate the name name to conform to the standards
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
        assert(isinstance(name, str)), "name must be a string"
        name = name.lower().replace('/', '.')
        if name[0] in [str(ii) for ii in range(10)]:
            raise MTSchemaError('name name must start with a character {a-z}')
        return name

    def __setattr__(self, name, value):
        """
        set attribute based on metadata standards

        """
        # skip these attribute because they are validated in the property 
        # setter.
        skip_list = ['latitude_d', 'longitude_d',  'elevation_d',
                     'start_date_s', 'end_date_s', 'start_s', 'end_s']
        if hasattr(self, '_attr_dict'):
            if name[0] != '_':
                if not name in skip_list: 
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
                msg = ('WARNING: {0} is not defined in the standards. '+\
                      ' Assuming type and style are correct')
                print(msg.format(name))
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


    def _validate_type(self, value, v_type, style=None):
        """
        validate type from standards
        """

        if value is None or v_type is None:
            return value
        # for some reason storing types in ATTR_DICT gets messed up
        # when read in, so a work around is to make a dictionary
        # locally.
        type_dict = {'float': float,
                     'string': str,
                     'integer': int,
                     'boolean': bool}
        v_type = type_dict[v_type]

        if isinstance(value, v_type):
            return value

        else:
            msg = ' must be {0} not {1}'
            if isinstance(value, str):
                if v_type is int:
                    try:
                        return int(value)
                    except ValueError:
                        raise MTSchemaError(msg.format(v_type, type(value)))
                elif v_type is float:
                    try:
                        return float(value)
                    except ValueError:
                        raise MTSchemaError(msg.format(v_type, type(value)))
                elif v_type is bool:
                    if value.lower() in ['false']:
                        return False
                    elif value.lower() in ['true']:
                        return True
                    else:
                        raise MTSchemaError(msg.format(v_type, type(value)))
                elif v_type is str:
                    return value
            elif isinstance(value, int):
                if v_type is float:
                    return float(value)
                elif v_type is str:
                    return '{0:.0f}'.format(value)
            elif isinstance(value, float):
                if v_type is int:
                    return int(value)
                elif v_type is str:
                    return '{0}'.format(value)
            else:
                raise MTSchemaError(msg.format(v_type, type(value)))
                
    def to_dict(self):
        """
        make a dictionary from attributes, makes dictionary from _attr_list.
        """
        meta_dict = {}
        for name in list(self._attr_dict.keys()):
            meta_dict[name] = self.get_attr_from_name(name)

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
        assert isinstance(meta_dict, (dict, OrderedDict)), "Input must be a dictionary" 
        for name, value in meta_dict.items():
            self.set_attr_from_name(name, value)
                
    def to_json(self):
        """
        Write a json string from a given object, taking into account other
        class objects contained within the given object.
        """

        return json.dumps(self.to_dict(), cls=NumpyEncoder)

    def from_json(self, json_str):
        """
        read in a json string and update attributes of an object

        :param json_str: json string
        :type json_str: string

        """
        assert isinstance(json_str, str), "Input must be valid JSON string"
        self.from_dict(json.loads(json_str))

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

        self._attr_dict = {}


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
    """

    def __init__(self, **kwargs):
        self.name_s = None
        self.applied_b = False
        super().__init__()

        self._attr_dict = ATTR_DICT['filter']

    def to_poles_zeros(self):
        pass

    def from_poles_zeros(self, pz_arr):
        pass

    def from_file(self, filename):
        pass

    def to_file(self, filename):
        pass


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
    """

    def __init__(self, **kwargs):
        self.id_s = None
        self._start_dt = MTime()
        self._end_dt = MTime()
        self.sampling_rate_d = None
        self.num_channels_i = None
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
class Channel(Base):
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

        super(Channel, self).__init__(**kwargs)
        self._attr_dict = ATTR_DICT['channel']

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
class Magnetic(Channel, Location):
    """

    """

    def __init__(self, **kwargs):
        self.sensor = Instrument()
        self.h_field_min = Diagnostic()
        self.h_field_max = Diagnostic()

        super().__init__()
        Location.__init__(self)

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

# -*- coding: utf-8 -*-
"""
=======================
schema
=======================

Convenience Classes and Functions to deal with the base metadata standards
described by the csv file.

The hope is that only the csv files will need to be changed as the standards
are modified.  The attribute dictionaries are stored in ATTR_DICT

Created on Wed Apr 29 11:11:31 2020

@author: jpeacock
"""
# =============================================================================
# Imports
# =============================================================================
import logging
import sys
import re

from pathlib import Path
from copy import deepcopy
from collections.abc import MutableMapping
from operator import itemgetter

from mth5.standards import CSV_FN_PATHS
from mth5.utils.exceptions import MTSchemaError

logger = logging.getLogger(__name__)
# =============================================================================
# Variables
# =============================================================================
ACCEPTED_STYLES = ['name', 'url', 'email', 'number', 'date',
                   'time', 'date_time', 'net_code', 'name_list']

REQUIRED_KEYS = ['attribute', 'type', 'required', 'units', 'style']

# =============================================================================
# Helper functions
# =============================================================================
def validate_header(header, attribute=False):
    """
    validate header to make sure it includes the required keys:
        * 'attribute'
        * 'type'
        * 'required'
        * 'style'
        * 'units'

    :param header: list of header names
    :type header: list

    :param attribute: include attribute in test or not
    :type attribute: [ True | False ]

    :return: validated header
    :rtype: list

    """
    if not isinstance(header, list):
        msg = 'input header must be a list, not {0}'.format(header)
        logger.error(msg)
        raise MTSchemaError(msg)

    if attribute:
        if sorted(header) != sorted(REQUIRED_KEYS):
            logger.error('CSV Header is not correct, must include {0}'.format(
                REQUIRED_KEYS))
            raise MTSchemaError('CSV header must inlcude {0}'.format(
                REQUIRED_KEYS))
    else:
        required_keys = [key for key in REQUIRED_KEYS if key != 'attribute']
        if sorted(header) != sorted(required_keys):
            logger.error('CSV Header is not correct, must include {0}'.format(
                required_keys))
            raise MTSchemaError('CSV header must inlcude {0}'.format(
                required_keys))
    return header


def validate_attribute(name):
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
    
    if not isinstance(name, str):
        msg = 'attribute name must be a string, not {0}'.format(type(name))
        logger.error(msg)
        raise MTSchemaError(msg)
        
    if '/' in name:
        name = name.replace('/', '.')
        logger.debug("replaced '/' with '.' --> {0}".format(name))
        
    if re.search('[A-Z].*?', name):
        logger.debug('found capital letters in attribute {0}'.format(name))
        logger.debug('Spliting by capital letters')
        name = '_'.join(re.findall('.[^A-Z]*', name))
        name = name.replace('._', '.')
        logger.debug('result {0}'.format(name))
        name = name.lower()
        logger.debug('converted to lower case. Result {0}'.format(name))

    if re.match('^[0-9]', name):
        msg = 'attribute name cannot start with a number, {0}'.format(name)
        logger.error(msg)
        raise MTSchemaError(msg)
        
    return name
        
def validate_required(value):
    """

    Validate required, must be True or False

    :param value: required value
    :type value: [ string | bool ]
    :return: validated required value
    :rtype: boolean

    """
    if isinstance(value, bool):
        return value

    if isinstance(value, str):
        if value.lower() in ['false']:
            return False
        elif value.lower() in ['true']:
            return True
        else:
            msg = ('Required value must be True or False, '+
                   'not {0}'.format(value)) 
            logger.error(msg)
            raise MTSchemaError(msg)
    else:
        msg = ('Required value must be True or False, '+
                   'not {0}'.format(value)) 
        logger.error(msg)
        raise MTSchemaError(msg)

def validate_type(value):
    """

    Validate required type. Must be:
        * str
        * float
        * int
        * bool

    :param value: required type
    :type value: [ type | string ]
    :return: validated type
    :rtype: string

    """
    if isinstance(value, type):
        value = '{0}'.format(value).replace('<class', '').replace('>', '')

    if isinstance(value, str):
        value = value.replace('<class', '').replace('>', '')
        if 'int' in value.lower():
            return 'integer'
        elif 'float' in value.lower():
            return 'float'
        elif 'str' in value.lower():
            return 'string'
        elif 'bool' in value.lower():
            return 'boolean'

        else:
            msg = ("'type' must be type [ int | float " +
                   "| str | bool ].  Not {0}".format(value))
            logger.error(msg)
            raise MTSchemaError(msg)
    else:
        msg = ("'type' must be type [ int | float " +
               "| str | bool ] or string.  Not {0}".format(value))
        logger.error(msg)
        raise MTSchemaError(msg)

def validate_units(value):
    """
    Validate units

    ..todo:: make a list of acceptable unit names

    :param value: unit value to be validated
    :type value: string

    :return: validated units
    :rtype: string

    """
    if value is None:
        return value
    if isinstance(value, str):
        if value.lower() in ['none', 'empty', '']:
            return None
        else:
            return value.lower()
    else:
        msg = ("'units' must be a string or None." +
               " Not {0}".format(value))
        logger.error(msg)
        raise MTSchemaError(msg)

def validate_style(value):
    """
    Validate string style

    ..todo:: make list of accepted style formats

    :param value: style to be validated
    :type value: string
    :return: validated style
    :rtype: string

    """
    # if None then return the generic name style
    if value is None:
        return 'name'
    
    if not isinstance(value, str):
        msg = "'value' must be a string. Not {0}".format(value)
        logger.error(msg)
        raise MTSchemaError(msg)
        
    if value.lower() not in ACCEPTED_STYLES:
        msg = ("style {0} unknown, must be {1}".format(
                value, ACCEPTED_STYLES) + '. Not {0}'.format(value))
        logger.error(msg)
        raise MTSchemaError(msg)

    return value.lower()

def validate_value_dict(value_dict):
    """
    Validate an input value dictionary

    Must be of the form:
        {'type': str, 'required': True, 'style': 'name', 'units': units}

    :param value_dict: DESCRIPTION
    :type value_dict: TYPE
    :return: DESCRIPTION
    :rtype: TYPE

    """
    if not isinstance(value_dict, dict):
        msg = ("Input must be a dictionary," +
               " not {0}".format(value_dict))
        logger.error(msg)
        raise MTSchemaError(msg)

    header = validate_header(list(value_dict.keys()))
    # loop over validating functions in this module
    for key in header:
        value_dict[key] = getattr(sys.modules[__name__],
                                  'validate_{0}'.format(key))(value_dict[key])

    return value_dict

def get_level_fn(level):
    """

    Get the filename that corresponds to level of metadata

    acceptable names are:
        * 'auxiliary'
        * 'battery'
        * 'channel'
        * 'citation'
        * 'copyright'
        * 'datalogger,
        * 'data_quality'
        * 'declination'
        * 'diagnostic'
        * 'electric'
        * 'electrode'
        * 'filter'
        * 'instrument'
        * 'location'
        * 'magnetic'
        * 'person'
        * 'provenance'
        * 'run'
        * 'software'
        * 'station'
        * 'survey'
        * 'timing_system'

    :param level: name of level
    :type level: string
    :return: full path to file name
    :rtype: pathlib.Path or None if not found

    :Example: ::

        >>> run_fn = get_level_fn('run')

    """

    for fn in CSV_FN_PATHS:
        if level in fn.stem:
            if not fn.exists():
                msg = '{0} does not exist for level={1}'.format(fn, level)
                logger.error(msg)
                raise MTSchemaError(msg)
            logger.debug('Found standards csv file {0} for level={1}'.format(fn,
                                                                             level))
            return fn
    logger.debug('Cound not find CSV file for {0}'.format(level))
    return None

def from_csv(csv_fn):
    """
    Read in CSV file as a dictionary

    :param csv_fn: csv file to read metadata standards from
    :type csv_fn: pathlib.Path or string

    :return: dictionary of the contents of the file
    :rtype: Dictionary

    :Example: ::

        >>> run_dict = from_csv(get_level_fn('run'))

    """
    if not isinstance(csv_fn, Path):
        csv_fn = Path(csv_fn)

    with open(csv_fn, 'r') as fid:
        logger.debug('reading {0}'.format(csv_fn))
        lines = fid.readlines()

    header = validate_header([ss.strip().lower() for ss in
                              lines[0].strip().split(',')],
                             attribute=True)
    attribute_dict = {}
    for line in lines[1:]:
        line_dict = dict([(key, ss.strip()) for key, ss in
                          zip(header, line.strip().split(','))])

        key_name = validate_attribute(line_dict['attribute'])
        line_dict.pop('attribute')

        attribute_dict[key_name] = validate_value_dict(line_dict)

    return BaseDict(**attribute_dict)

def to_csv(level_dict, csv_fn):
    """
    write dictionary to csv file
    
    :param level_dict: DESCRIPTION
    :type level_dict: TYPE
    :param csv_fn: DESCRIPTION
    :type csv_fn: TYPE
    :return: DESCRIPTION
    :rtype: TYPE

    """
    
    if not isinstance(csv_fn, Path):
        csv_fn = Path(csv_fn)
        
    # sort dictionary first
    lines = [','.join(REQUIRED_KEYS)]
    for key in sorted(list(level_dict.keys())):
        line = [key]
        for rkey in REQUIRED_KEYS[1:]:
            line.append('{0}'.format(level_dict[key][rkey]))
        lines.append(','.join(line))
    
    with csv_fn.open('w') as fid:
        fid.write('\n'.join(lines))
    logger.info('Wrote dictionary to {0}'.format(csv_fn))
    return csv_fn
    

# =============================================================================
# base dictionary
# =============================================================================
class BaseDict(MutableMapping):
    """
    BaseDict is a convenience class that can help the metadata dictionaries 
    act like classes so you can access variables by .name or [name]
    
    .. note:: If the attribute has a . in the name then you will not be able
              to access that attribute by class.name.name  You will get an 
              attribute error.  You need to access the attribute like a 
              dictionary class['name.name']
              
    You can add an attribute by:
        
        >>> b = BaseDict()
        >>> b.update({name: value_dict})
        
    Or you can add a whole dictionary:
        
        >>> b.add_dict(ATTR_DICT['run'])
        
    All attributes have a descriptive dictionary of the form:
        
        >>> {'type': data type, 'required': [True | False],
        >>> ... 'style': 'string style', 'units': attribute units}
    
        * **type** --> the data type [ str | int | float | bool ]
        * **required** --> required in the standards [ True | False ]
        * **style** --> style of the string
        * **units** --> units of the attribute, must be a string
    """
    
    def __init__(self, *args, **kwargs):
        self.update(dict(*args, **kwargs))
        
    def __setitem__(self, key, value):
        self.__dict__[key] = validate_value_dict(value)
        
    def __getitem__(self, key):         
        return self.__dict__[key]
    
    def __delitem__(self, key):
        del self.__dict__[key]
        
    def __iter__(self):
        return iter(self.__dict__)
    
    def __len__(self):
        return len(self.__dict__)
    
    # The final two methods aren't required, but nice for demo purposes:
    def __str__(self):
        """returns simple dict representation of the mapping"""
        s = list(sorted(self.__dict__.items(), key=itemgetter(0)))
        s = ['{0}: {1}'.format(k, v) for k, v in s]
        return '\n'.join(s)
    
    def __repr__(self):
        """echoes class, id, & reproducible representation in the REPL"""
        return '{}, BaseDict({})'.format(super(BaseDict, self).__repr__(), 
                                  self.__dict__)
    
    def add_dict(self, add_dict, name=None):
        """
        Add a dictionary to.  If name is input it is added to the keys of
        the input dictionary
        
        :param add_dict: dictionary to add
        :type add_dict: dictionary, or MutableMapping
        :param name: name to add to keys
        :type name: string or None
    
        :Example: :: 
            
            >>> s_obj = Standards()
            >>> run_dict = s_obj.run_dict
            >>> run_dict.add_dict(s_obj.declination_dict, 'declination')
            
        """
        assert isinstance(add_dict, (dict, MutableMapping))
        
        if name:
            add_dict = dict([('{0}.{1}'.format(name, key), value) for 
                             key, value in add_dict.items()])
        self.update(**add_dict)
            
    def copy(self):
        return deepcopy(self)
    
    
class Standards():
    """
    Helper container to read in csv files and make the appropriate
    dictionaries used in metadata.

    The thought is that only the csv files need to be changed if there is
    a change in standards.

    """

    def __init__(self):
        self.standards_dict = {}
        self.required_keys = REQUIRED_KEYS
        self.accepted_styles = ACCEPTED_STYLES

        self.logger = logger
        self.logger.debug('Initiating Standards')

    @property
    def declination_dict(self):
        return from_csv(get_level_fn('declination'))

    @property
    def instrument_dict(self):
        return from_csv(get_level_fn('instrument'))

    @property
    def data_quality_dict(self):
        return from_csv(get_level_fn('data_quality'))

    @property
    def citation_dict(self):
        return from_csv(get_level_fn('citation'))

    @property
    def copyright_dict(self):
        return from_csv(get_level_fn('copyright'))

    @property
    def person_dict(self):
        return from_csv(get_level_fn('person'))

    @property
    def software_dict(self):
        return from_csv(get_level_fn('software'))

    @property
    def diagnostic_dict(self):
        return from_csv(get_level_fn('diagnostic'))

    @property
    def battery_dict(self):
        return from_csv(get_level_fn('battery'))

    @property
    def timing_system_dict(self):
        return from_csv(get_level_fn('timing_system'))

    @property
    def filter_dict(self):
        return from_csv(get_level_fn('filter'))

    @property
    def location_dict(self):
        location_dict = from_csv(get_level_fn('location'))
        location_dict.add_dict(self.declination_dict.copy(), 'declination')
        
        return location_dict

    @property
    def provenance_dict(self):
        provenance_dict = from_csv(get_level_fn('provenance'))
        provenance_dict.add_dict(self.software_dict.copy(), 'software')
        provenance_dict.add_dict(self.person_dict.copy(), 'person')
        return provenance_dict


    @property
    def datalogger_dict(self):
        dl_dict = from_csv(get_level_fn('datalogger'))
        dl_dict.add_dict(self.instrument_dict.copy())
        dl_dict.add_dict(self.timing_system_dict.copy(),'timing_system')
        dl_dict.add_dict(self.software_dict.copy(), 'firmware')
        dl_dict.add_dict(self.battery_dict.copy(), 'power_source')
        return dl_dict

    @property
    def electrode_dict(self):
        elec_dict = from_csv(get_level_fn('electrode'))
        for key, v_dict in self.location_dict.items():
            if 'declination' not in key:
                elec_dict.update({key: v_dict})
        return elec_dict

    @property
    def survey_dict(self):
        survey_dict = from_csv(get_level_fn('survey'))
        survey_dict.add_dict(self.person_dict.copy(), 'acquired_by')
        return survey_dict

    @property
    def station_dict(self):
        station_dict = from_csv(get_level_fn('station'))
        station_dict.add_dict(self.location_dict.copy())
        for key, v_dict in self.person_dict.items():
            if key in ['author_s', 'email_s']:
                station_dict.update({'acquired_by.{0}'.format(key): v_dict})

        station_dict.add_dict(self.software_dict.copy(), 'provenance.software')
        station_dict.add_dict(self.person_dict.copy(), 'provenance.submitter')
        return station_dict

    @property
    def run_dict(self):
        return from_csv(get_level_fn('run'))

    @property
    def channel_dict(self):
        channel_dict = from_csv(get_level_fn('channel'))
        channel_dict.add_dict(self.data_quality_dict.copy(), 'data_quality')
        channel_dict.add_dict(self.filter_dict.copy(), 'filter')
        for key, v_dict in self.location_dict.items():
            if 'declination' not in key:
                channel_dict.update({key: v_dict})
        return channel_dict

    @property
    def auxiliary_dict(self):
        return self.channel_dict

    @property
    def electric_dict(self):
        electric_dict = from_csv(get_level_fn('electric'))
        electric_dict.add_dict(from_csv(get_level_fn('channel')))
        electric_dict.add_dict(self.data_quality_dict.copy(), 'data_quality')
        electric_dict.add_dict(self.filter_dict.copy(), 'filter')
        electric_dict.add_dict(self.electrode_dict.copy(), 'positive')
        electric_dict.add_dict(self.electrode_dict.copy(), 'negative')
        return electric_dict

    @property
    def magnetic_dict(self):
        magnetic_dict = from_csv(get_level_fn('magnetic'))
        magnetic_dict.add_dict(self.channel_dict.copy())
        magnetic_dict.add_dict(self.instrument_dict.copy(), 'sensor')
        return magnetic_dict
# =============================================================================
# Make ATTR_DICT
# =============================================================================
m_obj = Standards()

keys = [fn.stem for fn in CSV_FN_PATHS]
ATTR_DICT = dict([(key, deepcopy(getattr(m_obj, '{0}_dict'.format(key))))
                  for key in keys])
logger.debug("Successfully made ATTR_DICT")

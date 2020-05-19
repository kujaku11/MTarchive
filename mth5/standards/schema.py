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

from pathlib import Path
from copy import deepcopy

from mth5.standards import CSV_FN_PATHS
from mth5.utils.exceptions import MTSchemaError


logger = logging.getLogger(__name__)
# =============================================================================
# Variables
# =============================================================================
ACCEPTED_STYLES = ['name', 'url', 'email', 'number', 'date',
                   'time', 'date_time', 'net_code', 'name_list']

REQUIRED_KEYS = ['attribute', 'type', 'required', 'style', 'units']

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
    assert(isinstance(header, list)), 'header must be a list'

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
                REQUIRED_KEYS))
            raise MTSchemaError('CSV header must inlcude {0}'.format(
                REQUIRED_KEYS))
    logger.info('Validate header')
    return header


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
        logger.error('Required value must be True or False')
        raise MTSchemaError("'required' must be bool [ True | False ]")

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
            logging.error("'type' must be a [ int | float | str | bool ]"+\
                                " Not {0}".format(value))
            raise MTSchemaError("'type' must be a [ int | float | str | bool ]"+\
                                " Not {0}".format(value))

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
        logger.error("'units' must be a string or None")
        raise MTSchemaError("'units' must be a string or None")

def validate_style(value):
    """
    Validate string style

    ..todo:: make list of accepted style formats

    :param value: style to be validated
    :type value: string
    :return: validated style
    :rtype: string

    """

    assert isinstance(value, str), "'value' must be a string"
    if value.lower() not in ACCEPTED_STYLES:
        raise MTSchemaError("style {0} unknown, must be {1}".format(
            value, ACCEPTED_STYLES) + '. Not {0}'.format(value))

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
    assert isinstance(value_dict, dict), "Input must be a dictionary"

    header = validate_header(list(value_dict.keys()))
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
                logger.error('{0} does not exist'.format(fn))
                raise MTSchemaError("Can not find file {0}".format(fn))
            logger.info('Found standards csv file {0}'.format(fn))
            return fn
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
        logger.info('reading {0}'.format(csv_fn))
        lines = fid.readlines()

    header = validate_header([ss.strip().lower() for ss in
                              lines[0].strip().split(',')],
                             attribute=True)
    attribute_dict = {}
    for line in lines[1:]:
        line_dict = dict([(key, ss.strip()) for key, ss in
                          zip(header, line.strip().split(','))])

        key_name = line_dict['attribute']
        line_dict.pop('attribute')

        attribute_dict[key_name] = validate_value_dict(line_dict)

    return attribute_dict

def add_attr_dict(original_dict, new_dict, name):
    """
    Add an attribute dictionary from another container

    Must be of the form:
        * {attribute_name:{'type':data_type
                           'required': [True | False ],
                           'style': string_style,
                           'units': units of attribute_name]}

    :param original_dict: original dictionary to append to
    :type original_dict: dictionary

    :param new_dict: new dictionary to append
    :type new_dict: dictionary

    :param name: categorical name of new dictionary, name.key, if None
                 then no name is added.
    :type name: string
    :return: dictionary with appended key, values
    :rtype: dictionary

    :Example: ::

        >>> run_dict = from_csv(get_level_fn('run'))
        >>> extra = {'weather':{'type': str, 'style': 'name',
        >>> ...                 'required': False, 'units': None}}
        >>> run_dict = add_attr_dict(run_dict, extra, None)

    """

    for key, v_dict in new_dict.items():
        if name is not None:
            key = '{0}.{1}'.format(name, key)
        original_dict[key] = validate_value_dict(v_dict)

    return original_dict

def add_attr_to_dict(original_dict, key, value_dict):
    """
    Add an attribute to an existing attribute dictionary

    :param original_dict: original dictionary to append to
    :type original_dict: dictionary

    :param key: new dictionary to append
    :type key: string

    :param value_dict: dictionary describing the attribute, must have keys
                       ['type', 'required', 'style', 'units']
    :type name: string

    * type --> the data type [ str | int | float | bool ]
    * required --> required in the standards [ True | False ]
    * style --> style of the string
    * units --> units of the attribute, must be a string

    :return: dictionary with appended key, values
    :rtype: dictionary

    """

    original_dict[key] = validate_value_dict(value_dict)

    return original_dict


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
        self.logger.info('='*50)

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
        location_dict = add_attr_dict(location_dict,
                                      self.declination_dict,
                                      'declination')
        return location_dict

    @property
    def provenance_dict(self):
        provenance_dict = from_csv(get_level_fn('provenance'))
        provenance_dict = add_attr_dict(provenance_dict,
                                        self.software_dict,
                                        'software')
        provenance_dict = add_attr_dict(provenance_dict,
                                        self.person_dict,
                                        'person')
        return provenance_dict


    @property
    def datalogger_dict(self):
        dl_dict = from_csv(get_level_fn('datalogger'))
        dl_dict = add_attr_dict(dl_dict, self.instrument_dict, None)
        dl_dict = add_attr_dict(dl_dict, self.timing_system_dict,
                                'timing_system')
        dl_dict = add_attr_dict(dl_dict, self.software_dict, 'firmware')
        dl_dict = add_attr_dict(dl_dict, self.battery_dict,
                                'power_source')
        return dl_dict

    @property
    def electrode_dict(self):
        elec_dict = from_csv(get_level_fn('electrode'))
        for key, v_dict in self.location_dict.items():
            if 'declination' not in key:
                elec_dict = add_attr_to_dict(elec_dict, key, v_dict)
        return elec_dict

    @property
    def survey_dict(self):
        survey_dict = from_csv(get_level_fn('survey'))
        survey_dict = add_attr_dict(survey_dict, self.person_dict,
                                    'acquired_by')
        return survey_dict

    @property
    def station_dict(self):
        station_dict = from_csv(get_level_fn('station'))
        station_dict = add_attr_dict(station_dict, self.location_dict, None)
        for key, v_dict in self.person_dict.items():
            if key in ['author_s', 'email_s']:
                station_dict = add_attr_to_dict(station_dict,
                                                'acquired_by.{0}'.format(key),
                                                v_dict)

        station_dict = add_attr_dict(station_dict, self.software_dict,
                                     'provenance.software')
        station_dict = add_attr_dict(station_dict, self.person_dict,
                                     'provenance.submitter')
        return station_dict

    @property
    def run_dict(self):
        return from_csv(get_level_fn('run'))

    @property
    def channel_dict(self):
        channel_dict = from_csv(get_level_fn('channel'))
        channel_dict = add_attr_dict(channel_dict, self.data_quality_dict,
                                    'data_quality')
        channel_dict = add_attr_dict(channel_dict, self.filter_dict, 'filter')
        for key, v_dict in self.location_dict.items():
            if 'declination' not in key:
                channel_dict = add_attr_to_dict(channel_dict, key,
                                                v_dict)
        return channel_dict

    @property
    def auxiliary_dict(self):
        return self.channel_dict

    @property
    def electric_dict(self):
        electric_dict = from_csv(get_level_fn('electric'))
        electric_dict = add_attr_dict(electric_dict,
                                      from_csv(get_level_fn('channel')),
                                      None)
        electric_dict = add_attr_dict(electric_dict, self.data_quality_dict,
                                      'data_quality')
        electric_dict = add_attr_dict(electric_dict, self.filter_dict, 'filter')
        electric_dict = add_attr_dict(electric_dict, self.electrode_dict,
                                      'positive')
        electric_dict = add_attr_dict(electric_dict, self.electrode_dict,
                                      'negative')
        return electric_dict

    @property
    def magnetic_dict(self):
        magnetic_dict = from_csv(get_level_fn('magnetic'))
        magnetic_dict = add_attr_dict(magnetic_dict, self.channel_dict,
                                      None)
        magnetic_dict = add_attr_dict(magnetic_dict, self.instrument_dict,
                                      'sensor')
        return magnetic_dict
# =============================================================================
# Make ATTR_DICT
# =============================================================================
m_obj = Standards()

keys = [fn.stem for fn in CSV_FN_PATHS]
ATTR_DICT = dict([(key, deepcopy(getattr(m_obj, '{0}_dict'.format(key))))
                  for key in keys])

# -*- coding: utf-8 -*-
"""
Convenience Classes and Functions

Created on Wed Apr 29 11:11:31 2020

@author: jpeacock
"""
# =============================================================================
# Imports
# =============================================================================
import datetime

from dateutil import parser as dtparser
from pathlib import Path

from mth5.standards import CSV_LIST, CSV_PATH

# =============================================================================
# Error container
# =============================================================================
class MTSchemaError(Exception):
    pass

#==============================================================================
# convenience date-time container
#==============================================================================    
class MTime(object):
    """
    date and time container
    """
    
    def __init__(self):
        self.dt_object = self.from_str('1980-01-01 00:00:00')
           
    @property
    def iso_str(self):
        return self.dt_object.isoformat()
        
    @property
    def epoch_sec(self):
        return self.dt_object.timestamp()
    
    def from_str(self, dt_str):
        return self.validate_tzinfo(dtparser.parse(dt_str))
        
    def validate_tzinfo(self, dt_object):
        """
        make sure the timezone is UTC
        """
        
        if dt_object.tzinfo == datetime.timezone.utc:
            return dt_object
        
        elif dt_object.tzinfo is None:
            return dt_object.replace(tzinfo=datetime.timezone.utc)
        
        elif dt_object.tzinfo != datetime.timezone.utc:
            raise ValueError('Time zone must be UTC')
            
    @property
    def date(self):
        return self.dt_object.date().isoformat()
            
    @property
    def year(self):
        return self.dt_object.year
    
    @year.setter
    def year(self, value):
        self.dt_object = self.dt_object.replace(year=value)
        
    @property
    def month(self):
        return self.dt_object.month
    
    @month.setter
    def month(self, value):
        self.dt_object = self.dt_object.replace(month=value)
        
    @property
    def day(self):
        return self.dt_object.day
    
    @day.setter
    def day(self, value):
        self.dt_object = self.dt_object.replace(day=value)
        
    @property
    def hour(self):
        return self.dt_object.hour
    
    @hour.setter
    def hour(self, value):
        self.dt_object = self.dt_object.replace(hour=value)
        
    @property
    def minutes(self):
        return self.dt_object.minute
    
    @minutes.setter
    def minutes(self, value):
        self.dt_object = self.dt_object.replace(minute=value)
        
    @property
    def seconds(self):
        return self.dt_object.second
    
    @seconds.setter
    def seconds(self, value):
        self.dt_object = self.dt_object.replace(second=value)
        
    @property
    def microseconds(self):
        return self.dt_object.microsecond
    
    @microseconds.setter
    def microseconds(self, value):
        self.dt_object = self.dt_object.replace(microsecond=value)
        
    def now(self):
        """
        set date time to now
        
        :return: DESCRIPTION
        :rtype: TYPE

        """
        self.dt_object = self.validate_tzinfo(datetime.datetime.utcnow())
        
# =============================================================================
# Helper functions
# =============================================================================
class Standards(object):
    """
    """
    
    def __init__(self):
        self.standards_dict = {}
        self.required_keys = ['attribute', 'type', 'required', 'style',
                              'units']
        self.accepted_styles = ['name', 'url', 'email', 'number', 'date',
                                'time', 'date-time']
        
        
    def from_csv(self, csv_fn, name=None):
        """
        
        :param csv_fn: csv file to read metadata standards from
        :type csv_fn: TYPE
        :return: DESCRIPTION
        :rtype: TYPE
    
        """
        if not isinstance(csv_fn, Path):
            csv_fn = Path(csv_fn)

        if not name:
            name = csv_fn.name
            
        with open(csv_fn, 'r') as fid:
            lines = fid.readlines()
            
        header = self._validate_header([ss.strip().lower() for ss in 
                                        lines[0].strip().split(',')],
                                       attribute=True)
        attribute_dict = {}
        for line in lines[1:]:
            line_dict = dict([(key, ss.strip()) for key, ss in
                              zip(header, line.strip().split(','))])

            key_name = line_dict['attribute']
            line_dict.pop('attribute')

            attribute_dict[key_name] = self._validate_value_dict(line_dict)
        
        return attribute_dict
    
    def _validate_header(self, header, attribute=False):
        """
        
        :param header: DESCRIPTION
        :type header: TYPE
        :return: DESCRIPTION
        :rtype: TYPE

        """
        assert(isinstance(header, list)), 'header must be a list'
        if attribute:
            if sorted(header) != sorted(self.required_keys):
                raise MTSchemaError('CSV header must inlcude {0}'.format(
                                self.required_keys))
        else:
            required_keys = [key for key in self.required_keys 
                             if key != 'attribute']
            if sorted(header) != sorted(required_keys):
                raise MTSchemaError('CSV header must inlcude {0}'.format(
                                    self.required_keys))

        return header
    
    def _validate_required(self, value):
        """
        
        :param value: DESCRIPTION
        :type value: TYPE
        :return: DESCRIPTION
        :rtype: TYPE

        """
        if isinstance(value, bool):
            return value

        if isinstance(value, str):
            if value.lower() in ['false']:
                return False
            elif value.lower() in ['true']:
                return True
        else:
            raise MTSchemaError("'required' must be bool [ True | False ]")
            
    def _validate_type(self, value):
        """
        
        :param value: DESCRIPTION
        :type value: TYPE
        :return: DESCRIPTION
        :rtype: TYPE

        """
        
        if isinstance(value, str):
            if 'int' in value.lower():
                return int
            elif 'float' in value.lower():
                return float
            elif 'str' in value.lower():
                return str
            elif 'bool' in value.lower():
                return bool
        elif isinstance(value, (int, str, bool, float)):
            return value
        else:
            raise MTSchemaError("'type' must be a [ int | float | str | bool ]")
            
    def _validate_units(self, value):
        """
        """
        if value is None:
            return value
        if isinstance(value, str):
            if value.lower() in ['none', 'empty', '']:
                return None
        else:
            raise MTSchemaError("'units' must be a string or None")
            
    def _validate_style(self, value):
        """
        
        :param value: DESCRIPTION
        :type value: TYPE
        :return: DESCRIPTION
        :rtype: TYPE

        """
        
        assert isinstance(value, str), "'value' must be a string"
        if value.lower() not in self.accepted_styles:
            raise MTSchemaError("style {0} unknown, must be {1}".format(
                                value, self.accepted_styles))
            
        return value.lower()
    
    def _validate_value_dict(self, value_dict):
        """
        Validate an input value dictionary
        
        Must be of the form:
            {'type': str, 'required': True, 'style': 'name'}
            
        :param value_dict: DESCRIPTION
        :type value_dict: TYPE
        :return: DESCRIPTION
        :rtype: TYPE
    
        """
        assert isinstance(value_dict, dict), "Input must be a dictionary"
        
        header = self._validate_header(list(value_dict.keys()))
        for key in header:
            value_dict[key] = getattr(self, '_validate_{0}'.format(key))(value_dict[key])
        # value_dict['type'] = self._validate_type(value_dict['type'])
        # value_dict['required'] = self._validate_required(value_dict['required'])
        # value_dict['style'] = self._validate_style(value_dict['style'])
        return value_dict
            
    def add_attr_dict(self, original_dict, new_dict, name):
        """
        Add an attribute dictionary from another container
        
        :param original_dict: DESCRIPTION
        :type original_dict: TYPE
        :param new_dict: DESCRIPTION
        :type new_dict: TYPE
        :param name: DESCRIPTION
        :type name: TYPE
        :return: DESCRIPTION
        :rtype: TYPE
    
        """
        for key, v_dict in new_dict.items():
            if name is not None:
                key = '{0}.{1}'.format(name, key)
            original_dict[key] = v_dict
            
        return original_dict
    
    def add_attr_to_dict(self, original_dict, key, value_dict):
        """
        Add an attribute to an existing attribute dictionary
        
        :param original_dict: DESCRIPTION
        :type original_dict: TYPE
        :param key: DESCRIPTION
        :type key: TYPE
        :param value: DESCRIPTION
        :type value: TYPE
        :return: DESCRIPTION
        :rtype: TYPE
    
        """
        
        original_dict[key] = self.validate_value_dict(value_dict)
        
        return original_dict
    
    def _get_level_fn(self, level):
        """
        
        :param level: DESCRIPTION
        :type level: TYPE
        :return: DESCRIPTION
        :rtype: TYPE

        """
    
        for fn in CSV_LIST:
            if level in fn:
                return CSV_PATH.joinpath(Path(fn))
    
    @property
    def declination_dict(self):
        return self.from_csv(self._get_level_fn('declination'))
    
    @property
    def instrument_dict(self):
        return self.from_csv((self._get_level_fn('instrument')))

    @property
    def data_quailty_dict(self):
        return self.from_csv((self._get_level_fn('data_quality')))
        
    @property
    def citation_dict(self):
        return self.from_csv((self._get_level_fn('citation')))
    
    @property
    def copyright_dict(self):
        return self.from_csv((self._get_level_fn('copyright')))
    
    @property
    def person_dict(self):
        return self.from_csv((self._get_level_fn('person')))
    
    @property
    def software_dict(self):
        return self.from_csv((self._get_level_fn('software')))
    
    @property
    def diagnostic_dict(self):
        return self.from_csv((self._get_level_fn('diagnostic')))
    
    @property
    def battery_dict(self):
        return self.from_csv((self._get_level_fn('battery')))
    
    @property
    def timing_system_dict(self):
        return self.from_csv((self._get_level_fn('timing_system')))
    
    @property
    def filter_dict(self):
        return self.from_csv((self._get_level_fn('filter')))
    
    @property
    def location_dict(self):
        for key, v_dict in DECLINATION_ATTR.items():
#     key = '{0}.{1}'.format('declination', key)
#     LOCATION_ATTR[key] = v_dict
        return self.from_csv((self._get_level_fn('location')))
# # =============================================================================
# #     Attribute dictionaries
# # =============================================================================

# FILTER_ATTR = {'name_s': {'type': str,
#                            'required': True,
#                            'style': 'name'},
#                'applied_b': {'type': bool,
#                              'required': True,
#                              'style': 'name'},
#                'notes_s': {'type': str,
#                            'required': True,
#                            'style': 'name'}}
# # ----------------------------------------------------------------------
# LOCATION_ATTR = {'datum_s': {'type': str, 
#                              'required': True,
#                              'style': 'name'},
#                  'latitude_d': {'type': float,
#                                 'required': True,
#                                 'style': 'name'},
#                  'longitude_d': {'type': float,
#                                  'required': True,
#                                  'style': 'name'},
#                  'elevation_d': {'type': float,
#                                  'required': True,
#                                  'style': 'name'}}
# for key, v_dict in DECLINATION_ATTR.items():
#     key = '{0}.{1}'.format('declination', key)
#     LOCATION_ATTR[key] = v_dict

# # ----------------------------------------------------------------------
# PROVENANCE_ATTR = {'creation_time_s':{'type': str,
#                                       'required': True,
#                                       'style': 'name'},
#                    'notes_s':{'type': str, 'required': True,
#                               'style': 'name'},
#                    'log_s':{'type': str,
#                             'required': True,
#                             'style': 'name'}}
# PROVENANCE_ATTR = add_attr_dict(PROVENANCE_ATTR, SOFTWARE_ATTR, 'software')
# PROVENANCE_ATTR = add_attr_dict(PROVENANCE_ATTR, PERSON_ATTR, 'submitter')

# # ---------------------------------------------------------------------------
# DATALOGGER_ATTR = {"notes_s": {'type': str,
#                                'required': True,
#                                'style': 'name'},
#                    "n_channels_i": {'type': str,
#                                     'required': True,
#                                     'style': 'name'},
#                    "n_channels_used_s": {'type': str,
#                                          'required': True,
#                                          'style': 'name'}}  

# DATALOGGER_ATTR = add_attr_dict(DATALOGGER_ATTR, INSTRUMENT_ATTR,
#                                 None)
# DATALOGGER_ATTR = add_attr_dict(DATALOGGER_ATTR, TIMING_SYSTEM_ATTR,
#                                 'timing_system')
# DATALOGGER_ATTR = add_attr_dict(DATALOGGER_ATTR, SOFTWARE_ATTR,
#                                 'firmware')
# DATALOGGER_ATTR = add_attr_dict(DATALOGGER_ATTR, BATTERY_ATTR,
#                                 'power_source')
# # -----------------------------------------------------------------------------
# ELECTRODE_ATTR = {"notes_s": {'type': str, 
#                               'required': True,
#                               'style': 'name'}}

# ELECTRODE_ATTR = add_attr_dict(ELECTRODE_ATTR, INSTRUMENT_ATTR, None)
# for key, v_dict in LOCATION_ATTR.items():
#     if 'declination' not in key:
#         ELECTRODE_ATTR = add_attr_to_dict(ELECTRODE_ATTR, key, v_dict)
 
# # ----------------------------------------------------------------------
# SURVEY_ATTR = {'name_s': {'type': str, 
#                           'required': True,
#                           'style': 'name'},
#                'id_s': {'type': str, 
#                         'required': True, 
#                         'style': 'name'},
#                'net_code_s': {'type': str,
#                               'required': True, 
#                               'style': 'name'},
#                'start_date_s': {'type': str, 
#                                 'required': True,
#                                 'style': 'name'},
#                'end_date_s': {'type': str,
#                               'required': True,
#                               'style': 'name'},
#                'northwest_corner.latitude_d': {'type':float,
#                                                'required': True,
#                                                'style': 'name'},
#                'northwest_corner.longitude_d': {'type':float, 
#                                                 'required': True, 
#                                                 'style': 'name'},
#                'southeast_corner.latitude_d': {'type':float, 
#                                                'required': True, 
#                                                'style': 'name'},
#                'southeast_corner.longitude_d': {'type':float,
#                                             'required': True,
#                                             'style': 'name'},
#                'datum_s': {'type': str,
#                            'required': True,
#                            'style': 'name'},
#                'location_s': {'type': str,
#                               'required': True, 
#                               'style': 'name'},
#                'country_s': {'type': str, 
#                              'required': True,
#                              'style': 'name'},
#                'summary_s': {'type': str,
#                              'required': True,
#                              'style': 'name'},
#                'notes_s': {'type': str, 
#                            'required': True, 
#                            'style': 'name'},
#                'release_status_s': {'type': str,
#                                     'required': True, 
#                                     'style': 'name'},
#                'conditions_of_use_s': {'type': str,
#                                        'required': True, 
#                                        'style': 'name'},
#                'citation_dataset.doi_s': {'type': str,
#                                           'required': True,
#                                           'style': 'name'},
#                'citation_journal.doi_s': {'type': str, 
#                                           'required': True, 
#                                           'style': 'name'}}

# SURVEY_ATTR = add_attr_dict(SURVEY_ATTR, PERSON_ATTR, 'acquired_by')

# # ----------------------------------------------------------------------
# STATION_ATTR = {'sta_code_s': {'type': str, 
#                                'required': True, 
#                                'style': 'name'},
#                 'name_s':{'type': str, 
#                           'required': True,
#                           'style': 'name'},
#                 'start_s':{'type': str,
#                            'required': True,
#                            'style': 'name'},
#                 'end_s':{'type': str, 
#                          'required': True,
#                          'style': 'name'},
#                 'num_channels_i':{'type':int,
#                                   'required': True,
#                                   'style': 'name'},
#                 'channels_recorded_s':{'type': str, 
#                                        'required': True,
#                                        'style': 'name'},
#                 'data_type_s':{'type': str,
#                                'required': True, 
#                                'style': 'name'},
#                 'provenance.creation_time_s':{'type': str,
#                                               'required': True,
#                                               'style': 'name'},
#                 'provenance.notes_s':{'type': str, 'required': True,
#                                       'style': 'name'},
#                 'provenance.log_s':{'type': str, 'required': True,
#                                     'style': 'name'}}

# STATION_ATTR = add_attr_dict(STATION_ATTR, LOCATION_ATTR, None)
# STATION_ATTR = add_attr_dict(STATION_ATTR, PERSON_ATTR, 'acquired_by')
# STATION_ATTR = add_attr_dict(STATION_ATTR, SOFTWARE_ATTR,
#                              'provenance.software')
# STATION_ATTR = add_attr_dict(STATION_ATTR, PERSON_ATTR,
#                              'provenance.submitter')

# # ----------------------------------------------------------------------
# RUN_ATTR = {"id_s": {'type': str, 
#                      'required': True, 
#                      'style': 'name'},
#             "notes_s": {'type': str, 
#                         'required': True, 
#                         'style': 
#                             'name'},
#             "start_s": {'type': str,
#                         'required': True,
#                         'style': 'name'},
#             "end_s": {'type': str, 
#                       'required': True,
#                       'style': 'name'},
#             "sampling_rate_d": {'type': str,
#                                 'required': True,
#                                 'style': 'name'},
#             "num_channels_i": {'type': str, 
#                                'required': True,
#                                'style': 'name'},
#             "channels_recorded_s": {'type': str, 
#                                     'required': True,
#                                     'style': 'name'},
#             "data_type_s": {'type': str, 
#                             'required': True,
#                             'style': 'name'},
#             "acquired_by.author_s": {'type': str, 
#                                      'required': True, 
#                                      'style': 'name'},
#             "acquired_by.email_s": {'type': str, 
#                                     'required': True, 
#                                     'style': 'name'},
#             "provenance.notes_s": {'type': str, 
#                                    'required': True, 
#                                    'style': 'name'},
#             "provenance.log_s": {'type': str, 
#                                  'required': True,
#                                  'style': 'name'}}
    
# #-----------------------------------------------------------------------------
# CHANNEL_ATTR = {"type_s": {'type': str, 
#                            'required': True,
#                            'style': 'name'},
#                 "units_s": {'type': str, 
#                             'required': True,
#                             'style': 'name'},
#                 "channel_number_i": {'type': str, 
#                                      'required': True,
#                                      'style': 'name'},
#                 "component_s":{'type': str, 
#                                 'required': True,
#                                 'style': 'name'},
#                 "sample_rate_d": {'type': str, 
#                                   'required': True,
#                                   'style': 'name'},
#                 "azimuth_d": {'type': str, 
#                               'required': True,
#                               'style': 'name'},
#                 "notes_s": {'type': str, 
#                             'required': True,
#                             'style': 'name'}}
# CHANNEL_ATTR = add_attr_dict(CHANNEL_ATTR, DATA_QUALITY_ATTR, 'data_quality')
# CHANNEL_ATTR = add_attr_dict(CHANNEL_ATTR, FILTER_ATTR, 'filter')
    
# # ------------------------------------------------------------------
# AUXILIARY_ATTR = {}
# AUXILIARY_ATTR = add_attr_dict(AUXILIARY_ATTR, CHANNEL_ATTR, None)

# # ------------------------------------------------------------------
# ELECTRIC_ATTR = {"dipole_length_d": {'type': str, 
#                                      'required': True,
#                                      'style': 'name'}}
# ELECTRIC_ATTR = add_attr_dict(ELECTRIC_ATTR, CHANNEL_ATTR, None)
# ELECTRIC_ATTR = add_attr_dict(ELECTRIC_ATTR, DIAGNOSTIC_ATTR,
#                               'contact_resistance_A')
# ELECTRIC_ATTR = add_attr_dict(ELECTRIC_ATTR, DIAGNOSTIC_ATTR,
#                               'contact_resistance_B')
# ELECTRIC_ATTR = add_attr_dict(ELECTRIC_ATTR, DIAGNOSTIC_ATTR, 'ac')
# ELECTRIC_ATTR = add_attr_dict(ELECTRIC_ATTR, DIAGNOSTIC_ATTR, 'dc')
# ELECTRIC_ATTR = add_attr_dict(ELECTRIC_ATTR, ELECTRODE_ATTR, 'positive')
# ELECTRIC_ATTR = add_attr_dict(ELECTRIC_ATTR, ELECTRODE_ATTR, 'negative')

# #-----------------------------------------------------------------------------
# MAGNETIC_ATTR = {}

# MAGNETIC_ATTR = add_attr_dict(MAGNETIC_ATTR, CHANNEL_ATTR, None)
# MAGNETIC_ATTR = add_attr_dict(MAGNETIC_ATTR, INSTRUMENT_ATTR, 'sensor')
# for key, v_dict in LOCATION_ATTR.items():
#     if 'declination' not in key:
#         MAGNETIC_ATTR = add_attr_to_dict(MAGNETIC_ATTR, key, v_dict)
# MAGNETIC_ATTR = add_attr_dict(MAGNETIC_ATTR, DIAGNOSTIC_ATTR, 'h_field_min')
# MAGNETIC_ATTR = add_attr_dict(MAGNETIC_ATTR, DIAGNOSTIC_ATTR, 'h_field_max')

# # ------------------------------------------------------------------
# ATTR_DICT = {'location': LOCATION_ATTR,
#              'declination': DECLINATION_ATTR,
#              'instrument': INSTRUMENT_ATTR,
#              'data_quality': DATA_QUALITY_ATTR,
#              'citation': CITATION_ATTR,
#              'copyright': COPYRIGHT_ATTR,
#              'person': PERSON_ATTR,
#              'diagnostic': DIAGNOSTIC_ATTR,
#              'provenance': PROVENANCE_ATTR,
#              'battery': BATTERY_ATTR,
#              'electrode': ELECTRODE_ATTR,
#              'filter': FILTER_ATTR,
#              'software': SOFTWARE_ATTR,
#              'timing_system': TIMING_SYSTEM_ATTR, 
#              'survey': SURVEY_ATTR,
#              'station': STATION_ATTR,
#              'run': RUN_ATTR,
#              'datalogger': DATALOGGER_ATTR,
#              'electric': ELECTRIC_ATTR,
#              'auxiliary': AUXILIARY_ATTR,
#              'magnetic': MAGNETIC_ATTR}


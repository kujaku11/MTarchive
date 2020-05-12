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
def add_attr_dict(original_dict, new_dict, name):
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

def add_attr_to_dict(original_dict, key, value_dict):
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
    
    original_dict[key] = validate_value_dict(value_dict)
    
    return original_dict
    
def validate_value_dict(value_dict):
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
    
    default_keys = sorted(['type', 'required', 'style'])
    
    new_keys = sorted(list(value_dict.keys())) 
    
    if default_keys != new_keys:
        msg = ', '.join(default_keys)
        raise MTSchemaError("Dictionary must have keys: ({0})".format(msg))
    else:
        return value_dict
    
# =============================================================================
#     Attribute dictionaries
# =============================================================================
DECLINATION_ATTR = {'value_d': {'type': float,
                                'required': True, 
                                'style': '%.2f'},
                    'units_s': {'type': str, 
                                'required': True,
                                'style': 'name'},
                    'epoch_s': {'type': str, 
                                'required': True,
                                'style': 'name'},
                    'model_s': {'type': str,
                                'required': True,
                                'style': 'name'}}

# ----------------------------------------------------------------------
INSTRUMENT_ATTR = {'id_s': {'type': str,
                            'required': True,
                            'style': 'name'},
                   'manufacturer_s': {'type': str, 
                                      'required': True,
                                      'style': 'name'},
                   'type_s': {'type': str, 
                              'required': True, 
                              'style': 'name'}}

# ----------------------------------------------------------------------
DATA_QUALITY_ATTR = {'rating_i': {'type': str, 
                                 'required': True,
                                 'style': 'name'},
                    'warning_notes_s': {'type': float,
                                        'required': True, 
                                        'style': '%.2f'},
                    'warning_flag_s': {'type': str, 
                                       'required': True,
                                       'style': 'name'},
                    'author_s': {'type': str,
                                 'required': True,
                                 'style': 'name'}}

# ----------------------------------------------------------------------
CITATION_ATTR = {'doi_s': {'type': str,
                           'required': True,
                           'style': 'name'}}


COPYRIGHT_ATTR = {'release_status_s': {'type': str,
                                       'required': True,
                                       'style': 'name'}, 
                  'conditions_of_use_s': {'type': str,
                                           'required': True,
                                           'style': 'name'}}

PERSON_ATTR = {'author_s':{'type': str, 
                           'required': True,
                           'style': 'name'},
               'organization_s':{'type': str, 
                                 'required': True,
                                 'style': 'name'},
               'url_s':{'type': str, 
                        'required': True,
                        'style': 'name'},
               'email_s':{'type': str, 
                          'required': True,
                          'style': 'name'}}
SOFTWARE_ATTR = {'author_s':{'type': str, 
                           'required': True,
                           'style': 'name'},
                 'version_s':{'type': str, 
                              'required': True,
                              'style': 'name'},
                 'name_s':{'type': str, 
                           'required': True,
                           'style': 'name'}}

DIAGNOSTIC_ATTR = {'start_d': {'type': float,
                               'required': True,
                               'style': 'name'}, 
                   'end_d': {'type': float,
                             'required': True,
                             'style': 'name'}}

BATTERY_ATTR = {'type_s': {'type': str,
                           'required': True,
                           'style': 'name'},
                'id_s': {'type': str,
                         'required': True,
                         'style': 'name'},
                'start_voltage_d': {'type': float,
                                    'required': True,
                                    'style': 'name'}, 
                'end_voltage_d': {'type': float,
                                  'required': True,
                                  'style': 'name'}}

TIMING_SYSTEM_ATTR = {'type_s': {'type': str,
                                 'required': True,
                                 'style': 'name'},
                      'drift_d': {'type': float,
                                  'required': True,
                                  'style': 'name'},
                      'drift_units_s': {'type': float,
                                        'required': True,
                                        'style': 'name'},
                      'uncertainty_d': {'type': float,
                                        'required': True,
                                        'style': 'name'},
                      'undertainty_units_d': {'type': float,
                                              'required': True,
                                              'style': 'name'},
                      'notes_s': {'type': str,
                                  'required': True,
                                  'style': 'name'}}

FILTER_ATTR = {'names_s': {'type': str,
                           'required': True,
                           'style': 'name'},
               'applied_b': {'type': bool,
                             'required': True,
                             'style': 'name'},
               'notes_s': {'type': str,
                           'required': True,
                           'style': 'name'}}
# ----------------------------------------------------------------------
LOCATION_ATTR = {'datum_s': {'type': str, 
                             'required': True,
                             'style': 'name'},
                 'latitude_d': {'type': float,
                                'required': True,
                                'style': 'name'},
                 'longitude_d': {'type': float,
                                 'required': True,
                                 'style': 'name'},
                 'elevation_d': {'type': float,
                                 'required': True,
                                 'style': 'name'}}
for key, v_dict in DECLINATION_ATTR.items():
    key = '{0}.{1}'.format('declination', key)
    LOCATION_ATTR[key] = v_dict

# ----------------------------------------------------------------------
PROVENANCE_ATTR = {'creation_time_s':{'type': str,
                                      'required': True,
                                      'style': 'name'},
                   'software.name_s':{'type': str,
                                      'required': True,
                                      'style': 'name'},
                   'software.version_s':{'type': str,
                                         'required': True,
                                         'style': 'name'},
                   'software.author_s':{'type': str, 
                                        'required': True,
                                        'style': 'name'},
                   'submitter.author_s':{'type': str, 
                                         'required': True,
                                         'style': 'name'},
                   'submitter.organization_s':{'type': str, 
                                               'required': True,
                                               'style': 'name'},
                   'submitter.url_s':{'type': str, 
                                      'required': True,
                                      'style': 'name'},
                   'submitter.email_s':{'type': str, 
                                        'required': True,
                                        'style': 'name'},
                   'notes_s':{'type': str, 'required': True,
                              'style': 'name'},
                   'log_s':{'type': str,
                            'required': True,
                            'style': 'name'}}
PROVENANCE_ATTR = add_attr_dict(PROVENANCE_ATTR, SOFTWARE_ATTR, 'software')
PROVENANCE_ATTR = add_attr_dict(PROVENANCE_ATTR, PERSON_ATTR, 'submitter')

# ---------------------------------------------------------------------------
DATALOGGER_ATTR = {"manufacturer_s": {'type': str,
                                      'required': True,
                                      'style': 'name'},
                   "model_s": {'type': str,
                               'required': True,
                               'style': 'name'},
                   "serial_s": {'type': str,
                                'required': True,
                                'style': 'name'},
                   "notes_s": {'type': str,
                               'required': True,
                               'style': 'name'},
                   "n_channels_i": {'type': str,
                                    'required': True,
                                    'style': 'name'},
                   "n_channels_used_s": {'type': str,
                                         'required': True,
                                         'style': 'name'}}  
DATALOGGER_ATTR = add_attr_dict(DATALOGGER_ATTR, TIMING_SYSTEM_ATTR,
                                'timing_system')
DATALOGGER_ATTR = add_attr_dict(DATALOGGER_ATTR, SOFTWARE_ATTR,
                                'firmware')
DATALOGGER_ATTR = add_attr_dict(DATALOGGER_ATTR, BATTERY_ATTR,
                                'power_source')
# -----------------------------------------------------------------------------
ELECTRODE_ATTR = {"id_s": {'type': str, 
                           'required': True,
                           'style': 'name'},
                 "type_s": {'type': str, 
                            'required': True,
                            'style': 'name'},
                 "manufacturer_s": {'type': str, 
                                    'required': True,
                                    'style': 'name'},
                 "notes_s": {'type': str, 
                             'required': True,
                             'style': 'name'}}

for key, v_dict in LOCATION_ATTR.items():
    if 'declination' not in key:
        ELECTRODE_ATTR = add_attr_to_dict(ELECTRODE_ATTR, key, v_dict)
 
# ----------------------------------------------------------------------
SURVEY_ATTR = {'name_s': {'type': str, 
                          'required': True,
                          'style': 'name'},
               'id_s': {'type': str, 
                        'required': True, 
                        'style': 'name'},
               'net_code_s': {'type': str,
                              'required': True, 
                              'style': 'name'},
               'start_date_s': {'type': str, 
                                'required': True,
                                'style': 'name'},
               'end_date_s': {'type': str,
                              'required': True,
                              'style': 'name'},
               'northwest_corner.latitude_d': {'type':float,
                                               'required': True,
                                               'style': 'name'},
               'northwest_corner.longitude_d': {'type':float, 
                                                'required': True, 
                                                'style': 'name'},
               'southeast_corner.latitude_d': {'type':float, 
                                               'required': True, 
                                               'style': 'name'},
               'southeast_corner.longitude_d': {'type':float,
                                            'required': True,
                                            'style': 'name'},
               'datum_s': {'type': str,
                           'required': True,
                           'style': 'name'},
               'location_s': {'type': str,
                              'required': True, 
                              'style': 'name'},
               'country_s': {'type': str, 
                             'required': True,
                             'style': 'name'},
               'summary_s': {'type': str,
                             'required': True,
                             'style': 'name'},
               'notes_s': {'type': str, 
                           'required': True, 
                           'style': 'name'},
               'release_status_s': {'type': str,
                                    'required': True, 
                                    'style': 'name'},
               'conditions_of_use_s': {'type': str,
                                       'required': True, 
                                       'style': 'name'},
               'citation_dataset.doi_s': {'type': str,
                                          'required': True,
                                          'style': 'name'},
               'citation_journal.doi_s': {'type': str, 
                                          'required': True, 
                                          'style': 'name'}}

SURVEY_ATTR = add_attr_dict(SURVEY_ATTR, PERSON_ATTR, 'acquired_by')

# ----------------------------------------------------------------------
STATION_ATTR = {'sta_code_s': {'type': str, 
                               'required': True, 
                               'style': 'name'},
                'name_s':{'type': str, 
                          'required': True,
                          'style': 'name'},
                'start_s':{'type': str,
                           'required': True,
                           'style': 'name'},
                'end_s':{'type': str, 
                         'required': True,
                         'style': 'name'},
                'num_channels_i':{'type':int,
                                  'required': True,
                                  'style': 'name'},
                'channels_recorded_s':{'type': str, 
                                       'required': True,
                                       'style': 'name'},
                'data_type_s':{'type': str,
                               'required': True, 
                               'style': 'name'},
                'provenance.creation_time_s':{'type': str,
                                              'required': True,
                                              'style': 'name'},
                'provenance.notes_s':{'type': str, 'required': True,
                                      'style': 'name'},
                'provenance.log_s':{'type': str, 'required': True,
                                    'style': 'name'}}

STATION_ATTR = add_attr_dict(STATION_ATTR, LOCATION_ATTR, None)
STATION_ATTR = add_attr_dict(STATION_ATTR, PERSON_ATTR, 'acquired_by')
STATION_ATTR = add_attr_dict(STATION_ATTR, SOFTWARE_ATTR,
                             'provenance.software')
STATION_ATTR = add_attr_dict(STATION_ATTR, PERSON_ATTR,
                             'provenance.submitter')

# ----------------------------------------------------------------------
RUN_ATTR = {"id_s": {'type': str, 
                     'required': True, 
                     'style': 'name'},
            "notes_s": {'type': str, 
                        'required': True, 
                        'style': 
                            'name'},
            "start_s": {'type': str,
                        'required': True,
                        'style': 'name'},
            "end_s": {'type': str, 
                      'required': True,
                      'style': 'name'},
            "sampling_rate_d": {'type': str,
                                'required': True,
                                'style': 'name'},
            "num_channels_i": {'type': str, 
                               'required': True,
                               'style': 'name'},
            "channels_recorded_s": {'type': str, 
                                    'required': True,
                                    'style': 'name'},
            "data_type_s": {'type': str, 
                            'required': True,
                            'style': 'name'},
            "acquired_by.author_s": {'type': str, 
                                     'required': True, 
                                     'style': 'name'},
            "acquired_by.email_s": {'type': str, 
                                    'required': True, 
                                    'style': 'name'},
            "provenance.notes_s": {'type': str, 
                                   'required': True, 
                                   'style': 'name'},
            "provenance.log_s": {'type': str, 
                                 'required': True,
                                 'style': 'name'}}
    
# ------------------------------------------------------------------
AUXILIARY_ATTR = {"type_s": {'type': str, 
                             'required': True,
                             'style': 'name'},
                  "units_s": {'type': str, 
                              'required': True,
                              'style': 'name'},
                  "channel_number_i": {'type': str, 
                                       'required': True,
                                       'style': 'name'},
                  "sample_rate_d": {'type': str, 
                                    'required': True,
                                    'style': 'name'},
                  "notes_s": {'type': str, 
                              'required': True,
                              'style': 'name'}}
AUXILIARY_ATTR = add_attr_dict(AUXILIARY_ATTR, FILTER_ATTR, 'filter')

# ------------------------------------------------------------------
ELECTRIC_ATTR = {"dipole_length_d": {'type': str, 
                                     'required': True,
                                     'style': 'name'},
                 "channel_number_i": {'type': str, 
                                      'required': True,
                                      'style': 'name'},
                 "component_s": {'type': str, 
                                 'required': True,
                                 'style': 'name'},
                 "azimuth_d": {'type': str, 
                                     'required': True,
                                     'style': 'name'},
                 "units_s": {'type': str, 
                             'required': True,
                             'style': 'name'},
                 "sample_rate_d": {'type': str, 
                                   'required': True,
                                   'style': 'name'},
                 "notes_s": {'type': str, 
                             'required': True,
                             'style': 'name'}}

ELECTRIC_ATTR = add_attr_dict(ELECTRIC_ATTR, DIAGNOSTIC_ATTR,
                              'contact_resistance_A')
ELECTRIC_ATTR = add_attr_dict(ELECTRIC_ATTR, DIAGNOSTIC_ATTR,
                              'contact_resistance_B')
ELECTRIC_ATTR = add_attr_dict(ELECTRIC_ATTR, DIAGNOSTIC_ATTR, 'ac')
ELECTRIC_ATTR = add_attr_dict(ELECTRIC_ATTR, DIAGNOSTIC_ATTR, 'dc')
ELECTRIC_ATTR = add_attr_dict(ELECTRIC_ATTR, ELECTRODE_ATTR, 'positive')
ELECTRIC_ATTR = add_attr_dict(ELECTRIC_ATTR, ELECTRODE_ATTR, 'negative')
ELECTRIC_ATTR = add_attr_dict(ELECTRIC_ATTR, DATA_QUALITY_ATTR,
                              'data_quality')
ELECTRIC_ATTR = add_attr_dict(ELECTRIC_ATTR, FILTER_ATTR, 'filter')

#-----------------------------------------------------------------------------
MAGNETIC_ATTR = {"sensor.type_s": {'type': str,
                                   'required': True, 
                                   'style': 'name'},
                 "sensor.manufacturer_s":{'type': str,
                                          'required': True,
                                          'style': 'name'},
                 "sensor.notes_s":{'type': str,
                                   'required': True,
                                   'style': 'name'},
                 "sensor.id_s":{'type': str,
                                'required': True,
                                'style': 'name'},
                 "channel_number_i":{'type': str,
                                  'required': True,
                                  'style': 'name'},
                 "component_s":{'type': str, 
                                'required': True,
                                'style': 'name'},
                 "azimuth_d":{'type': str,
                              'required': True,
                              'style': 'name'},
                 "longitude_d":{'type': str, 
                                'required': True,
                                'style': 'name'},
                 "latitude_d":{'type': str, 
                               'required': True,
                               'style': 'name'},
                 "elevation_d":{'type': str, 
                                'required': True,
                                'style': 'name'},
                 "datum_s":{'type': str,
                            'required': True, 
                            'style': 'name'},
                 "units_s":{'type': str, 
                            'required': True, 
                            'style': 'name'},
                 "sample_rate_d":{'type': str, 
                                  'required': True,
                                  'style': 'name'},
                 "h_field.start_min_d":{'type': str, 
                                        'required': True,
                                        'style': 'name'},
                 "h_field.start_max_d":{'type': str, 
                                        'required': True, 
                                        'style': 'name'},
                 "h_field.end_min_d":{'type': str, 
                                      'required': True, 
                                      'style': 'name'},
                 "h_field.end_max_d":{'type': str,
                                      'required': True,
                                      'style': 'name'},
                 "h_field.units_s":{'type': str, 
                                    'required': True, 
                                    'style': 'name'},
                 "notes_s":{'type': str, 
                            'required': True, 
                            'style': 'name'},
                 "data_quality.rating_i":{'type': str, 
                                          'required': True,
                                          'style': 'name'},
                 "data_quality.warning_notes_s":{'type': str,
                                                 'required': True, 
                                                 'style': 'name'},
                 "data_quality.warning_flags_s":{'type': str, 
                                                 'required': True,
                                                 'style': 'name'},
                 "data_quality.author_s":{'type': str, 
                                          'required': True,
                                          'style': 'name'},
                 "filter.name_s":{'type': str, 
                                  'required': True, 
                                  'style': 'name'},
                 "filter.notes_s":{'type': str, 
                                   'required': True, 
                                   'style': 'name'},
                 "filter.applied_b":{'type': str, 
                                     'required': True,
                                     'style': 'name'}}

# ------------------------------------------------------------------
ATTR_DICT = {'location': LOCATION_ATTR,
             'declination': DECLINATION_ATTR,
             'instrument': INSTRUMENT_ATTR,
             'data_quality': DATA_QUALITY_ATTR,
             'citation': CITATION_ATTR,
             'copyright': COPYRIGHT_ATTR,
             'person': PERSON_ATTR,
             'diagnostic': DIAGNOSTIC_ATTR,
             'provenance': PROVENANCE_ATTR,
             'battery': BATTERY_ATTR,
             'electrode': ELECTRODE_ATTR,
             'survey': SURVEY_ATTR,
             'station': STATION_ATTR,
             'run': RUN_ATTR,
             'datalogger': DATALOGGER_ATTR,
             'electric': ELECTRIC_ATTR,
             'auxiliary': AUXILIARY_ATTR,
             'magnetic': MAGNETIC_ATTR}


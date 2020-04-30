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
#     Attribute dictionaries
# =============================================================================
LOCATION_ATTR = {'datum_s': {'type': str, 
                             'required': True},
                 'latitude_d': {'type': float,
                                'required': True},
                 'longitude_d': {'type': float,
                                 'required': True},
                 'elevation_d': {'type': float,
                                 'required': True},
                 'declination/value_d':{'type': float,
                                        'required': True,
                                        'style': 'name'},
                 'declination/units_s':{'type': str,
                                        'required': True, 
                                        'style': 'name'},
                 'declination/epoch_s':{'type': str, 
                                        'required': True,
                                        'style': 'name'},
                 'declination/model_s':{'type': str, 
                                        'required': True, 
                                        'style': 'name'}}

# ----------------------------------------------------------------------
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
DATAQUALITY_ATTR = {'rating_i': {'type': str, 
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

DIAGNOSTIC_ATTR = {'start_d': {'type': float,
                               'required': True,
                               'style': 'name'}, 
                  'end_d': {'type': float,
                            'required': True,
                            'style': 'name'}}

# ----------------------------------------------------------------------
PROVENANCE_ATTR = {'creation_time_s':{'type': str,
                                      'required': True,
                                      'style': 'name'},
                   'software/name_s':{'type': str,
                                      'required': True,
                                      'style': 'name'},
                   'software/version_s':{'type': str,
                                         'required': True,
                                         'style': 'name'},
                   'software/author_s':{'type': str, 
                                        'required': True,
                                        'style': 'name'},
                   'submitter/author_s':{'type': str, 
                                         'required': True,
                                         'style': 'name'},
                   'submitter/organization_s':{'type': str, 
                                               'required': True,
                                               'style': 'name'},
                   'submitter/url_s':{'type': str, 
                                      'required': True,
                                      'style': 'name'},
                   'submitter/email_s':{'type': str, 
                                        'required': True,
                                        'style': 'name'},
                   'notes_s':{'type': str, 'required': True,
                              'style': 'name'},
                   'log_s':{'type': str,
                            'required': True,
                            'style': 'name'}}

# ----------------------------------------------------------------------
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
                   "timing_system/type_s": {'type': str,
                                            'required': True,
                                            'style': 'name'},
                   "timing_system/drift_d": {'type': str,
                                             'required': True,
                                             'style': 'name'},
                   "timing_system/uncertainty_d": {'type': str,
                                                   'required': True,
                                                   'style': 'name'},
                   "timing_system/notes_s": {'type': str,
                                             'required': True,
                                             'style': 'name'},
                   "firmware/version_s": {'type': str,
                                          'required': True,
                                          'style': 'name'},
                   "firmware/date_s": {'type': str,
                                       'required': True,
                                       'style': 'name'},
                   "firmware/author_s": {'type': str,
                                         'required': True,
                                         'style': 'name'},
                   "n_channels_i": {'type': str,
                                    'required': True,
                                    'style': 'name'},
                   "n_channels_used_s": {'type': str,
                                         'required': True,
                                         'style': 'name'},
                   "power_source/type_s": {'type': str,
                                           'required': True,
                                           'style': 'name'},
                   "power_source/start_voltage_d": {'type': str,
                                                    'required': True,
                                                    'style': 'name'},
                   "power_source/end_voltage_d": {'type': str,
                                                  'required': True,
                                                  'style': 'name'},
                   "power_source/notes_s": {'type': str,
                                            'required': True,
                                            'style': 'name'}}   
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
               'northwest_corner/latitude_d': {'type':float,
                                               'required': True,
                                               'style': 'name'},
               'northwest_corner/longitude_d': {'type':float, 
                                                'required': True, 
                                                'style': 'name'},
               'southeast_corner/latitude_d': {'type':float, 
                                               'required': True, 
                                               'style': 'name'},
               'southeast_corner/longitude_d': {'type':float,
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
               'acquired_by/author_s': {'type': str,
                                        'required': True, 
                                        'style': 'name'},
               'acquired_by/organization_s': {'type': str, 
                                              'required': True, 
                                              'style': 'name'},
               'acquired_by/email_s': {'type': str, 
                                       'required': True,
                                       'style': 'name'},
               'acquired_by/url_s': {'type': str, 
                                     'required': True, 
                                     'style': 'name'},
               'release_status_s': {'type': str,
                                    'required': True, 
                                    'style': 'name'},
               'conditions_of_use_s': {'type': str,
                                       'required': True, 
                                       'style': 'name'},
               'citation_dataset/doi_s': {'type': str,
                                          'required': True,
                                          'style': 'name'},
               'citation_journal/doi_s': {'type': str, 
                                          'required': True, 
                                          'style': 'name'}}

# ----------------------------------------------------------------------
STATION_ATTR = {'sta_code_s': {'type': str, 
                               'required': True, 
                               'style': 'name'},
                'name_s':{'type': str, 
                          'required': True,
                          'style': 'name'},
                'latitude_d':{'type': str,
                              'required': True,
                              'style': 'name'},
                'longitude_d':{'type': float,
                               'required': True, 
                               'style': 'name'},
                'elevation_d':{'type': float,
                               'required': True, 
                               'style': 'name'},
                'notes_s':{'type': str,
                           'required': True,
                           'style': 'name'},
                'datum_s':{'type': str, 
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
                'declination/value_d':{'type': float,
                                       'required': True,
                                       'style': 'name'},
                'declination/units_s':{'type': str,
                                       'required': True,
                                       'style': 'name'},
                'declination/epoch_s':{'type': str, 
                                       'required': True, 
                                       'style': 'name'},
                'declination/model_s':{'type': str, 
                                       'required': True,
                                       'style': 'name'},
                'station_orientation_s':{'type': str,
                                         'required': True, 
                                         'style': 'name'},
                'orientation_method_s':{'type': str,
                                        'required': True,
                                        'style': 'name'},
                'acquired_by/author_s':{'type': str,
                                        'required': True,
                                        'style': 'name'},
                'acquired_by/email_s':{'type': str,
                                       'required': True,
                                       'style': 'name'},
                'provenance/creation_time_s':{'type': str,
                                              'required': True,
                                              'style': 'name'},
                'provenance/software/name_s':{'type': str,
                                              'required': True,
                                              'style': 'name'},
                'provenance/software/version_s':{'type': str,
                                                 'required': True,
                                                 'style': 'name'},
                'provenance/software/author_s':{'type': str, 
                                                'required': True,
                                                'style': 'name'},
                'provenance/submitter/author_s':{'type': str, 
                                                 'required': True,
                                                 'style': 'name'},
                'provenance/submitter/organization_s':{'type': str, 
                                                       'required': True,
                                                       'style': 'name'},
                'provenance/submitter/url_s':{'type': str, 
                                              'required': True,
                                              'style': 'name'},
                'provenance/submitter/email_s':{'type': str, 
                                                'required': True,
                                                'style': 'name'},
                'provenance/notes_s':{'type': str, 'required': True,
                                      'style': 'name'},
                'provenance/log_s':{'type': str, 'required': True,
                                    'style': 'name'}}

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
            "acquired_by/author_s": {'type': str, 
                                     'required': True, 
                                     'style': 'name'},
            "acquired_by/email_s": {'type': str, 
                                    'required': True, 
                                    'style': 'name'},
            "provenance/notes_s": {'type': str, 
                                   'required': True, 
                                   'style': 'name'},
            "provenance/log_s": {'type': str, 
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
                              'style': 'name'},
                  "filter/name_s": {'type': str, 
                                    'required': True,
                                    'style': 'name'},
                  "filter/notes_s": {'type': str, 
                                     'required': True,
                                     'style': 'name'},
                  "filter/applied_b": {'type': str, 
                                       'required': True,
                                       'style': 'name'}}

# ------------------------------------------------------------------
ELECTRIC_ATTR = {"dipole/length_d": {'type': str, 
                                     'required': True,
                                     'style': 'name'},
                 "channel_num_i": {'type': str, 
                                   'required': True,
                                   'style': 'name'},
                 "component_s": {'type': str, 
                                 'required': True,
                                 'style': 'name'},
                 "azimuth/value_d": {'type': str, 
                                     'required': True,
                                     'style': 'name'},
                 "positive/id_s": {'type': str, 
                                   'required': True,
                                   'style': 'name'},
                 "positive/latitude_d": {'type': str, 
                                         'required': True,
                                         'style': 'name'},
                 "positive/longitude_d": {'type': str, 
                                          'required': True,
                                          'style': 'name'},
                 "positive/elevation_d": {'type': str, 
                                          'required': True,
                                          'style': 'name'},
                 "positive/datum_s": {'type': str, 
                                      'required': True,
                                      'style': 'name'},
                 "positive/sensor_type_s": {'type': str, 
                                            'required': True,
                                            'style': 'name'},
                 "positive/sensor_manufacturer_s": {'type': str, 
                                                    'required': True,
                                                    'style': 'name'},
                 "positive/sensor_notes_s": {'type': str, 
                                             'required': True,
                                             'style': 'name'},
                 "negative/id_s": {'type': str, 
                                   'required': True,
                                   'style': 'name'},
                 "negative/latitude_d": {'type': str, 
                                         'required': True,
                                         'style': 'name'},
                 "negative/longitude_d": {'type': str, 
                                          'required': True,
                                          'style': 'name'},
                 "negative/elevation_d": {'type': str, 
                                          'required': True,
                                          'style': 'name'},
                 "negative/datum_s": {'type': str, 
                                      'required': True,
                                      'style': 'name'},
                 "negative/sensor_type_s": {'type': str, 
                                            'required': True,
                                            'style': 'name'},
                 "negative/sensor_manufacturer_s": {'type': str, 
                                                    'required': True,
                                                    'style': 'name'},
                 "negative/sensor_notes_s": {'type': str, 
                                             'required': True,
                                             'style': 'name'},
                 "contact_resistance/start_A_d": {'type': str, 
                                                  'required': True,
                                                  'style': 'name'},
                 "contact_resistance/start_B_d": {'type': str, 
                                                  'required': True,
                                                  'style': 'name'},
                 "contact_resistance/end_A_d": {'type': str, 
                                                'required': True,
                                                'style': 'name'},
                 "contact_resistance/end_B_d": {'type': str, 
                                                'required': True,
                                                'style': 'name'},
                 "ac/start_d": {'type': str, 
                                'required': True,
                                'style': 'name'},
                 "ac/end_d": {'type': str, 
                              'required': True,
                              'style': 'name'},
                 "dc/start_d": {'type': str, 
                                'required': True,
                                'style': 'name'},
                 "dc/end_d": {'type': str, 
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
                             'style': 'name'},
                 "data_quality/rating_d": {'type': str, 
                                           'required': True,
                                           'style': 'name'},
                 "data_quality/warning_comments_s": {'type': str, 
                                                     'required': True,
                                                     'style': 'name'},
                 "data_quality/warning_flags_s": {'type': str, 
                                                  'required': True,
                                                  'style': 'name'},
                 "data_quality/author_s": {'type': str, 
                                           'required': True,
                                           'style': 'name'},
                 "filter/name_s": {'type': str, 
                                   'required': True,
                                   'style': 'name'},
                 "filter/notes_s": {'type': str, 
                                    'required': True,
                                    'style': 'name'},
                 "filter/applied_b": {'type': str, 
                                      'required': True,
                                      'style': 'name'}}

# ------------------------------------------------------------------
ATTR_DICT = {'location': LOCATION_ATTR,
             'declination': DECLINATION_ATTR,
             'instrument': INSTRUMENT_ATTR,
             'data_quality': DATAQUALITY_ATTR,
             'citation': CITATION_ATTR,
             'copyright': COPYRIGHT_ATTR,
             'person': PERSON_ATTR,
             'diagnostic': DIAGNOSTIC_ATTR,
             'provenance': PROVENANCE_ATTR,
             'survey': SURVEY_ATTR,
             'station': STATION_ATTR,
             'run': RUN_ATTR,
             'datalogger': DATALOGGER_ATTR,
             'electric': ELECTRIC_ATTR,
             'auxiliary': AUXILIARY_ATTR}
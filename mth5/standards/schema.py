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

from pathlib import Path
from copy import deepcopy

from mth5.standards import CSV_FN_PATHS
from mth5.utils.exceptions import MTSchemaError
      
# =============================================================================
# Helper functions
# =============================================================================
class Standards(object):
    """
    Helper container to read in csv files and make the appropriate 
    dictionaries used in metadata.  
    
    The thought is that only the csv files need to be changed if there is 
    a change in standards.
    
    """
    
    def __init__(self):
        self.standards_dict = {}
        self.required_keys = ['attribute', 'type', 'required', 'style',
                              'units']
        self.accepted_styles = ['name', 'url', 'email', 'number', 'date',
                                'time', 'date_time', 'net_code', 'name_list']
        
        
        
    def _get_level_fn(self, level):
        """
        
        :param level: DESCRIPTION
        :type level: TYPE
        :return: DESCRIPTION
        :rtype: TYPE

        """
    
        for fn in CSV_FN_PATHS:
            if level in fn.stem:
                if not fn.exists():
                    raise MTSchemaError("Can not find file {0}".format(fn))
                return fn
    
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
        if isinstance(value, type):
            value = '{0}'.format(value)

        if isinstance(value, str):
            value = value.replace('<class', '').replace('>', '')
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
            raise MTSchemaError("'type' must be a [ int | float | str | bool ]"+\
                                " Not {0}".format(value))
            
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
                                value, self.accepted_styles) + 
                                '. Not {0}'.format(value))
            
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
            value_dict[key] = getattr(self,
                                      '_validate_{0}'.format(key))(value_dict[key])

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
        
        original_dict[key] = self._validate_value_dict(value_dict)
        
        return original_dict

    
    @property
    def declination_dict(self):
        return self.from_csv(self._get_level_fn('declination'))
    
    @property
    def instrument_dict(self):
        return self.from_csv(self._get_level_fn('instrument'))

    @property
    def data_quality_dict(self):
        return self.from_csv(self._get_level_fn('data_quality'))
        
    @property
    def citation_dict(self):
        return self.from_csv(self._get_level_fn('citation'))
    
    @property
    def copyright_dict(self):
        return self.from_csv(self._get_level_fn('copyright'))
    
    @property
    def person_dict(self):
        return self.from_csv(self._get_level_fn('person'))
    
    @property
    def software_dict(self):
        return self.from_csv(self._get_level_fn('software'))
    
    @property
    def diagnostic_dict(self):
        return self.from_csv(self._get_level_fn('diagnostic'))
    
    @property
    def battery_dict(self):
        return self.from_csv(self._get_level_fn('battery'))
    
    @property
    def timing_system_dict(self):
        return self.from_csv(self._get_level_fn('timing_system'))
    
    @property
    def filter_dict(self):
        return self.from_csv(self._get_level_fn('filter'))
    
    @property
    def location_dict(self):
        location_dict = self.from_csv(self._get_level_fn('location'))
        location_dict = self.add_attr_dict(location_dict, 
                                           self.declination_dict,
                                           'declination')
        return location_dict
    
    @property
    def provenance_dict(self):
        provenance_dict = self.from_csv(self._get_level_fn('provenance'))
        provenance_dict = self.add_attr_dict(provenance_dict, 
                                             self.software_dict, 
                                             'software')
        provenance_dict = self.add_attr_dict(provenance_dict, 
                                             self.person_dict, 
                                             'person')
        return provenance_dict
    
    
    @property
    def datalogger_dict(self):
        dl_dict = self.from_csv(self._get_level_fn('datalogger'))
        dl_dict = self.add_attr_dict(dl_dict, self.instrument_dict, None)
        dl_dict = self.add_attr_dict(dl_dict, self.timing_system_dict, 
                                     'timing_system')
        dl_dict = self.add_attr_dict(dl_dict, self.software_dict, 'firmware')
        dl_dict = self.add_attr_dict(dl_dict, self.battery_dict,
                                     'power_source')
        return dl_dict
    
    @property
    def electrode_dict(self):
        elec_dict = self.from_csv(self._get_level_fn('electrode'))
        for key, v_dict in self.location_dict.items():
            if 'declination' not in key:
                elec_dict = self.add_attr_to_dict(elec_dict, key, v_dict)
        return elec_dict
    
    @property
    def survey_dict(self):
        survey_dict = self.from_csv(self._get_level_fn('survey'))
        survey_dict = self.add_attr_dict(survey_dict, self.person_dict, 'acquired_by')
        return survey_dict
        
    @property
    def station_dict(self):
        station_dict = self.from_csv(self._get_level_fn('station'))
        station_dict = self.add_attr_dict(station_dict, self.location_dict, None)
        station_dict = self.add_attr_dict(station_dict, self.person_dict, 'acquired_by')
        station_dict = self.add_attr_dict(station_dict, self.software_dict, 
                                    'provenance.software')
        station_dict = self.add_attr_dict(station_dict, self.person_dict, 
                                    'provenance.submitter')
        return station_dict
    
    @property
    def run_dict(self):
        return self.from_csv(self._get_level_fn('run'))
    
    @property
    def channel_dict(self):
        channel_dict = self.from_csv(self._get_level_fn('channel'))
        channel_dict = self.add_attr_dict(channel_dict, self.data_quality_dict,
                                    'data_quality')
        channel_dict = self.add_attr_dict(channel_dict, self.filter_dict, 'filter')
        return channel_dict
    
    @property
    def auxiliary_dict(self):
        return self.channel_dict
    
    @property
    def electric_dict(self):
        electric_dict = self.from_csv(self._get_level_fn('electric'))
        electric_dict = self.add_attr_dict(electric_dict, self.channel_dict,
                                           None)
        electric_dict = self.add_attr_dict(electric_dict, self.electrode_dict,
                                           'positive')
        electric_dict = self.add_attr_dict(electric_dict, self.electrode_dict,
                                           'negative')
        return electric_dict
    
    @property
    def magnetic_dict(self):
        magnetic_dict = self.from_csv(self._get_level_fn('magnetic'))
        for key, v_dict in self.location_dict.items():
            if 'declination' not in key:
                magnetic_dict = self.add_attr_to_dict(magnetic_dict, key,
                                                      v_dict)
        magnetic_dict = self.add_attr_dict(magnetic_dict, self.instrument_dict,
                                           'sensor')
        return magnetic_dict
# =============================================================================
# Make ATTR_DICT
# =============================================================================
m_obj = Standards()

keys = [fn.stem for fn in CSV_FN_PATHS]
ATTR_DICT = dict([(key, deepcopy(getattr(m_obj, '{0}_dict'.format(key)))) 
                   for key in keys])


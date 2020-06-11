# -*- coding: utf-8 -*-
"""
This module provides tools to convert MT metadata to a StationXML file.

Created on Tue Jun  9 19:53:32 2020

@author: jpeacock
"""

# =============================================================================
# Imports
# =============================================================================
from obspy.core import inventory
from obspy.core.util import AttribDict

from mth5 import metadata
from copy import deepcopy
import logging

logger = logging.getLogger(__name__)
# =============================================================================
# Translate between metadata and inventory: mapping dictionaries 
# =============================================================================
base_translator = {'alternate_code': None,
                   'code': None,
                   'comments': None,
                   'data_availability': None,
                   'description': None,
                   'historical_code': None,
                   'identifiers': None,
                   'restricted_status': None,
                   'source_id': None}

network_translator = deepcopy(base_translator)
network_translator.update({'description': 'summary',
                           'comments': 'comments',
                           'start_date': 'time_period.start',
                           'end_date':'time_period.end',
                           'restricted_status': 'release_license',
                           'operators': 'special',
                           'code': 'archive_network'})

station_translator = deepcopy(base_translator)
station_translator.update({'alternate_code': None,
                           'channels': None,
                           'code': None,
                           'comments': 'provenance.comments',
                           'creation_date': 'time_period.start',
                           'data_availability': None,
                           'description': 'comments',
                           'elevation': 'location.elevation',
                           'end_date': 'time_period.end',
                           'equipments': None,
                           'external_references': None,
                           'geology': None,
                           'identifiers': None,
                           'latitude': 'location.latitude',
                           'longitude': 'location.longitude',
                           'operators': 'special',
                           'site': 'special',
                           'start_date': 'time_period.start',
                           'termination_date': 'time_period.end',
                           'vault': None,
                           'water_level': None})  

channel_translator = deepcopy(base_translator)
channel_translator.update({'azimuth': 'measurement_azimuth',
                           'calibration_units': 'units',
                           'calibration_units_description': None,
                           'clock_drift_in_seconds_per_sample': None,
                           'data_logger': 'run.special',
                           'description': None,
                           'dip': 'measurement_tilt',
                           'end_date': 'time_period.end',
                           'equipments': None,
                           'pre_amplifier': None,
                           'response': None,
                           'sample_rate': 'sample_rate',
                           'sample_rate_ratio_number_samples': None,
                           'sample_rate_ratio_number_seconds': None,
                           'sensor': 'special',
                           'start_date': 'time_period.start',
                           'types': 'special',
                           'water_level': None})

period_code_dict = {"F": {"min": 1000 , "max": 5000},
                    "G": {"min": 1000 , "max": 5000},
                    "D": {"min": 250 , "max": 1000},
                    "C": {"min": 250 , "max": 1000},
                    "E": {"min": 80 , "max": 250},
                    "S": {"min": 10 , "max": 80},
                    "H": {"min": 80 , "max": 250},
                    "B": {"min": 10 , "max": 80},
                    "M": {"min": 1 , "max": 10},
                    "L": {"min": .95, "max": 1.05},
                    "V": {"min": 0.095, "max": .105},
                    "U": {"min": 0.0095, "max": 0.0105},
                    "R": {"min": 0.0001 , "max": 0.001},
                    "P": {"min": 0.00001 , "max": 0.0001},
                    "T": {"min": 0.000001 , "max": 0.00001},
                    "Q": {"min": 0, "max": 0.000001}}

measurement_code_dict = {"tilt": "A",
                         "creep": "B",
                         "calibration": 'C',
                         "pressure": 'D',
                         'magnetics': 'F',
                         'gravity': 'G',
                         'humidity': 'I',
                         'temperature': 'K',
                         'water_current': 'O',
                         'electric': 'Q',
                         'rain_fall': 'R',
                         'linear_strain': 'S',
                         'tide': 'T', 
                         'wind': 'W'}

orientation_code_dict = {'N': {'min': 0, 'max': 5},
                         'E': {'min': 85, 'max': 90},
                         'Z': {'min': 0, 'max': 5},
                         '1': {'min': 5, 'max': 45},
                         '2': {'min': 45, 'max': 85},
                         '3': {'min': 5, 'max': 85}}

release_dict = {'CC 0': 'open',
                'CC BY': 'partial',
                'CC BY-SA': 'partial',
                'CC BY-ND': 'partial',
                'CC BY-NC-SA': 'partial',
                'CC BY-NC-NC': 'closed'}

def get_location_code(channel_obj):
    """
    Get the location code given the components and channel number
    
    :param channel_obj: Channel object
    :type channel_obj: :class:`~mth5.metadata.Channel`
    :return: 2 character location code
    :rtype: string

    """
    
    location_code = '{0}{1}'.format(channel_obj.component[0].upper(),
                                    channel_obj.channel_number % 10)
    
    return location_code


def get_period_code(sample_rate):
    """
    Get the SEED sampling rate code given a sample rate
    
    :param sample_rate: sample rate in samples per second
    :type sample_rate: float
    :return: single character SEED sampling code
    :rtype: string

    """
    period_code = 'A'
    for key, v_dict in sorted(period_code_dict.items()):
        if (sample_rate >= v_dict['min']) and \
            (sample_rate <= v_dict['max']):
            period_code = key
            break
    return period_code

def get_measurement_code(measurement):
    """
    get SEED sensor code given the measurement type
    
    :param measurement: measurement type, e.g.
        * temperature
        * electric
        * magnetic
    :type measurement: string
    :return: single character SEED sensor code, if the measurement type has
             not been defined yet Y is returned.
    :rtype: string

    """
    sensor_code = 'Y'
    for key, code in measurement_code_dict.items():
        if measurement.lower() in key:
            sensor_code = code
    return sensor_code

def get_orientation_code(azimuth, orientation='horizontal'):
    """
    Get orientation code given angle and orientation.  This is a general
    code and the true azimuth is stored in channel
    
    :param azimuth: angel assuming 0 is north, 90 is east, 0 is vertical down
    :type azimuth: float
    :return: single character SEED orientation code
    :rtype: string

    """
    orientation_code = '1'
    horizontal_keys = ['N', 'E', '1', '2']
    vertical_keys = ['Z', '3']
    
    azimuth = abs(azimuth) % 91
    if orientation == 'horizontal':
        test_keys = horizontal_keys
        
    elif orientation == 'vertical':
        test_keys = vertical_keys
        
    for key in test_keys:
        angle_min = orientation_code_dict[key]['min']
        angle_max = orientation_code_dict[key]['max']
        if (azimuth <= angle_max) and (azimuth >= angle_min):
            orientation_code = key
            break
    return orientation_code

def make_channel_code(channel_obj):
    """
    Make the 3 character SEED channel code
    
    :param channel_obj: Channel metadata
    :type channel_obj: :class:`~mth5.metadata.Channel`
    :return: 3 character channel code
    :type: string
    
    """

    period_code = get_period_code(channel_obj.sample_rate)
    sensor_code = get_measurement_code(channel_obj.type)
    if 'z' in channel_obj.component.lower():
        orientation_code = get_orientation_code(channel_obj.measurement_tilt,
                                                orientation='vertical')
    else:
        orientation_code = get_orientation_code(channel_obj.measurement_azimuth)        
     
    channel_code = '{0}{1}{2}'.format(period_code, sensor_code,
                                       orientation_code)
        
    return channel_code


def add_custom_element(obj, custom_name, custom_value, units=None, 
                       namespace='MT'):
    """
    Add a custom MT element to Obspy Inventory object
    
    :param obj: :class:`~obspy.core.inventory.Inventory` object that will 
                have the element added
    :type obj: :class:`~obspy.core.inventory.Inventory`
    
    :param custom_key: name of custom element, if the key has a '.' it will
                       be recursively split to assure proper nesting.
    :type custom_key: str
    
    :param custom_value: value of custom element
    :type custom_value: [ int | float | string ]
    
    :Example: ::
        
        >>> from obspy.core import inventory
        >>> from obspy.util import AttribDict()
        >>> channel_01 = inventory.Channel('SQE', "", 39.0, -112.0, 150, 0,
        ...                                azimuth=90,
        ...                                sample_rate=256, dip=0, 
        ...                                types=['ELECTRIC POTENTIAL'])
        >>> # add custom element
        >>> channel_01.extra = AttribDict({'namespace':'MT'})
        >>> channel_01.extra.FieldNotes = AttribDict({'namespace':'MT'})
        >>> channel_01.extra.FieldNotes.value = AttribDict({'namespace':'MT'})
        >>> channel_01.extra.FieldNotes = add_custom_element(
        >>>...                                    channel_01.extra.FieldNotes,
        >>>...                                    'ContactResistanceA',
        >>>...                                    1.2,
        >>>...                                    units='kOhm')

    """
    
    if custom_value is None:
        return
    
    if '.' in custom_name:
        custom_category, custom_name = custom_name.split('.', 1)
        if not hasattr(obj, custom_category):
            obj[custom_category] = AttribDict({'namespace': namespace,
                                               'value': AttribDict()})
        add_custom_element(obj[custom_category].value, 
                           custom_name, 
                           custom_value, 
                           units=units, 
                           namespace=namespace)
    else:
        obj[custom_name] = AttribDict({'namespace':namespace})
        obj[custom_name].value = custom_value
        if units:
            assert isinstance(units, str), 'Units must be a string'
            obj[custom_name].attrib = {'units': units.upper()}

# =============================================================================
# Translate between metadata and inventory: Survey --> Network
# ============================================================================= 
def mt_survey_to_inventory_network(survey_obj):
    """
    Translate MT survey metadata to inventory Network in StationXML
    
    Metadata that does not fit under StationXML schema is added as extra.
    
    :param survey_obj: MT survey metadata
    :type survey_obj: :class:`~mth5.metadata.Survey`
    :return: DESCRIPTION
    :rtype: TYPE

    """
    network_obj = inventory.Network(survey_obj.get_attr_from_name(
        network_translator['code']))
    
    used_list = ['northwest_corner.latitude', 'northwest_corner.longitude',
                 'southeast_corner.latitude', 'southeast_corner.longitude',
                 'time_period.start_date', 'time_period.end_date']
    for inv_key, mth5_key in network_translator.items():
        if mth5_key is None:
            msg = "cannot currently map mth5.survey to network.{0}".format(
                inv_key)
            logger.debug(msg)
            continue
        if inv_key == 'operators':
            operator = inventory.Operator(
                agency=[survey_obj.project_lead.organization])
            person = inventory.Person(names=[survey_obj.project_lead.author],
                                      emails=[survey_obj.project_lead.email])
            operator.contacts = [person]
            network_obj.operators = [operator]
            used_list.append('project_lead.author')
            used_list.append('project_lead.email')
            used_list.append('project_lead.organization')
            
        
        elif inv_key == 'comments':
            comment = inventory.Comment(survey_obj.comments, id=0)
            network_obj.comments.append(comment)
        elif inv_key == 'restricted_status':
            network_obj.restricted_status = \
                release_dict[survey_obj.release_license]
            
        else:
            setattr(network_obj, inv_key,
                    survey_obj.get_attr_from_name(mth5_key))
        used_list.append(mth5_key)
     
    # add any extra metadata that does not fit with StationXML schema
    network_obj.extra = AttribDict()
    network_obj.extra.MT = AttribDict({'namespace':'MT',
                                       'value':AttribDict()})
    
    for mt_key in survey_obj.get_attribute_list():
        if not mt_key in used_list:
            add_custom_element(network_obj.extra.MT.value, mt_key, 
                               survey_obj.get_attr_from_name(mt_key),
                               units=survey_obj._attr_dict[mt_key]['units'])

    return network_obj

# =============================================================================
# Translate between metadata and inventory: Station 
# =============================================================================      
def mt_station_to_inventory_station(station_obj):
    """
    Translate MT station metadata to inventory station
    
    Metadata that does not fit under StationXML schema is added as extra.
    
    :param station_obj: MT station metadata
    :type station_obj: :class:`~mth5.metadata.Station`

    :return: StationXML Station element
    :rtype: :class:`~obspy.core.inventory.Station`

    """
    inv_station = inventory.Station(station_obj.archive_id, 
                                    station_obj.location.latitude,
                                    station_obj.location.longitude,
                                    station_obj.location.elevation)
    
    used_list = ['channels_recorded', 'time_period.start', 'time_period.end',
                 'location.latitude', 'location.longitude', 
                 'location.elevation', 'archive_id']
    for inv_key, mth5_key in station_translator.items():
        if mth5_key is None:
            msg = "cannot currently map mth5.station to inventory.station.{0}".format(
                inv_key)
            logger.debug(msg)
            continue
        if inv_key == 'operators':
            operator = inventory.Operator(
                agency=[station_obj.acquired_by.organization])
            person = inventory.Person(names=[station_obj.acquired_by.author])
            operator.contacts = [person]
            inv_station.operators = [operator]
            used_list.append('acquired_by.author')
            used_list.append('acquired_by.organization')
        elif inv_key == 'site':
            inv_station.site.description = station_obj.geographic_name
            inv_station.site.name = station_obj.id
            used_list.append('geographic_name')
            used_list.append('id')
        elif inv_key == 'comments':
            comment = inventory.Comment(station_obj.comments, id=0)
            inv_station.comments.append(comment)
        else:
            setattr(inv_station, inv_key,
                    station_obj.get_attr_from_name(mth5_key))
            
    inv_station.extra = AttribDict()
    inv_station.extra.MT = AttribDict({'namespace':'MT',
                                       'value':AttribDict()})
    
    for mt_key in station_obj.get_attribute_list():
        if not mt_key in used_list:
            add_custom_element(inv_station.extra.MT.value, mt_key, 
                               station_obj.get_attr_from_name(mt_key),
                               units=station_obj._attr_dict[mt_key]['units'])
            
    return inv_station

# =============================================================================
# Translate between metadata and inventory: Channel
# =============================================================================
def mt_electric_to_inventory_channel(electric_obj, run_obj):
    """
    
    Translate MT electric channel metadata to inventory channel
    
    Metadata that does not fit under StationXML schema is added as extra.
    
    :param electric_obj: MT electric channel metadata
    :type electric_obj: :class:`~mth5.metadata.Electric`
    :param run_obj: MT run metadata to get data logger information
    :type run_obj: :class:`~mth5.metadata.Run`
    :return: StationXML channel
    :rtype: :class:`~obspy.core.inventory.Channel`

    """  
    location_code = get_location_code(electric_obj)
    channel_code = make_channel_code(electric_obj)

    inv_channel = inventory.Channel(channel_code, location_code,
                                    electric_obj.positive.latitude,
                                    electric_obj.positive.longitude,
                                    electric_obj.positive.elevation,
                                    electric_obj.positive.elevation)
    
    used_list = ['channels_recorded', 'time_period.start', 'time_period.end',
                 'sample_rate']
    for inv_key, mth5_key in channel_translator.items():
        if mth5_key is None:
            msg = "cannot currently map mth5.station to inventory.station.{0}".format(
                inv_key)
            logger.debug(msg)
            continue
        if inv_key == 'data_logger':
            dl = inventory.Equipment()
            dl.manufacturer = run_obj.data_logger.manufacturer
            dl.model = run_obj.data_logger.model
            dl.serial_number = run_obj.data_logger.id
            dl.type = run_obj.data_logger.type
            inv_channel.data_logger = dl
        elif inv_key == 'sensor':
            sensor = inventory.Equipment()
            sensor.manufacturer = electric_obj.positive.manufacturer
            sensor.type = electric_obj.positive.type
            sensor.model = electric_obj.positive.model
            inv_channel.sensor = sensor
        elif inv_key == 'comments':
            comment = inventory.Comment(electric_obj.comments, id=0)
            inv_channel.comments.append(comment)
        elif inv_key == 'types':
            inv_channel.types = ['GEOPHYSICAL']
        else:
            setattr(inv_channel, inv_key,
                    electric_obj.get_attr_from_name(mth5_key))
            
    inv_channel.extra = AttribDict()
    inv_channel.extra.MT = AttribDict({'namespace':'MT',
                                       'value':AttribDict()})
    
    for mt_key in electric_obj.get_attribute_list():
        if not mt_key in used_list:
            add_custom_element(inv_channel.extra.MT.value, mt_key, 
                               electric_obj.get_attr_from_name(mt_key),
                               units=electric_obj._attr_dict[mt_key]['units'])
            
    return inv_channel
            
     
def mt_channel_to_inventory_channel(channel_obj, run_obj): 
    """
    
    Translate MT channel metadata to inventory channel
    
    Metadata that does not fit under StationXML schema is added as extra.
    
    :param channel_obj: MT electric channel metadata
    :type channel_obj: :class:`~mth5.metadata.Channel`
    :param run_obj: MT run metadata to get data logger information
    :type run_obj: :class:`~mth5.metadata.Run`
    :return: StationXML channel
    :rtype: :class:`~obspy.core.inventory.Channel`

    """  
    location_code = get_location_code(channel_obj)
    channel_code = make_channel_code(channel_obj)

    inv_channel = inventory.Channel(channel_code, location_code,
                                    channel_obj.location.latitude,
                                    channel_obj.location.longitude,
                                    channel_obj.location.elevation,
                                    channel_obj.location.elevation)
    
    used_list = ['channels_recorded', 'time_period.start', 'time_period.end',
                 'sample_rate', 'location.latitude', 'location.longitude', 
                 'location.elevation', 'measurement_azimuth',
                 'measurement_tilt', 'units']
    for inv_key, mth5_key in channel_translator.items():
        if mth5_key is None:
            msg = "cannot currently map mth5.station to inventory.station.{0}".format(
                inv_key)
            logger.debug(msg)
            continue
        if inv_key == 'data_logger':
            dl = inventory.Equipment()
            dl.manufacturer = run_obj.data_logger.manufacturer
            dl.model = run_obj.data_logger.model
            dl.serial_number = run_obj.data_logger.id
            dl.type = run_obj.data_logger.type
            inv_channel.data_logger = dl
        elif inv_key == 'sensor':
            sensor = inventory.Equipment()
            sensor.manufacturer = channel_obj.sensor.manufacturer
            sensor.type = channel_obj.sensor.type
            sensor.model = channel_obj.sensor.model
            inv_channel.sensor = sensor
        elif inv_key == 'comments':
            comment = inventory.Comment(channel_obj.comments, id=0)
            inv_channel.comments.append(comment)
        elif inv_key == 'types':
            inv_channel.types = ['GEOPHYSICAL']
        else:
            setattr(inv_channel, inv_key,
                    channel_obj.get_attr_from_name(mth5_key))
            
    inv_channel.extra = AttribDict()
    inv_channel.extra.MT = AttribDict({'namespace':'MT',
                                       'value':AttribDict()})
    
    for mt_key in channel_obj.get_attribute_list():
        if not mt_key in used_list:
            add_custom_element(inv_channel.extra.MT.value, mt_key, 
                               channel_obj.get_attr_from_name(mt_key),
                               units=channel_obj._attr_dict[mt_key]['units'])
            
    return inv_channel

# =============================================================================
# 
# =============================================================================
class MTToStationXML():
    """
    Translate MT metadata to StationXML using Obspy Inventory classes.
    
    Any metadata that does not fit under the StationXML schema will be added
    as extra metadata in the namespace MT.
    
    MT metadata is mapped into StationXML as:
        
        Inventory 
        ===========
          |--> Network (MT Survey)
          -------------- 
            |--> Station (MT Station)
            -------------
              |--> Channel (MT Channel + MT Run)
              -------------
              
    :Example: ::
        
        >>> from mth5.utils import translator
        >>> from mth import metadata
        >>> mt2xml = translator.MTToStationXML()
        >>> mt_survey = metadata.Survey()
        >>> 
        
    
    
    """
    
    def __init__(self, inventory_object=None):
        
        self.logger = logging.getLogger('{0}.{1}'.format(__name__, 
                                                     self.__class__.__name__))
        if inventory_object is not None: 
            if not isinstance(inventory_object, inventory.Inventory):
                msg = 'Input must be obspy.Inventory object not type {0}'
                self.logger.error(msg.format(type(inventory_object)))
                raise TypeError(msg.format(type(inventory_object)))
            self.inventory_obj = inventory_object
                
        else:
            self.inventory_obj = inventory.Inventory(source='MT Metadata')
            
    def find_network_index(self, network):
        """
        locat the index where of network
        """
        
        for ii, net in enumerate(self.inventory_obj.networks):
            if network == net.code:
                return ii
        return None
    
    def find_station_index(self, station, network=None):
        """
        locate station
        
        :param station: DESCRIPTION
        :type station: TYPE
        :param network: DESCRIPTION, defaults to None
        :type network: TYPE, optional
        :return: DESCRIPTION
        :rtype: TYPE

        """
        
        if network is not None:
            network_index = self.find_network_index(network)
        else:
            network_index = 0

        for ii, sta in enumerate(
                self.inventory_obj.networks[network_index].stations):
            if station == sta.code:
                return ii
            
        return None
        
    def add_network(self, mt_survey_obj):
        """
        
        :param mt_survey_obj: DESCRIPTION
        :type mt_survey_obj: TYPE
        :return: DESCRIPTION
        :rtype: TYPE

        """
        network_obj = mt_survey_to_inventory_network(mt_survey_obj)
        
        if network_obj.code in self.inventory_obj.networks:
            msg = 'Network {0} is alread in current inventory'.format(
                network_obj.code)
            self.logger.error(msg)
            raise ValueError(msg)
        self.inventory_obj.networks.append(network_obj)
        
        self.logger.debug('Added network {0} to inventory'.format(
            mt_survey_obj.archive_network))
        
    def add_station(self, mt_station_obj, network_code=None):
        """
        
        :param mt_station_obj: DESCRIPTION
        :type mt_station_obj: TYPE
        :param network_code: DESCRIPTION
        :type network_code: TYPE
        :return: DESCRIPTION
        :rtype: TYPE

        """
        if network_code is None:
            network_code = self.inventory_obj.networks[0].code
            
        network_index = self.find_network_index(network_code)
            
        station_obj = mt_station_to_inventory_station(mt_station_obj)
        
        # locate the network in the list
        self.inventory_obj.networks[network_index].stations.append(station_obj)
        
        msg = 'Added station {0} to network {1}'.format(
            mt_station_obj.archive_id, network_code)
        self.logger.debug(msg)
        
    def add_channel(self, mt_channel, mt_run, station, network_code=None):
        """
        
        :param mt_channel: DESCRIPTION
        :type mt_channel: TYPE
        :param station: DESCRIPTION
        :type station: TYPE
        :param network_code: DESCRIPTION, defaults to None
        :type network_code: TYPE, optional
        :return: DESCRIPTION
        :rtype: TYPE

        """
        
        if network_code is None:
            network_code = self.inventory_obj.networks[0].code 
            
        network_index = self.find_network_index(network_code)
        station_index = self.find_station_index(station, network_code)
            
        if mt_channel.type in ['electric']:
            channel_obj = mt_electric_to_inventory_channel(mt_channel, 
                                                           mt_run)
        else:
            channel_obj = mt_channel_to_inventory_channel(mt_channel,
                                                          mt_run)
            
        self.inventory_obj.networks[network_index].stations[station_index].channels.append(channel_obj)
        
        self.logger.debug('Added channel {0} with code {1} to station {2} for netowrk {3}'.format(
            mt_channel.component, channel_obj.code, station, network_code))
            
            
    def to_stationxml(self, station_xml_fn):
        """
        
        :param station_xml_fn: DESCRIPTION
        :type station_xml_fn: TYPE
        :return: DESCRIPTION
        :rtype: TYPE

        """
        
        self.inventory_obj.write(station_xml_fn, format='stationxml',
                                 validate=True)
        self.logger.info('Wrote StationXML to {0}'.format(station_xml_fn))
        
        
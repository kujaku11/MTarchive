# -*- coding: utf-8 -*-
"""
Created on Tue Jun  9 19:53:32 2020

@author: jpeacock
"""

# =============================================================================
# Imports
# =============================================================================
from obspy.core import inventory
from mth5 import metadata
from copy import deepcopy
import logging

logger = logging.getLogger(__name__)
# =============================================================================
# Translate between metadata and inventory: Network
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
                           'end_date': 'time_period.start',
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
                           # 'depth': 'location.elevation',
                           'description': None,
                           'dip': 'measurement_tilt',
                           # 'elevation': 'location.elevation',
                           'end_date': 'time_period.end',
                           'equipments': None,
                           # 'latitude': 'location.latitude',
                           # 'longitude': 'location.longitude',
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
                    "Q": {"min": 0, "max": 0.000001},
                    "A": {"min": 0, "max": 100000},
                    "O": {"min": 0, "max": 100000}}

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

orientation_code_dict = {'x': 'N',
                         'y': 'E',
                         'z': 'Z',
                         '0-90': '1',
                         '90-180': '2'}

release_dict = {'CC 0': 'open',
                'CC BY': 'partial',
                'CC BY-SA': 'partial',
                'CC BY-ND': 'partial',
                'CC BY-NC-SA': 'partial',
                'CC BY-NC-NC': 'closed'}

def make_location_code(channel_obj):
    """
    
    :param channel_obj: DESCRIPTION
    :type channel_obj: TYPE
    :return: DESCRIPTION
    :rtype: TYPE

    """
    
    location_code = '{0}{1}'.format(channel_obj.component[0].upper(),
                                    channel_obj.channel_number % 10)
    
    return location_code

def make_channel_code(channel_obj):
    """
    """
    period_code = None
    sensor_code = None
    orientation_code = None
    
    for key, v_dict in period_code_dict.items():
        if (channel_obj.sample_rate >= v_dict['min']) and \
            (channel_obj.sample_rate <= v_dict['max']):
            period_code = key
            
    for key, code in measurement_code_dict.items():
        if channel_obj.type.lower() in key:
            sensor_code = code
    
    azimuth = channel_obj.measurement_azimuth % 180
    for key, code in orientation_code_dict.items():
        if key in channel_obj.component.lower():
            orientation_code = code.upper()
        if (azimuth > 5) and (azimuth < 85):
            orientation_code = '1'
        elif (azimuth > 95) and (azimuth < 175):
            orientation_code = '2'
        elif channel_obj.measurement_tilt > 5:
            orientation_code = '3'
            
    channel_code = '{0}{1}{2}'.format(period_code, sensor_code,
                                       orientation_code)
    if period_code is None or sensor_code is None or orientation_code is None:
        raise ValueError('Could not make channel code {0}'.format(
            channel_code))
        
    return channel_code

def mt_survey_to_inventory_network(survey_obj):
    """
    
    :param survey_obj: DESCRIPTION
    :type survey_obj: TYPE
    :return: DESCRIPTION
    :rtype: TYPE

    """
    network_obj = inventory.Network(survey_obj.get_attr_from_name(
        network_translator['code']))
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
        
        elif inv_key == 'comments':
            comment = inventory.Comment(survey_obj.comments, id=0)
            network_obj.comments.append(comment)
        elif inv_key == 'restricted_status':
            network_obj.restricted_status = \
                release_dict[survey_obj.release_license]
            
        else:
            setattr(network_obj, inv_key,
                    survey_obj.get_attr_from_name(mth5_key))
        
    return network_obj

# =============================================================================
# Translate between metadata and inventory: Station 
# =============================================================================      
def mt_station_to_inventory_station(station_obj):
    """
    
    :param station_obj: DESCRIPTION
    :type station_obj: TYPE
    :param code: DESCRIPTION
    :type code: TYPE
    :return: DESCRIPTION
    :rtype: TYPE

    """
    inv_station = inventory.Station(station_obj.archive_id, 
                                    station_obj.location.latitude,
                                    station_obj.location.longitude,
                                    station_obj.location.elevation)
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
        elif inv_key == 'site':
            inv_station.site.description = station_obj.geographic_name
            inv_station.site.name = station_obj.id
        elif inv_key == 'comments':
            comment = inventory.Comment(station_obj.comments, id=0)
            inv_station.comments.append(comment)
        else:
            setattr(inv_station, inv_key,
                    station_obj.get_attr_from_name(mth5_key))
            
    return inv_station

# =============================================================================
# Translate between metadata and inventory: Channel
# =============================================================================
def mt_electric_to_inventory_channel(electric_obj, run_obj): 
    """
    
    :param electric_obj: DESCRIPTION
    :type electric_obj: TYPE
    :param run_obj: DESCRIPTION
    :type run_obj: TYPE
    :param code: DESCRIPTION
    :type code: TYPE
    :param location_code: DESCRIPTION
    :type location_code: TYPE
    :return: DESCRIPTION
    :rtype: TYPE

    """  
    location_code = make_location_code(electric_obj)
    channel_code = make_channel_code(electric_obj)

    inv_channel = inventory.Channel(channel_code, location_code,
                                    electric_obj.positive.latitude,
                                    electric_obj.positive.longitude,
                                    electric_obj.positive.elevation,
                                    electric_obj.positive.elevation)
    
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
            
    return inv_channel
            
     
def mt_channel_to_inventory_channel(channel_obj, run_obj): 
    """
    
    :param electric_obj: DESCRIPTION
    :type electric_obj: TYPE
    :param run_obj: DESCRIPTION
    :type run_obj: TYPE
    :param code: DESCRIPTION
    :type code: TYPE
    :param location_code: DESCRIPTION
    :type location_code: TYPE
    :return: DESCRIPTION
    :rtype: TYPE

    """  
    location_code = make_location_code(channel_obj)
    channel_code = make_channel_code(channel_obj)

    inv_channel = inventory.Channel(channel_code, location_code,
                                    channel_obj.location.latitude,
                                    channel_obj.location.longitude,
                                    channel_obj.location.elevation,
                                    channel_obj.location.elevation)
    
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
            inv_channel.types = 'GEOPHYSICAL'
        else:
            setattr(inv_channel, inv_key,
                    channel_obj.get_attr_from_name(mth5_key))
            
    return inv_channel

# =============================================================================
# 
# =============================================================================
class MTToStationXML():
    """
    translate MT metadata to StationXML
    
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
        
        
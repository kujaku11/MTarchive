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
                   'comments': 'comments',
                   'data_availability': None,
                   'description': None,
                   'historical_code': None,
                   'identifiers': None,
                   'restricted_status': None,
                   'source_id': None}

network_translator = deepcopy(base_translator)
network_translator.update({'description': 'summary',
                           'comments': 'comments',
                           'start_date': 'time_period.start_date',
                           'end_date':'time_period.end_date',
                           'restricted_status': 'release_license',
                           'operators': 'special',
                           'code': 'archive_network'})

def mth5_survey_to_inventory_network(survey_obj):
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
            logger.info(msg)
            continue
        if inv_key == 'operators':
            operator = inventory.Operator(
                agency=[survey_obj.project_lead.organization])
            operator.contacts = [survey_obj.project_lead.author]
            network_obj.operators = [operator]
            
        else:
            setattr(network_obj, inv_key,
                    survey_obj.get_attr_from_name(mth5_key))
        
    return network_obj

# =============================================================================
# Translate between metadata and inventory: Station 
# =============================================================================
station_translator = deepcopy(base_translator)
station_translator.update({'alternate_code': None,
                           'channels': 'channels_recorded',
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

def mth5_station_to_inventory_station(station_obj, code):
    """
    
    :param station_obj: DESCRIPTION
    :type station_obj: TYPE
    :param code: DESCRIPTION
    :type code: TYPE
    :return: DESCRIPTION
    :rtype: TYPE

    """
    inv_station = inventory.Station(code, 
                                    station_obj.location.latitude,
                                    station_obj.location.longitude,
                                    station_obj.location.elevation)
    for inv_key, mth5_key in station_translator.items():
        if mth5_key is None:
            msg = "cannot currently map mth5.station to inventory.station.{0}".format(
                inv_key)
            logger.info(msg)
            continue
        if inv_key == 'operators':
            operator = inventory.Operator(
                agency=[station_obj.acquired_by.organization])
            operator.contacts = [station_obj.acquired_by.author]
            inv_station.operators = [operator]
        elif inv_key == 'site':
            inv_station.site.description = station_obj.geographic_name
        else:
            setattr(inv_station, inv_key,
                    station_obj.get_attr_from_name(mth5_key))
            
    return inv_station

# =============================================================================
# Translate between metadata and inventory: Channel
# =============================================================================
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

def electric_to_inventory_channel(electric_obj, run_obj, code, 
                                  location_code): 
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

    inv_channel = inventory.Channel(code, location_code,
                                    electric_obj.positive.latitude,
                                    electric_obj.positive.longitude,
                                    electric_obj.positive.elevation,
                                    electric_obj.positive.elevation)
    
    for inv_key, mth5_key in channel_translator.items():
        if mth5_key is None:
            msg = "cannot currently map mth5.station to inventory.station.{0}".format(
                inv_key)
            logger.info(msg)
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
        elif inv_key == 'types':
            inv_channel.types = 'GEOPHYSICAL'
        else:
            setattr(inv_channel, inv_key,
                    electric_obj.get_attr_from_name(mth5_key))
            
    return inv_channel
            
     
def channel_to_inventory_channel(channel_obj, run_obj, code, 
                                 location_code): 
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

    inv_channel = inventory.Channel(code, location_code,
                                    channel_obj.location.latitude,
                                    channel_obj.location.longitude,
                                    channel_obj.location.elevation,
                                    channel_obj.location.elevation)
    
    for inv_key, mth5_key in channel_translator.items():
        if mth5_key is None:
            msg = "cannot currently map mth5.station to inventory.station.{0}".format(
                inv_key)
            logger.info(msg)
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
        elif inv_key == 'types':
            inv_channel.types = 'GEOPHYSICAL'
        else:
            setattr(inv_channel, inv_key,
                    channel_obj.get_attr_from_name(mth5_key))
            
    return inv_channel
     

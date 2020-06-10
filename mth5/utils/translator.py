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
                           'operators': 'project_lead.author',
                           'code': 'archive_network'})

def mth5_survey_to_inventory_network(survey_obj):
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
                           'operators': None,
                           'site': None,
                           'start_date': 'time_period.start',
                           'termination_date': 'time_period.end',
                           'vault': None,
                           'water_level': None})        

def mth5_station_to_inventory_station(station_obj, code):
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
                    
     
     

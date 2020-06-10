# -*- coding: utf-8 -*-
"""
Created on Tue Jun  9 20:44:44 2020

@author: jpeacock
"""

import unittest
from mth5.utils import translator
from mth5 import metadata

# =============================================================================
# 
# =============================================================================
class TestSurvey2Network(unittest.TestCase):
    def setUp(self):
        self.survey_obj = metadata.Survey()
        self.meta_dict = {'survey':
                          {'acquired_by.author': 'MT',
                           'acquired_by.comments': 'tired',
                           'archive_id': 'MT01',
                           'archive_network': 'EM',
                           'citation_dataset.doi': 'http://doi.####',
                           'citation_journal.doi': None,
                           'comments': None,
                           'country': None,
                           'datum': 'WGS84',
                           'geographic_name': 'earth',
                           'name': 'entire survey of the earth',
                           'northwest_corner.latitude': 80.0,
                           'northwest_corner.longitude': 179.9,
                           'project': 'EM-EARTH',
                           'project_lead.author': 'T. Lurric',
                           'project_lead.email': 'mt@mt.org',
                           'project_lead.organization': 'mt rules',
                           'release_license': 'CC 0',
                           'southeast_corner.latitude': -80.,
                           'southeast_corner.longitude': -179.9,
                           'summary': None,
                           'time_period.end_date': '1980-01-01',
                           'time_period.start_date': '2080-01-01'}}
        self.survey_obj.from_dict(self.meta_dict)
        
    def test_survey_to_network(self):
        network_obj = translator.mth5_survey_to_inventory_network(
            self.survey_obj)
        
        self.assertEqual(network_obj.code, self.survey_obj.archive_network)
        self.assertEqual(network_obj.comments, self.survey_obj.comments)
        self.assertEqual(network_obj.start_date, 
                         self.survey_obj.time_period.start_date)
        self.assertEqual(network_obj.end_date, 
                         self.survey_obj.time_period.end_date)
        self.assertEqual(network_obj.restricted_status, 
                         self.survey_obj.release_license)
        self.assertEqual(network_obj.operators[0].agency,
                         self.survey_obj.project_lead.organization)
        self.assertEqual(network_obj.operators[0].contacts[0],
                         self.survey_obj.project_lead.author)
        

class TestStationMetadata(unittest.TestCase):
    """
    test station metadata
    """
    
    def setUp(self):
        self.maxDiff = None
        self.station_obj = metadata.Station()
        self.meta_dict = {'station':
                          {'acquired_by.author': 'mt',
                           'acquired_by.comments': None,
                           'archive_id': 'MT012',
                           'channel_layout': 'L',
                           'channels_recorded': 'Ex, Ey, Hx, Hy',
                           'comments': None,
                           'data_type': 'MT',
                           'geographic_name': 'london',
                           'id': 'mt012',
                           'location.declination.comments': None,
                           'location.declination.model': 'WMM',
                           'location.declination.value': 12.3,
                           'location.elevation': 1234.,
                           'location.latitude': 10.0,
                           'location.longitude': -112.98,
                           'orientation.layout_rotation_angle': 0.0,
                           'orientation.method': 'compass',
                           'orientation.option': 'geographic orthogonal',
                           'provenance.comments': None,
                           'provenance.creation_time': '1980-01-01T00:00:00+00:00',
                           'provenance.log': None,
                           'provenance.software.author': 'test',
                           'provenance.software.name': 'name',
                           'provenance.software.version': '1.0a',
                           'provenance.submitter.author': 'name',
                           'provenance.submitter.email': 'test@here.org',
                           'provenance.submitter.organization': None,
                           'time_period.end': '1980-01-01T00:00:00+00:00',
                           'time_period.start': '1980-01-01T00:00:00+00:00'}}
        self.station_obj.from_dict(self.meta_dict)
            
    def test_station_to_station(self):
        inv_station = translator.mth5_station_to_inventory_station(
            self.station_obj, 'EM')
        
        self.assertEqual(inv_station.latitude,
                         self.station_obj.location.latitude)
        self.assertEqual(inv_station.longitude,
                         self.station_obj.location.longitude)
        self.assertEqual(inv_station.elevation, 
                         self.station_obj.location.elevation)
        self.assertEqual(inv_station.start_date, 
                         self.station_obj.time_period.start)
        self.assertEqual(inv_station.end_date, 
                         self.station_obj.time_period.end)
        self.assertListEqual(inv_station.channels, 
                             self.station_obj.channels_recorded)
        self.assertEqual(inv_station.creation_date, 
                         self.station_obj.time_period.start)
        self.assertEqual(inv_station.termination_date, 
                         self.station_obj.time_period.end)
        
        
        
# =============================================================================
# run        
# =============================================================================
if __name__ == '__main__':
    unittest.main()
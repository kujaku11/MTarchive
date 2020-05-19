# -*- coding: utf-8 -*-
"""
Created on Tue Apr 28 18:08:40 2020

@author: jpeacock
"""

# =============================================================================
# Imports
# =============================================================================
import os
import unittest
import json
import numpy as np
import pandas as pd
from mth5 import metadata
from collections import OrderedDict
from operator import itemgetter

# =============================================================================
# Tests
# =============================================================================

class TestSurveyMetadata(unittest.TestCase):
    """
    test metadata in is metadata out
    """

    def setUp(self):
        self.maxDiff = None
        self.meta_dict = {'name_s': 'name test',
                          'id_s': 'id test',
                          'net_code_s': 'net_code test',
                          'start_date_s': '2019-01-02',
                          'end_date_s': '2019-03-05',
                          'northwest_corner.latitude_d': 40.09,
                          'northwest_corner.longitude_d': -115.6,
                          'southeast_corner.latitude_d': 35.90,
                          'southeast_corner.longitude_d': -118.9,
                          'datum_s': 'WGS84',
                          'location_s': 'location test',
                          'country_s': 'country test',
                          'summary_s': 'summary test',
                          'notes_s': 'notes test',
                          'acquired_by.author_s': 'author test',
                          'acquired_by.organization_s': 'organization test',
                          'acquired_by.email_s': 'email@test.mt',
                          'acquired_by.url_s': 'https:test.com',
                          'release_status_s': 'free',
                          'conditions_of_use_s': 'freedom',
                          'citation_dataset.doi_s': 'https:doi.adfa12',
                          'citation_journal.doi_s': None} 
        self.meta_dict = key =  OrderedDict(sorted(self.meta_dict.items(),
                                                   key=itemgetter(0)))
    
        self.survey_object = metadata.Survey()
    
    def test_in_out(self):
        self.survey_object.from_dict(self.meta_dict)
        self.assertDictEqual(self.meta_dict, self.survey_object.to_dict())

        survey_series = pd.Series(self.meta_dict)
        self.survey_object.from_series(survey_series)
        self.assertDictEqual(self.meta_dict, self.survey_object.to_dict())
        
        survey_json = json.dumps(self.meta_dict)
        self.survey_object.from_json((survey_json))
        self.assertDictEqual(self.meta_dict, self.survey_object.to_dict())  
        
    def test_start_date(self):
        self.survey_object.start_date_s = '2020/01/02'
        self.assertEqual(self.survey_object.start_date_s, '2020-01-02')
        
        self.survey_object.start_date_s = '01-02-2020T12:20:30.45Z'
        self.assertEqual(self.survey_object.start_date_s, '2020-01-02')

    def test_end_date(self):
        self.survey_object.start_date_s = '2020/01/02'
        self.assertEqual(self.survey_object.start_date_s, '2020-01-02')
        
        self.survey_object.start_date_s = '01-02-2020T12:20:30.45Z'
        self.assertEqual(self.survey_object.start_date_s, '2020-01-02')
        
    def test_latitude(self):
        self.survey_object.southeast_corner.latitude_d = '40:10:05.123'
        self.assertTrue(np.isclose(self.survey_object.southeast_corner.latitude_d,
                                   40.1680897))
        
    def test_longitude(self):
        self.survey_object.southeast_corner.longitude_d = '-115:34:24.9786'
        self.assertTrue(np.isclose(self.survey_object.southeast_corner.longitude_d,
                                   -115.5736))
        
class TestStationMetadata(unittest.TestCase):
    """
    test station metadata
    """
    
    def setUp(self):
        self.maxDiff = None
        self.station_object = metadata.Station()
        self.meta_dict = {'sta_code_s': 'test sta_code',
                          'name_s': 'test name',
                          'latitude_d': 40.019,
                          'longitude_d': -117.89,
                          'elevation_d': 1230.0,
                          'notes_s': 'notes test',
                          'datum_s': 'data test',
                          'start_s': '2010-01-01T12:30:20+00:00',
                          'end_s': '2010-01-04T07:40:30+00:00',
                          'num_channels_i': 5,
                          'channels_recorded_s': '[ex, ey, hx, hy, hz]',
                          'data_type_s': 'MT',
                          'declination.value_d': -12.3,
                          'declination.units_s': 'degrees',
                          'declination.epoch_s': 'MTM01',
                          'declination.model_s': 'MTM01',
                          'station_orientation_s': 'geographic north',
                          'orientation_method_s': 'compass',
                          'acquired_by.author_s': 'acquired test',
                          'acquired_by.email_s': 'acquired email',
                          'provenance.creation_time_s': '2010-04-01T10:10:10+00:00',
                          'provenance.software.name_s': 'mth5',
                          'provenance.software.version_s': '1.0.1',
                          'provenance.software.author_s': 'Peacock',
                          'provenance.submitter.author_s': 'submitter name',
                          'provenance.submitter.organization_s': 'mt inc',
                          'provenance.submitter.url_s': 'mt.edi',
                          'provenance.submitter.email_s': 'mt@em.edi',
                          'provenance.notes_s': 'goats',
                          'provenance.log_s': 'EY flipped'}
              
        self.meta_dict = key =  OrderedDict(sorted(self.meta_dict.items(),
                                                   key=itemgetter(0)))
    def test_in_out(self):
        self.station_object.from_dict(self.meta_dict)
        out_dict = self.station_object.to_dict()
        self.assertDictEqual(self.meta_dict, out_dict)
        
        station_series = pd.Series(self.meta_dict)
        self.station_object.from_series(station_series)
        self.assertDictEqual(self.meta_dict, self.station_object.to_dict())
        
        station_json = json.dumps(self.meta_dict)
        self.station_object.from_json((station_json))
        self.assertDictEqual(self.meta_dict, self.station_object.to_dict())
        
    def test_start(self):
        self.station_object.start_s = '2020/01/02T12:20:40.4560Z'
        self.assertEqual(self.station_object.start_s, 
                         '2020-01-02T12:20:40.456000+00:00')
        
        self.station_object.start_s = '01/02/20T12:20:40.4560'
        self.assertEqual(self.station_object.start_s, 
                         '2020-01-02T12:20:40.456000+00:00')

    def test_end_date(self):
        self.station_object.end_s = '2020/01/02T12:20:40.4560Z'
        self.assertEqual(self.station_object.end_s, 
                         '2020-01-02T12:20:40.456000+00:00')
        
        self.station_object.end_s = '01/02/20T12:20:40.4560'
        self.assertEqual(self.station_object.end_s, 
                         '2020-01-02T12:20:40.456000+00:00')
        
    def test_latitude(self):
        self.station_object.latitude_d = '40:10:05.123'
        self.assertTrue(np.isclose(self.station_object.latitude_d,
                                   40.1680897))
        
    def test_longitude(self):
        self.station_object.longitude_d = '-115:34:24.9786'
        self.assertTrue(np.isclose(self.station_object.longitude_d,
                                   -115.5736))
        
    def test_declination(self):
        self.station_object.declination.value_d = '10.980'
        self.assertEqual(self.station_object.declination.value_d, 10.980)
        
class TestRun(unittest.TestCase):
    def setUp(self):
        self.meta_dict = OrderedDict([('acquired_by.author_s', 'mt'),
                                      ('acquired_by.email_s', 'mt@mt.org'),
                                      ('channels_recorded_s', 'EX, EY, HX, HY'),
                                      ('data_type_s', 'MT'),
                                      ('end_s', '1980-01-01T00:00:00+00:00'),
                                      ('id_s', 'mt01'),
                                      ('notes_s', 'cables chewed by gophers'),
                                      ('provenance.log_s', None),
                                      ('provenance.notes_s', None),
                                      ('sampling_rate_d', None),
                                      ('start_s', '1980-01-01T00:00:00+00:00')])
        self.meta_dict = OrderedDict(sorted(self.meta_dict.items(), 
                                            key=itemgetter(0)))
        self.run_object = metadata.Run()
   
    def test_in_out(self):
        self.run_object.from_dict(self.meta_dict)
        self.assertDictEqual(self.meta_dict, self.run_object.to_dict())
        
        run_series = pd.Series(self.meta_dict)
        self.run_object.from_series(run_series)
        self.assertDictEqual(self.meta_dict, self.run_object.to_dict())
        
        run_json = json.dumps(self.meta_dict)
        self.run_object.from_json((run_json))
        self.assertDictEqual(self.meta_dict, self.run_object.to_dict())
        
    def test_start(self):
        self.run_object.start_s = '2020/01/02T12:20:40.4560Z'
        self.assertEqual(self.run_object.start_s, 
                         '2020-01-02T12:20:40.456000+00:00')
        
        self.run_object.start_s = '01/02/20T12:20:40.4560'
        self.assertEqual(self.run_object.start_s, 
                         '2020-01-02T12:20:40.456000+00:00')

    def test_end_date(self):
        self.run_object.end_s = '2020/01/02T12:20:40.4560Z'
        self.assertEqual(self.run_object.end_s, 
                         '2020-01-02T12:20:40.456000+00:00')
        
        self.run_object.end_s = '01/02/20T12:20:40.4560'
        self.assertEqual(self.run_object.end_s, 
                         '2020-01-02T12:20:40.456000+00:00')
        
    def test_n_channels(self):
        self.run_object.channels_recorded_s = None
        self.assertEqual(self.run_object.num_channels_i, None)
        
        self.run_object.channels_recorded_s = 'EX, EY, HX, HY, HZ'
        self.assertEqual(self.run_object.num_channels_i, 5)

class TestChannel(unittest.TestCase):
    def setUp(self):
        self.maxDiff = None
        self.channel_object = metadata.Channel()
        self.meta_dict = OrderedDict([('azimuth_d', 0.0),
                                      ('channel_number_i', 1),
                                      ('component_s', 'hx'),
                                      ('data_quality.author_s', 'mt'),
                                      ('data_quality.rating_i', 5),
                                      ('data_quality.warning_flags_s', '0'),
                                      ('data_quality.warning_notes_s', None),
                                      ('datum_s', 'WGS84'),
                                      ('elevation_d', 1200.3),
                                      ('filter.applied_b', [False]),
                                      ('filter.name_s', ['counts2mv']),
                                      ('filter.notes_s', None),
                                      ('latitude_d', 40.12),
                                      ('longitude_d', -115.767),
                                      ('notes_s', None),
                                      ('sample_rate_d', 256.),
                                      ('type_s', 'auxiliary'),
                                      ('units_s', 'mV')])
        
        self.meta_dict = OrderedDict(sorted(self.meta_dict.items(), 
                                            key=itemgetter(0)))
        
    def test_in_out(self):
        self.channel_object.from_dict(self.meta_dict)
        self.assertDictEqual(self.meta_dict, self.channel_object.to_dict())
        
        channel_series = pd.Series(self.meta_dict)
        self.channel_object.from_series(channel_series)
        self.assertDictEqual(self.meta_dict, self.channel_object.to_dict())
        
        channel_json = json.dumps(self.meta_dict)
        self.channel_object.from_json((channel_json))
        self.assertDictEqual(self.meta_dict, self.channel_object.to_dict())
        
class TestElectric(unittest.TestCase):
    def setUp(self):
        self.maxDiff = None
        self.electric_object = metadata.Electric()
        self.meta_dict = OrderedDict([('ac.end_d', 10.0),
                                      ('ac.start_d', 9.0),
                                      ('azimuth_d', 23.0),
                                      ('channel_number_i', 5),
                                      ('component_s', 'EY'),
                                      ('contact_resistance_1.start_d', 1200.0),
                                      ('contact_resistance_2.end_d', 1210.0),
                                      ('data_quality.author_s', 'mt'),
                                      ('data_quality.rating_i', 4),
                                      ('data_quality.warning_flags_s', '0'),
                                      ('data_quality.warning_notes_s', None),
                                      ('dc.end_d', 2.0),
                                      ('dc.start_d', 2.5),
                                      ('dipole_length_d', 120.0),
                                      ('filter.applied_b', [False]),
                                      ('filter.name_s', ['counts2mv']),
                                      ('filter.notes_s', None),
                                      ('negative.datum_s', 'WGS84'),
                                      ('negative.elevation_d', 1200.0),
                                      ('negative.latitude_d', 40.123),
                                      ('negative.longitude_d', -115.134),
                                      ('negative.notes_s', None),
                                      ('notes_s', None),
                                      ('positive.datum_s', 'WGS84'),
                                      ('positive.elevation_d', 1210.0),
                                      ('positive.latitude_d', 40.234),
                                      ('positive.longitude_d', -115.234),
                                      ('positive.notes_s', None),
                                      ('sample_rate_d', 4096.0),
                                      ('type_s', 'electric'),
                                      ('units_s', 'counts')])
        
        self.meta_dict = OrderedDict(sorted(self.meta_dict.items(), 
                                            key=itemgetter(0)))
        
    def test_in_out(self):
        self.electric_object.from_dict(self.meta_dict)
        self.assertDictEqual(self.meta_dict, self.electric_object.to_dict())
        
        electric_series = pd.Series(self.meta_dict)
        self.electric_object.from_series(electric_series)
        self.assertDictEqual(self.meta_dict, self.electric_object.to_dict())
        
        electric_json = json.dumps(self.meta_dict)
        self.electric_object.from_json((electric_json))
        self.assertDictEqual(self.meta_dict, self.electric_object.to_dict())
        

class TestMagnetic(unittest.TestCase):
    def setUp(self):
        self.maxDiff = None
        self.electric_object = metadata.Magnetic()
        self.meta_dict = OrderedDict([('azimuth_d', 0.0),
                                      ('channel_number_i', 2),
                                      ('component_s', 'hy'),
                                      ('data_quality.author_s', 'mt'),
                                      ('data_quality.rating_i', 2),
                                      ('data_quality.warning_flags_s', '0'),
                                      ('data_quality.warning_notes_s', None),
                                      ('datum_s', 'WGS84'),
                                      ('elevation_d', 1230.9),
                                      ('filter.applied_b', [True]),
                                      ('filter.name_s', ['counts2mv']),
                                      ('filter.notes_s', None),
                                      ('h_field_max.end_d', 12.3),
                                      ('h_field_max.start_d',1200.1),
                                      ('h_field_min.end_d', 12.3),
                                      ('h_field_min.start_d', 1400.),
                                      ('latitude_d', 40.234),
                                      ('longitude_d', -113.45),
                                      ('notes_s', None),
                                      ('sample_rate_d', 256.),
                                      ('sensor.id_s', 'ant2284'),
                                      ('sensor.manufacturer_s', None),
                                      ('sensor.type_s', 'induction coil'),
                                      ('type_s', 'magnetic'),
                                      ('units_s', 'mv')])
        
        self.meta_dict = OrderedDict(sorted(self.meta_dict.items(), 
                                            key=itemgetter(0)))
        
    def test_in_out(self):
        self.electric_object.from_dict(self.meta_dict)
        self.assertDictEqual(self.meta_dict, self.electric_object.to_dict())
        
        electric_series = pd.Series(self.meta_dict)
        self.electric_object.from_series(electric_series)
        self.assertDictEqual(self.meta_dict, self.electric_object.to_dict())
        
        electric_json = json.dumps(self.meta_dict)
        self.electric_object.from_json((electric_json))
        self.assertDictEqual(self.meta_dict, self.electric_object.to_dict())
        
# =============================================================================
# run
# =============================================================================
if __name__ == '__main__':
    unittest.main()
# -*- coding: utf-8 -*-
"""
Tests for Metadata module

.. todo::
    * write tests for to/from_xml
    

Created on Tue Apr 28 18:08:40 2020

@author: jpeacock
"""

# =============================================================================
# Imports
# =============================================================================

import unittest
import json
import numpy as np
import pandas as pd
from collections import OrderedDict
from operator import itemgetter
from mth5 import metadata
from mth5.utils.exceptions import MTSchemaError

# =============================================================================
# Tests
# =============================================================================
class TestBase(unittest.TestCase):
    def setUp(self):
        self.maxDiff = None
        self.base_object = metadata.Base()
        self.extra_name = 'ExtraAttribute'
        self.extra_v_dict = {'type': str, 'required': True, 'units': 'mv',
                             'style': 'name'}
        self.extra_value = 10
        
    def test_validate_name(self):
        self.assertEqual('name.test_case', 
                         self.base_object._validate_name('name/TestCase'))
        
        self.assertRaises(MTSchemaError,
                          self.base_object._validate_name,
                          '0Name/Test_case')
        
    def test_add_attribute(self):
        self.base_object.add_base_attribute(self.extra_name,
                                            self.extra_value,
                                            self.extra_v_dict)
        self.assertIsInstance(self.base_object.extra_attribute, 
                              self.extra_v_dict['type'])
        self.assertEqual(self.base_object.extra_attribute, '10')
        
        
    def test_validate_type(self):
        self.assertEqual(10.0, self.base_object._validate_type('10',
                                                               'float'))
        self.assertEqual(10, self.base_object._validate_type('10', int))
        self.assertEqual('10', self.base_object._validate_type(10, str))
        self.assertEqual(True, self.base_object._validate_type('true', bool))
        
        number_list = [10, '11', 12.6, '13.3']
        self.assertEqual([10, 11, 12, 13], 
                         self.base_object._validate_type(number_list, int))
        self.assertEqual([10., 11., 12.6, 13.3], 
                          self.base_object._validate_type(number_list, float))
        self.assertEqual(['10', '11', '12.6', '13.3'], 
                          self.base_object._validate_type(number_list, str))
        self.assertEqual([True, False], 
                         self.base_object._validate_type(['true', 'False'],
                                                         bool))
        
class TestLocation(unittest.TestCase):
    def setUp(self):
        self.lat_str = '40:20:10.15'
        self.lat_value = 40.336153
        self.lon_str = '-115:20:30.40'
        self.lon_value = -115.34178
        self.elev_str = '1234.5'
        self.elev_value = 1234.5
        self.location_object = metadata.Location()
        self.lat_fail_01 = '40:20.34556'
        self.lat_fail_02 = 96.78
        self.lon_fail_01 = '-112:23.3453'
        self.lon_fail_02 = 190.87

    def test_str_conversion(self):
        self.location_object.latitude = self.lat_str
        self.assertAlmostEqual(self.lat_value, 
                               self.location_object.latitude,
                               places=5)
        
        self.location_object.longitude = self.lon_str
        self.assertAlmostEqual(self.lon_value, 
                               self.location_object.longitude,
                               places=5)
        
        self.location_object.elevation = self.elev_str
        self.assertAlmostEqual(self.elev_value, 
                               self.location_object.elevation,
                               places=1)
        
    def test_fails(self):
        self.assertRaises(ValueError, 
                          self.location_object._assert_lat_value,
                          self.lat_fail_01)
        self.assertRaises(ValueError, 
                          self.location_object._assert_lat_value,
                          self.lat_fail_02)
        self.assertRaises(ValueError, 
                          self.location_object._assert_lon_value,
                          self.lon_fail_01)
        self.assertRaises(ValueError, 
                          self.location_object._assert_lon_value,
                          self.lon_fail_02)

class TestSurveyMetadata(unittest.TestCase):
    """
    test metadata in is metadata out
    """

    def setUp(self):
        self.maxDiff = None
        self.meta_dict = {'survey':
                          {'project': 'name test',
                           'survey': 'id test',
                           'net_code': 'net_code test',
                           'time_period.start_date': '2019-01-02',
                           'time_period.end_date': '2019-03-05',
                           'northwest_corner.latitude': 40.09,
                           'northwest_corner.longitude': -115.6,
                           'southeast_corner.latitude': 35.90,
                           'southeast_corner.longitude': -118.9,
                           'datum': 'WGS84',
                           'geographic_location': 'location test',
                           'country': 'country test',
                           'summary': 'summary test',
                           'comments': 'comments test',
                           'acquired_by.author': 'author test',
                           'acquired_by.organization': 'organization test',
                           'acquired_by.email': 'email@test.mt',
                           'acquired_by.url': 'https:test.com',
                           'release_status': 'free',
                           'conditions_of_use': 'freedom',
                           'citation_dataset.doi': 'https:doi.adfa12',
                           'citation_journal.doi': None}}
                          
        self.meta_dict = {'survey': 
                          OrderedDict(sorted(self.meta_dict['survey'].items(),
                                             key=itemgetter(0)))}
    
        self.survey_object = metadata.Survey()
    
    def test_in_out_dict(self):
        self.survey_object.from_dict(self.meta_dict)
        self.assertDictEqual(self.meta_dict, self.survey_object.to_dict())
        
    def test_in_out_series(self):
        survey_series = pd.Series(self.meta_dict['survey'])
        self.survey_object.from_series(survey_series)
        self.assertDictEqual(self.meta_dict, self.survey_object.to_dict())
        
    def test_in_out_json(self):
        survey_json = json.dumps(self.meta_dict)
        self.survey_object.from_json((survey_json))
        self.assertDictEqual(self.meta_dict, self.survey_object.to_dict())
        
        survey_json = self.survey_object.to_json(structured=True)
        self.survey_object.from_json(survey_json)
        self.assertDictEqual(self.meta_dict, self.survey_object.to_dict())
        
    def test_start_date(self):
        self.survey_object.time_period.start_date = '2020/01/02'
        self.assertEqual(self.survey_object.time_period.start_date,
                         '2020-01-02')
        
        self.survey_object.start_date = '01-02-2020T12:20:30.450000+00:00'
        self.assertEqual(self.survey_object.time_period.start_date,
                         '2020-01-02')

    def test_end_date(self):
        self.survey_object.time_period.start_date = '2020/01/02'
        self.assertEqual(self.survey_object.time_period.start_date,
                         '2020-01-02')
        
        self.survey_object.start_date = '01-02-2020T12:20:30.45Z'
        self.assertEqual(self.survey_object.time_period.start_date,
                         '2020-01-02')
        
    def test_latitude(self):
        self.survey_object.southeast_corner.latitude = '40:10:05.123'
        self.assertAlmostEqual(self.survey_object.southeast_corner.latitude,
                               40.1680897,
                               places=5)
        
    def test_longitude(self):
        self.survey_object.southeast_corner.longitude = '-115:34:24.9786'
        self.assertAlmostEqual(self.survey_object.southeast_corner.longitude,
                               -115.57361, places=5)
        
class TestStationMetadata(unittest.TestCase):
    """
    test station metadata
    """
    
    def setUp(self):
        self.maxDiff = None
        self.station_object = metadata.Station()
        self.meta_dict = {'station':
                          {'sta_code': 'test sta_code',
                           'name': 'test name',
                           'location.latitude': 40.019,
                           'location.longitude': -117.89,
                           'location.elevation': 1230.0,
                           'location.datum': 'WGS84',
                           'location.declination.value': -12.3,
                           'location.declination.epoch': 'MTM01',
                           'location.declination.model': 'MTM01',
                           'comments': 'comments test',
                           'time_period.start': '2010-01-01T12:30:20+00:00',
                           'time_period.end': '2010-01-04T07:40:30+00:00',
                           'num_channels': 5,
                           'channels_recorded': '[ex, ey, hx, hy, hz]',
                           'data_type': 'MT',
                           'orientation.option': 'geographic north',
                           'orientation.method': 'compass',
                           'acquired_by.author': 'acquired test',
                           'acquired_by.email': 'acquired email',
                           'provenance.creation_time': '2010-04-01T10:10:10+00:00',
                           'provenance.software.name': 'mth5',
                           'provenance.software.version': '1.0.1',
                           'provenance.software.author': 'Peacock',
                           'provenance.submitter.author': 'submitter name',
                           'provenance.submitter.organization': 'mt inc',
                           'provenance.submitter.url': 'mt.edi',
                           'provenance.submitter.email': 'mt@em.edi',
                           'provenance.comments': 'goats',
                           'provenance.log': 'EY flipped'}}
              
        self.meta_dict = {'station': 
                          OrderedDict(sorted(self.meta_dict['station'].items(),
                                             key=itemgetter(0)))}
    def test_in_out_dict(self):
        self.station_object.from_dict(self.meta_dict)
        self.assertDictEqual(self.meta_dict, self.station_object.to_dict())
        
    def test_in_out_series(self):
        station_series = pd.Series(self.meta_dict['station'])
        self.station_object.from_series(station_series)
        self.assertDictEqual(self.meta_dict, self.station_object.to_dict())
        
    def test_in_out_json(self):
        survey_json = json.dumps(self.meta_dict)
        self.station_object.from_json((survey_json))
        self.assertDictEqual(self.meta_dict, self.station_object.to_dict())
        
        survey_json = self.station_object.to_json(structured=True)
        self.station_object.from_json(survey_json)
        self.assertDictEqual(self.meta_dict, self.station_object.to_dict())
        
    def test_start(self):
        self.station_object.time_period.start = '2020/01/02T12:20:40.4560Z'
        self.assertEqual(self.station_object.time_period.start, 
                         '2020-01-02T12:20:40.456000+00:00')
        
        self.station_object.time_period.start = '01/02/20T12:20:40.4560'
        self.assertEqual(self.station_object.time_period.start, 
                         '2020-01-02T12:20:40.456000+00:00')

    def test_end_date(self):
        self.station_object.time_period.end = '2020/01/02T12:20:40.4560Z'
        self.assertEqual(self.station_object.time_period.end, 
                         '2020-01-02T12:20:40.456000+00:00')
        
        self.station_object.time_period.end = '01/02/20T12:20:40.4560'
        self.assertEqual(self.station_object.time_period.end, 
                         '2020-01-02T12:20:40.456000+00:00')
        
    def test_latitude(self):
        self.station_object.location.latitude = '40:10:05.123'
        self.assertAlmostEqual(self.station_object.location.latitude,
                               40.1680897, places=5)
        
    def test_longitude(self):
        self.station_object.location.longitude = '-115:34:24.9786'
        self.assertAlmostEqual(self.station_object.location.longitude,
                               -115.57361, places=5)
        
    def test_declination(self):
        self.station_object.location.declination.value = '10.980'
        self.assertEqual(self.station_object.location.declination.value,
                         10.980)
        
class TestRun(unittest.TestCase):
    def setUp(self):
        self.maxDiff = None
        self.meta_dict = {'run': 
                          {'acquired_by.author': 'mt',
                           'acquired_by.email': 'mt@mt.org',
                           'channels_recorded': 'EX, EY, HX, HY',
                           'data_type': 'MT',
                           'time_period.end': '1980-01-01T00:00:00+00:00',
                           'id': 'mt01',
                           'comments': 'cables chewed by gophers',
                           'provenance.log': None,
                           'provenance.comments': None,
                           'sampling_rate': None,
                           'time_period.start': '1980-01-01T00:00:00+00:00'}}
            
        self.meta_dict = {'run': 
                          OrderedDict(sorted(self.meta_dict['run'].items(),
                                             key=itemgetter(0)))}
        self.run_object = metadata.Run()
   
    def test_in_out_dict(self):
        self.run_object.from_dict(self.meta_dict)
        self.assertDictEqual(self.meta_dict, self.run_object.to_dict())
        
    def test_in_out_series(self):
        run_series = pd.Series(self.meta_dict['run'])
        self.run_object.from_series(run_series)
        self.assertDictEqual(self.meta_dict, self.run_object.to_dict())
        
    def test_in_out_json(self):
        survey_json = json.dumps(self.meta_dict)
        self.run_object.from_json((survey_json))
        self.assertDictEqual(self.meta_dict, self.run_object.to_dict())
        
        survey_json = self.run_object.to_json(structured=True)
        self.run_object.from_json(survey_json)
        self.assertDictEqual(self.meta_dict, self.run_object.to_dict())
        
    def test_start(self):
        self.run_object.time_period.start = '2020/01/02T12:20:40.4560Z'
        self.assertEqual(self.run_object.time_period.start, 
                         '2020-01-02T12:20:40.456000+00:00')
        
        self.run_object.time_period.start = '01/02/20T12:20:40.4560'
        self.assertEqual(self.run_object.time_period.start, 
                         '2020-01-02T12:20:40.456000+00:00')

    def test_end_date(self):
        self.run_object.time_period.end = '2020/01/02T12:20:40.4560Z'
        self.assertEqual(self.run_object.time_period.end, 
                         '2020-01-02T12:20:40.456000+00:00')
        
        self.run_object.time_period.end = '01/02/20T12:20:40.4560'
        self.assertEqual(self.run_object.time_period.end, 
                         '2020-01-02T12:20:40.456000+00:00')
        
    def test_n_channels(self):
        self.run_object.channels_recorded = None
        self.assertEqual(self.run_object.num_channels, None)
        
        self.run_object.channels_recorded = 'EX, EY, HX, HY, HZ'
        self.assertEqual(self.run_object.num_channels, 5)

class TestChannel(unittest.TestCase):
    def setUp(self):
        self.maxDiff = None
        self.channel_object = metadata.Channel()
        self.meta_dict = {'channel':
                          {'azimuth': 0.0,
                           'channel_number': 1,
                           'component': 'hx',
                           'data_quality.author': 'mt',
                           'data_quality.rating': 5,
                           'data_quality.warning_flags': '0',
                           'data_quality.warning_comments': None,
                           'location.datum': 'WGS84',
                           'location.elevation': 1200.3,
                           'filter.applied': [False],
                           'filter.name': ['counts2mv'],
                           'filter.comments': None,
                           'location.latitude': 40.12,
                           'location.longitude': -115.767,
                           'comments': None,
                           'sample_rate': 256.0,
                           'type': 'auxiliary',
                           'units': 'mV',
                           'time_period.start': '2010-01-01T12:30:20+00:00',
                           'time_period.end': '2010-01-04T07:40:30+00:00'}}
        
        self.meta_dict = {'channel': 
                          OrderedDict(sorted(self.meta_dict['channel'].items(),
                                             key=itemgetter(0)))}
        
    def test_in_out_dict(self):
        self.channel_object.from_dict(self.meta_dict)
        self.assertDictEqual(self.meta_dict, self.channel_object.to_dict())
        
    def test_in_out_series(self):
        channel_series = pd.Series(self.meta_dict['channel'])
        self.channel_object.from_series(channel_series)
        self.assertDictEqual(self.meta_dict, self.channel_object.to_dict())
        
    def test_in_out_json(self):
        survey_json = json.dumps(self.meta_dict)
        self.channel_object.from_json((survey_json))
        self.assertDictEqual(self.meta_dict, self.channel_object.to_dict())
        
        survey_json = self.channel_object.to_json(structured=True)
        self.channel_object.from_json(survey_json)
        self.assertDictEqual(self.meta_dict, self.channel_object.to_dict())
        
class TestElectric(unittest.TestCase):
    def setUp(self):
        self.maxDiff = None
        self.electric_object = metadata.Electric()
        self.meta_dict = {'electric':
                          {'ac.end': 10.0,
                           'ac.start': 9.0,
                           'azimuth': 23.0,
                           'channel_number': 5,
                           'component': 'EY',
                           'contact_resistance.start': 1200.0,
                           'contact_resistance.end': 1210.0,
                           'data_quality.author': 'mt',
                           'data_quality.rating': 4,
                           'data_quality.warning_flags': '0',
                           'data_quality.warning_comments': None,
                           'dc.end': 2.0,
                           'dc.start': 2.5,
                           'dipole_length': 120.0,
                           'filter.applied': [False],
                           'filter.name': ['counts2mv'],
                           'filter.comments': None,
                           'negative.datum': 'WGS84',
                           'negative.elevation': 1200.0,
                           'negative.latitude': 40.123,
                           'negative.longitude': -115.134,
                           'negative.comments': None,
                           'comments': None,
                           'positive.datum': 'WGS84',
                           'positive.elevation': 1210.0,
                           'positive.latitude': 40.234,
                           'positive.longitude': -115.234,
                           'positive.comments': None,
                           'sample_rate': 4096.0,
                           'type': 'electric',
                           'units': 'counts',
                           'time_period.start': '1980-01-01T00:00:00+00:00',
                           'time_period.end': '1980-01-01T00:00:00+00:00'}}
        
        self.meta_dict = {'electric': 
                          OrderedDict(sorted(self.meta_dict['electric'].items(),
                                             key=itemgetter(0)))}
        
    def test_in_out_dict(self):
        self.electric_object.from_dict(self.meta_dict)
        self.assertDictEqual(self.meta_dict, self.electric_object.to_dict())
        
    def test_in_out_series(self):
        electric_series = pd.Series(self.meta_dict['electric'])
        self.electric_object.from_series(electric_series)
        self.assertDictEqual(self.meta_dict, self.electric_object.to_dict())
        
    def test_in_out_json(self):
        survey_json = json.dumps(self.meta_dict)
        self.electric_object.from_json((survey_json))
        self.assertDictEqual(self.meta_dict, self.electric_object.to_dict())
        
        survey_json = self.electric_object.to_json(structured=True)
        self.electric_object.from_json(survey_json)
        self.assertDictEqual(self.meta_dict, self.electric_object.to_dict())
        

class TestMagnetic(unittest.TestCase):
    def setUp(self):
        self.maxDiff = None
        self.magnetic_object = metadata.Magnetic()
        self.meta_dict = {'magnetic':
                          {'azimuth': 0.0,
                           'channel_number': 2,   
                           'component': 'hy', 
                           'data_quality.author': 'mt',
                           'data_quality.rating': 2,
                           'data_quality.warning_flags': '0',
                           'data_quality.warning_comments': None,
                           'location.datum': 'WGS84',
                           'location.elevation': 1230.9,
                           'filter.applied': [True],
                           'filter.name': ['counts2mv'],
                           'filter.comments': None,
                           'h_field_max.end': 12.3,
                           'h_field_max.start': 1200.1,
                           'h_field_min.end': 12.3,
                           'h_field_min.start': 1400.0,
                           'location.latitude': 40.234,
                           'location.longitude': -113.45,
                           'comments': None,
                           'sample_rate': 256.0,
                           'sensor.id': 'ant2284',
                           'sensor.manufacturer': None,
                           'sensor.type': 'induction coil',
                           'type': 'magnetic',
                           'units': 'mv',
                           'time_period.start': '1980-01-01T00:00:00+00:00',
                           'time_period.end': '1980-01-01T00:00:00+00:00'}}
        
        self.meta_dict = {'magnetic': 
                          OrderedDict(sorted(self.meta_dict['magnetic'].items(),
                                             key=itemgetter(0)))}
        
    def test_in_out_dict(self):
        self.magnetic_object.from_dict(self.meta_dict)
        self.assertDictEqual(self.meta_dict, self.magnetic_object.to_dict())
        
    def test_in_out_series(self):
        magnetic_series = pd.Series(self.meta_dict['magnetic'])
        self.magnetic_object.from_series(magnetic_series)
        self.assertDictEqual(self.meta_dict, self.magnetic_object.to_dict())
        
    def test_in_out_json(self):
        survey_json = json.dumps(self.meta_dict)
        self.magnetic_object.from_json((survey_json))
        self.assertDictEqual(self.meta_dict, self.magnetic_object.to_dict())
        
        survey_json = self.magnetic_object.to_json(structured=True)
        self.magnetic_object.from_json(survey_json)
        self.assertDictEqual(self.meta_dict, self.magnetic_object.to_dict())
        
# =============================================================================
# run
# =============================================================================
if __name__ == '__main__':
    unittest.main()
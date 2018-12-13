# -*- coding: utf-8 -*-
"""
Created on Wed Dec 12 10:51:40 2018

@author: jpeacock
"""

# =============================================================================
# Imports
# =============================================================================
import os
import unittest
import mth5
import pandas as pd

# =============================================================================
# Test Suite
# =============================================================================
class TestMTH5ReadCFG(unittest.TestCase):
    """
    test reading a cfg file and updating the attributes
    """
    
    def setUp(self):
        self.mth5_obj = mth5.MTH5()
        cfg_fn = r"example_mth5_cfg.txt"
        self.assertTrue(os.path.isfile(cfg_fn), "{0} not found".format(cfg_fn))
        
        self.mth5_obj.read_mth5_cfg(cfg_fn)
    
    ### Site Attributes
    def test_site_id(self):
        self.assertEqual(self.mth5_obj.site.id,  'MT Test', "site id not equal")
    def test_site_coordinate_system(self):
        self.assertEqual(self.mth5_obj.site.coordinate_system,
                         'Geomagnetic North',
                         "site coordinate system not equal")
    def test_site_datum(self):
        self.assertEqual(self.mth5_obj.site.datum, 'WGS84',
                         "site datum not equal") 
    def test_site_declination(self):
        self.assertEqual(self.mth5_obj.site.declination, 15.5,
                         "site declination not equal")
    def test_site_declination_epoch(self):
        self.assertEqual(self.mth5_obj.site.declination_epoch, 1995)   
    def test_site_elevation(self):
        self.assertEqual(self.mth5_obj.site.elevation, 1110)
    def test_site_elev_units(self):
        self.assertEqual(self.mth5_obj.site.elev_units, 'meters')
    def test_site_latitude(self):
        self.assertEqual(self.mth5_obj.site.latitude, 40.12434)
    def test_site_longitude(self):
        self.assertEqual(self.mth5_obj.site.longitude, -118.345)
    def test_site_survey(self):
        self.assertEqual(self.mth5_obj.site.survey, 'Test')
    def test_site_start_date(self):
        self.assertEqual(self.mth5_obj.site.start_date,
                         '2018-05-07T20:10:00.000000 UTC')
    def test_site_end_date(self):
        self.assertEqual(self.mth5_obj.site.end_date,
                         '2018-07-07T10:20:30.000000 UTC')
    def test_site_acquired_by_name(self):
        self.assertEqual(self.mth5_obj.site.acquired_by.name, 'steve')
    def test_site_acquired_by_email(self):
        self.assertEqual(self.mth5_obj.site.acquired_by.email, 'steve@email.com')
    def test_site_acquired_by_organization(self):
        self.assertEqual(self.mth5_obj.site.acquired_by.organization, 'Enron')
    def test_site_acquired_by_organization_url(self):
        self.assertEqual(self.mth5_obj.site.acquired_by.organization_url,
                         'www.corrupt.enron')
    
    ### Field Notes Attributes    
    # Data logger information
    def test_field_notes_data_logger_id(self):
        self.assertEqual(self.mth5_obj.field_notes.data_logger.id, 'ZEN_test')
    def test_field_notes_data_logger_manufacturer(self):
        self.assertEqual(self.mth5_obj.field_notes.data_logger.manufacturer,
                         'Zonge')
    def test_field_notes_data_logger_type(self):
        self.assertEqual(self.mth5_obj.field_notes.data_logger.type, 
                         '32-Bit 5-channel GPS synced')
        
    # Data quality information
    def test_field_notes_data_quality_comments(self):
        self.assertEqual(self.mth5_obj.field_notes.data_quality.comments, 
                         'testing')
    def test_field_notes_data_quality_rating(self):
        self.assertEqual(self.mth5_obj.field_notes.data_quality.rating, 0)
    def test_field_notes_data_quality_warning_comments(self):
        self.assertEqual(self.mth5_obj.field_notes.data_quality.warnings_comments,
                         'bad data at 2018-06-07T20:10:00.00')
    def test_field_notes_data_quality_warnings_flat(self):
        self.assertEqual(self.mth5_obj.field_notes.data_quality.warnings_flag, 1)
    def test_field_notes_data_quality_author(self):
        self.assertEqual(self.mth5_obj.field_notes.data_quality.author,
                         'C. Cagniard')
        
    # EX Electrode information 
    def test_field_notes_electrode_ex_azimuth(self):
        self.assertEqual(self.mth5_obj.field_notes.electrode_ex.azimuth, 0)
    def test_field_notes_electrode_ex_chn_num(self):
        self.assertEqual(self.mth5_obj.field_notes.electrode_ex.chn_num, 1)
    def test_field_notes_electrode_ex_id(self):
        self.assertEqual(self.mth5_obj.field_notes.electrode_ex.id, 1)
    def test_field_notes_electrode_ex_length(self):
        self.assertEqual(self.mth5_obj.field_notes.electrode_ex.length, 97.)
    def test_field_notes_electrode_ex_manufacturer(self):
        self.assertEqual(self.mth5_obj.field_notes.electrode_ex.manufacturer,
                         'Borin')
    def test_field_notes_electrode_ex_type(self):
        self.assertEqual(self.mth5_obj.field_notes.electrode_ex.type,
                         'Fat Cat Ag-AgCl')
    def test_field_notes_electrode_ex_units(self):
        self.assertEqual(self.mth5_obj.field_notes.electrode_ex.units, 'mV')
    def test_field_notes_electrode_ex_gain(self):
        self.assertEqual(self.mth5_obj.field_notes.electrode_ex.gain, 1)
    def test_field_notes_electrode_ex_contact_resistance(self):
        self.assertEqual(self.mth5_obj.field_notes.electrode_ex.contact_resistance,
                         1)
        
    # EY Electrode information 
    def test_field_notes_electrode_ey_azimuth(self):
        self.assertEqual(self.mth5_obj.field_notes.electrode_ey.azimuth, 90)
    def test_field_notes_electrode_ey_chn_num(self):
        self.assertEqual(self.mth5_obj.field_notes.electrode_ey.chn_num, 2)
    def test_field_notes_electrode_ey_id(self):
        self.assertEqual(self.mth5_obj.field_notes.electrode_ey.id, 2)
    def test_field_notes_electrode_ey_length(self):
        self.assertEqual(self.mth5_obj.field_notes.electrode_ey.length, 92.)
    def test_field_notes_electrode_ey_manufacturer(self):
        self.assertEqual(self.mth5_obj.field_notes.electrode_ey.manufacturer,
                         'Borin')
    def test_field_notes_electrode_ey_type(self):
        self.assertEqual(self.mth5_obj.field_notes.electrode_ey.type, 
                         'Fat Cat Ag-AgCl')
    def test_field_notes_electrode_ey_units(self):
        self.assertEqual(self.mth5_obj.field_notes.electrode_ey.units, 'mV')
    def test_field_notes_electrode_ey_gain(self):
        self.assertEqual(self.mth5_obj.field_notes.electrode_ey.gain, 1)
    def test_field_notes_electrode_ey_contact_resistance(self):
        self.assertEqual(self.mth5_obj.field_notes.electrode_ey.contact_resistance,
                         1)
    
    # HX magnetometer information 
    def test_field_notes_magnetometer_hx_azimuth(self):
        self.assertEqual(self.mth5_obj.field_notes.magnetometer_hx.azimuth, 0)
    def test_field_notes_magnetometer_hx_chn_num(self):
        self.assertEqual(self.mth5_obj.field_notes.magnetometer_hx.chn_num, 3)
    def test_field_notes_magnetometer_hx_id(self):
        self.assertEqual(self.mth5_obj.field_notes.magnetometer_hx.id, 2274)
    def test_field_notes_magnetometer_hx_manufacturer(self):
        self.assertEqual(self.mth5_obj.field_notes.magnetometer_hx.manufacturer,
                         'Geotell')
    def test_field_notes_magnetometer_hx_type(self):
        self.assertEqual(self.mth5_obj.field_notes.magnetometer_hx.type,
                         'Ant 4 Induction Coil')
    def test_field_notes_magnetometer_hx_units(self):
        self.assertEqual(self.mth5_obj.field_notes.magnetometer_hx.units, 'mV')
    def test_field_notes_magnetometer_hx_gain(self):
        self.assertEqual(self.mth5_obj.field_notes.magnetometer_hx.gain, 1)
    
    # HY magnetometer information 
    def test_field_notes_magnetometer_hy_azimuth(self):
        self.assertEqual(self.mth5_obj.field_notes.magnetometer_hy.azimuth, 90)
    def test_field_notes_magnetometer_hy_chn_num(self):
        self.assertEqual(self.mth5_obj.field_notes.magnetometer_hy.chn_num, 4)
    def test_field_notes_magnetometer_hy_id(self):
        self.assertEqual(self.mth5_obj.field_notes.magnetometer_hy.id, 2284)
    def test_field_notes_magnetometer_hy_manufacturer(self):
        self.assertEqual(self.mth5_obj.field_notes.magnetometer_hy.manufacturer,
                         'Geotell')
    def test_field_notes_magnetometer_hy_type(self):
        self.assertEqual(self.mth5_obj.field_notes.magnetometer_hy.type,
                         'Ant 4 Induction Coil')
    def test_field_notes_magnetometer_hy_units(self):
        self.assertEqual(self.mth5_obj.field_notes.magnetometer_hy.units, 'mV')
    def test_field_notes_magnetometer_hy_gain(self):
        self.assertEqual(self.mth5_obj.field_notes.magnetometer_hy.gain, 1)
        
    # HZ magnetometer information 
    def test_field_notes_magnetometer_hz_azimuth(self):
        self.assertEqual(self.mth5_obj.field_notes.magnetometer_hz.azimuth, 0)
    def test_field_notes_magnetometer_hz_chn_num(self):
        self.assertEqual(self.mth5_obj.field_notes.magnetometer_hz.chn_num, 5)
    def test_field_notes_magnetometer_hz_id(self):
        self.assertEqual(self.mth5_obj.field_notes.magnetometer_hz.id, 2294)
    def test_field_notes_magnetometer_hz_manufacturer(self):
        self.assertEqual(self.mth5_obj.field_notes.magnetometer_hz.manufacturer,
                         'Geotell')
    def test_field_notes_magnetometer_hz_type(self):
        self.assertEqual(self.mth5_obj.field_notes.magnetometer_hz.type,
                         'Ant 4 Induction Coil')
    def test_field_notes_magnetometer_hz_units(self):
        self.assertEqual(self.mth5_obj.field_notes.magnetometer_hz.units, 'mV')
    def test_field_notes_magnetometer_hz_gain(self):
        self.assertEqual(self.mth5_obj.field_notes.magnetometer_hz.gain, 1)
        
    ### Copyright information
    def test_copyright_citation_author(self):
        self.assertEqual(self.mth5_obj.copyright.citation.author, 'Tikhanov')
    def test_copyright_citation_doi(self):
        self.assertEqual(self.mth5_obj.copyright.citation.doi,
                         '10.1023/usgs_mt_test')
    def test_copyright_citation_journal(self):
        self.assertEqual(self.mth5_obj.copyright.citation.journal, 'SI')
    def test_copyright_citation_title(self):
        self.assertEqual(self.mth5_obj.copyright.citation.title,
                         'MT HDF5 test')
    def test_copyright_citation_volume(self):
        self.assertEqual(self.mth5_obj.copyright.citation.volume, 1)
    def test_copyright_citation_year(self):
        self.assertEqual(self.mth5_obj.copyright.citation.year, 2018)
    def test_copyright_additional_info(self):
        self.assertEqual(self.mth5_obj.copyright.additional_info,
                         'this is a test')
    def test_copyright_release_status(self):
        self.assertEqual(self.mth5_obj.copyright.release_status,
                         'Open to the public')
        
    ### Software information for making the HDF5 file
    def test_software_name(self):
        self.assertEqual(self.mth5_obj.software.name, 'MTH5py')
    def test_software_version(self):
        self.assertEqual(self.mth5_obj.software.version, 'Beta')
    def test_software_author_email(self):
        self.assertEqual(self.mth5_obj.software.author.email, 'send@gmail.com')
    def test_software_author_name(self):
        self.assertEqual(self.mth5_obj.software.author.name, 'author')
    def test_software_author_organization(self):
        self.assertEqual(self.mth5_obj.software.author.organization,
                         'U.S. Geological Survey')
    def test_software_author_organization_url(self):
        self.assertEqual(self.mth5_obj.software.author.organization_url,
                         'https://test.usgs.gov')
        
    ### Provenance information --> who, when, and where was the data submitted
    def test_provenance_creator_email(self):
        self.assertEqual(self.mth5_obj.provenance.creator.email,
                         'test@gmail.com')
    def test_provenance_creator_author(self):
        self.assertEqual(self.mth5_obj.provenance.creator.name, 'author')
    def test_provenance_creator_organization(self):
        self.assertEqual(self.mth5_obj.provenance.creator.organization,
                         'U.S. Geological Survey')
    def test_provenance_creator_organization_url(self):
        self.assertEqual(self.mth5_obj.provenance.creator.organization_url,
                         'https://www.usgs.gov/')
    def test_provenance_submitter_email(self):
        self.assertEqual(self.mth5_obj.provenance.submitter.email, 
                         'test@gmail.com')
    def test_provenance_submitter_name(self):
        self.assertEqual(self.mth5_obj.provenance.submitter.name, 'author')
    def test_provenance_submitter_oranization(self):
        self.assertEqual(self.mth5_obj.provenance.submitter.organization,
                         'U.S. Geological Survey')
    def test_provenance_submitter_organization_url(self):
        self.assertEqual(self.mth5_obj.provenance.submitter.organization_url,
                         'https://www.usgs.gov/')
    def test_provenance_creating_application(self):
        self.assertEqual(self.mth5_obj.provenance.creating_application,
                         'MTH5py')
    def test_provenance_creation_time(self):
        self.assertEqual(self.mth5_obj.provenance.creation_time,
                         '2017-11-27T21:54:49.00')
        
class TestMTH5UpdateAttributesFromSeries(unittest.TestCase):
    """
    test if attributes are updated from an input series.
    """
    def setUp(self):
        self.mth5_obj = mth5.MTH5()
        
        pd_series = pd.Series({'station': 'MT test',
                                'latitude': 40.90,
                                'longitude': -115.78,
                                'elevation': 1234,
                                'declination': -15.5,
                                'start': '2018-01-01 12:00:00.00',
                                'stop': '2018-02-01 12:00:00.00',
                                'datum': 'WGS84',
                                'coordinate_system': 'Geographic North',
                                'units': 'mV',
                                'instrument_id': 'ZEN_test',
                                'ex_azimuth': 0,
                                'ex_length': 50.0,
                                'ex_sensor': 1,
                                'ex_num': 1,
                                'ey_azimuth': 90,
                                'ey_length': 52.0,
                                'ey_sensor': 2,
                                'ey_num': 2,
                                'hx_azimuth': 0,
                                'hx_sensor': 2274,
                                'hx_num': 3,
                                'hy_azimuth': 90,
                                'hy_sensor': 2284,
                                'hy_num': 4,
                                'hz_azimuth': 0,
                                'hz_sensor': 2294,
                                'hz_num': 5})
        self.mth5_obj.update_metadata_from_series(pd_series)
    
    ### Site Attributes
    def test_site_id(self):
        self.assertEqual(self.mth5_obj.site.id,  'MT test')
    def test_site_coordinate_system(self):
        self.assertEqual(self.mth5_obj.site.coordinate_system,
                         'Geographic North')
    def test_site_datum(self):
        self.assertEqual(self.mth5_obj.site.datum, 'WGS84') 
    def test_site_declination(self):
        self.assertEqual(self.mth5_obj.site.declination, -15.5)   
    def test_site_elevation(self):
        self.assertEqual(self.mth5_obj.site.elevation, 1234)
    def test_site_latitude(self):
        self.assertEqual(self.mth5_obj.site.latitude, 40.90)
    def test_site_longitude(self):
        self.assertEqual(self.mth5_obj.site.longitude, -115.78)
    def test_site_start_date(self):
        self.assertEqual(self.mth5_obj.site.start_date,
                         '2018-01-01T12:00:00.000000 UTC')
    def test_site_end_date(self):
        self.assertEqual(self.mth5_obj.site.end_date,
                         '2018-02-01T12:00:00.000000 UTC')
    def test_site_project2utm(self):
        self.mth5_obj.site.project_location2utm()
        self.assertAlmostEqual(self.mth5_obj.site.easting, 602760.0, places=0)
        self.assertAlmostEqual(self.mth5_obj.site.northing, 4528373.0, places=0)
        self.assertEqual(self.mth5_obj.site.utm_zone, '11T')
    
    ### Field Notes Attributes    
    # Data logger information
    def test_field_notes_data_logger_id(self):
        self.assertEqual(self.mth5_obj.field_notes.data_logger.id, 'ZEN_test')
        
    # EX Electrode information 
    def test_field_notes_electrode_ex_azimuth(self):
        self.assertEqual(self.mth5_obj.field_notes.electrode_ex.azimuth, 0)
    def test_field_notes_electrode_ex_chn_num(self):
        self.assertEqual(self.mth5_obj.field_notes.electrode_ex.chn_num, 1)
    def test_field_notes_electrode_ex_id(self):
        self.assertEqual(self.mth5_obj.field_notes.electrode_ex.id, 1)
    def test_field_notes_electrode_ex_length(self):
        self.assertEqual(self.mth5_obj.field_notes.electrode_ex.length, 50.)
        
    # EY Electrode information 
    def test_field_notes_electrode_ey_azimuth(self):
        self.assertEqual(self.mth5_obj.field_notes.electrode_ey.azimuth, 90)
    def test_field_notes_electrode_ey_chn_num(self):
        self.assertEqual(self.mth5_obj.field_notes.electrode_ey.chn_num, 2)
    def test_field_notes_electrode_ey_id(self):
        self.assertEqual(self.mth5_obj.field_notes.electrode_ey.id, 2)
    def test_field_notes_electrode_ey_length(self):
        self.assertEqual(self.mth5_obj.field_notes.electrode_ey.length, 52.)
    
    # HX magnetometer information 
    def test_field_notes_magnetometer_hx_azimuth(self):
        self.assertEqual(self.mth5_obj.field_notes.magnetometer_hx.azimuth, 0)
    def test_field_notes_magnetometer_hx_chn_num(self):
        self.assertEqual(self.mth5_obj.field_notes.magnetometer_hx.chn_num, 3)
    def test_field_notes_magnetometer_hx_id(self):
        self.assertEqual(self.mth5_obj.field_notes.magnetometer_hx.id, 2274)
    
    # HY magnetometer information 
    def test_field_notes_magnetometer_hy_azimuth(self):
        self.assertEqual(self.mth5_obj.field_notes.magnetometer_hy.azimuth, 90)
    def test_field_notes_magnetometer_hy_chn_num(self):
        self.assertEqual(self.mth5_obj.field_notes.magnetometer_hy.chn_num, 4)
    def test_field_notes_magnetometer_hy_id(self):
        self.assertEqual(self.mth5_obj.field_notes.magnetometer_hy.id, 2284)
        
    # HZ magnetometer information 
    def test_field_notes_magnetometer_hz_azimuth(self):
        self.assertEqual(self.mth5_obj.field_notes.magnetometer_hz.azimuth, 0)
    def test_field_notes_magnetometer_hz_chn_num(self):
        self.assertEqual(self.mth5_obj.field_notes.magnetometer_hz.chn_num, 5)
    def test_field_notes_magnetometer_hz_id(self):
        self.assertEqual(self.mth5_obj.field_notes.magnetometer_hz.id, 2294)

# =============================================================================
# run        
# =============================================================================
if __name__ == '__main__':
    unittest.main()       


# =============================================================================
# File
# =============================================================================


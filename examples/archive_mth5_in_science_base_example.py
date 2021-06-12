# -*- coding: utf-8 -*-
"""
Created on Mon Dec 10 16:53:51 2018

@author: jpeacock
"""

# =============================================================================
# Imports
# =============================================================================
import os
import shutil
import datetime

import mth5.mth5 as mth5
import usgs_archive.usgs_archive as archive
#import usgs_archive.usgs_sb_xml as sb_xml
from usgs_archive import usgs_xml
import getpass

# =============================================================================
# Inputs
# =============================================================================
### path to station data
station_dir = r"c:\Users\jpeacock\DOI\Cox, Evan M - Datarelease_troubleshoot_JP"

### path to survey parameter spread sheet
### this can be made by running this code and setting csv_fn to None
# csv_fn =
csv_fn = None  # r"/mnt/hgfs/MTData/Geysers/Archive/survey_summary.csv"

### path to mth5 configuration file
### this is a configuration file that has metadata explaining most of the
### common information needed by the user.  See example files
cfg_fn = r"c:\Users\jpeacock\Documents\GitHub\MTarchive\examples\example_mth5_cfg.txt"

### path to xml configuration file
### this is a file that has metadata common to the xml files that go into
### science base, see examples files
xml_cfg_fn = r"c:\Users\jpeacock\Documents\GitHub\MTarchive\examples\example_xml_configuration.cfg"

### path to main xml file template.  This could be made somewhere else and
### has been through review.  
xml_main_template = r"c:\Users\jpeacock\Documents\GitHub\MTarchive\xml_templates\mt_root_template.xml"

### path to xml template for child item
### this is a file that has been created according to the metadata standards
### and only a few fields will be update with station specific information
xml_child_template = r"c:\Users\jpeacock\Documents\GitHub\MTarchive\xml_templates\mt_child_template.xml"

### path to calibration files
### path to the calibrations.  These are assumed to be
### in the format (frequency, real, imaginary) for each coil with the
### coil name in the file name, e.g. ant2284.[cal, txt, csv]
### see example script
calibration_dir = r"/mnt/hgfs/MTData/Ant_calibrations"

### paths to edi and png files if not already copied over
### typically all edi files are stored in one folder, but to make it easier
### to archive the code copies the edi and png files into the archve/station
### folder that makes it easier to upload to science base
edi_path = r"/mnt/hgfs/MTData/Geysers/final_edi"
png_path = r"/mnt/hgfs/MTData/Geysers/final_png"

### Make xml file each
make_xml = True

### if the chile xmls are already made, put them all in the same folder and add the
### path here.
xml_path = r"path/to/xml/file"

### SCIENCE BASE
### page id number
### this is the end of the link that science base sends you
page_id = "############"
username = "user@usgs.gov"
password = None

### summarize all runs [ True | False ]
### this will make a .csv file that summarizes the survey by summarizing
### all runs for a station for  all stations,
### you can use this file as the csv_fn above.
### also this will create a shape file of station locations
summarize = True

### upload data [ True | False]
upload_data = False
### type of files to upload in case you want to upload different formats
upload_files = [".zip", ".edi", ".png", ".xml", ".mth5"]
### if upload_data is True need to get the password for the user
### NOTE: you should run this in a generic python shell, if you use an
### ipython shell or Spyder or other IDL the password will be visible.
if upload_data:
    password = getpass.getpass()

# =============================================================================
# Make an archive folder to put everything
# =============================================================================
save_dir = os.path.join(station_dir, "Archive")
if not os.path.exists(save_dir):
    os.mkdir(save_dir)
# =============================================================================
# get station folders
# =============================================================================
station_list = [
    station
    for station in os.listdir(station_dir)
    if os.path.isdir(os.path.join(station_dir, station))
]

# =============================================================================
# Loop over stations
# =============================================================================
st = datetime.datetime.now()
for station in station_list:
    z3d_dir = os.path.join(station_dir, station)
    if os.path.isdir(z3d_dir):
        ### get the file names for each block of z3d files if none skip
        zc = archive.Z3DCollection()
        try:
            fn_list = zc.get_time_blocks(z3d_dir)
        except archive.ArchiveError:
            print("*** Skipping folder {0} because no Z3D files***".format(station))
            continue

        ### make a folder in the archive folder
        station_save_dir = os.path.join(save_dir, station)
        if not os.path.exists(station_save_dir):
            os.mkdir(station_save_dir)
        print("--> Archiving Station {0} ...".format(station))

        ### capture output to put into a log file
        with archive.Capturing() as output:
            station_st = datetime.datetime.now()
            # ### copy edi and png into archive director
            # if not os.path.isfile(os.path.join(station_save_dir, '{0}.edi'.format(station))):
            #     shutil.copy(os.path.join(edi_path, '{0}.edi'.format(station)),
            #                 os.path.join(station_save_dir, '{0}.edi'.format(station)))
            # if not os.path.isfile(os.path.join(station_save_dir, '{0}.png'.format(station))):
            #     shutil.copy(os.path.join(png_path, '{0}.png'.format(station)),
            #                 os.path.join(station_save_dir, '{0}.png'.format(station)))

            ### Make MTH5 File
            m = mth5.MTH5()
            mth5_fn = os.path.join(station_save_dir, "{0}.mth5".format(station))
            m.open_mth5(mth5_fn)
            if not m.h5_is_write:
                raise mth5.MTH5Error("Something is wrong")

            ### update metadata from csv and cfg files
            m.update_metadata_from_cfg(cfg_fn)
            if csv_fn is not None:
                try:
                    station_df = archive.get_station_info_from_csv(csv_fn, station)
                    m.update_metadata_from_series(station_df)
                except archive.ArchiveError as err:
                    print("{0} {1} {0}".format("*" * 4, err))
            m.write_metadata()

            ### loop over schedule blocks
            for ii, fn_block in enumerate(fn_list, 1):
                sch_obj = zc.merge_z3d(fn_block)
                sch_obj.name = "schedule_{0:02}".format(ii)
                sch_obj.write_metadata_csv(station_save_dir)

                ### create group for schedule action
                m.add_schedule(sch_obj)

            # ### add calibrations
            # for hh in ['hx', 'hy', 'hz']:
            #     mag_obj = getattr(m.field_notes, 'magnetometer_{0}'.format(hh))
            #     if mag_obj.id is not None and mag_obj.id != 0:
            #         cal_fn = os.path.join(calibration_dir,
            #                               'ant_{0}.csv'.format(mag_obj.id))
            #         cal_hx = mth5.Calibration()
            #         cal_hx.from_csv(cal_fn)
            #         cal_hx.name = hh
            #         cal_hx.instrument_id = mag_obj.id
            #         cal_hx.calibration_person.email = 'zonge@zonge.com'
            #         cal_hx.calibration_person.name = 'Zonge International'
            #         cal_hx.calibration_person.organization = 'Zonge International'
            #         cal_hx.calibration_person.organization_url = 'zonge.com'
            #         cal_hx.calibration_date = '2013-05-04'
            #         cal_hx.units = 'mV/nT'

            #         m.add_calibration(cal_hx)

            m.close_mth5()
            ####------------------------------------------------------------------
            #### Make xml file for science base
            ####------------------------------------------------------------------
            # make a station database
            s_df, run_csv_fn = archive.combine_station_runs(station_save_dir)
            # summarize the runs
            s_df = archive.summarize_station_runs(s_df)
            
            # make xml file
            if make_xml:
                s_xml = usgs_xml.MTSBXML()
                if xml_child_template:
                   s_xml.read_template_xml(xml_child_template)
                if xml_cfg_fn:
                    s_xml.update_from_config(xml_cfg_fn)
                    
                
                
                # add station name to title and abstract
                s_xml.metadata.idinfo.citation.title.text.replace("{STATION}", station)
    
                s_xml.metadata.idinfo.descript.abstract.text.replace("{STATION}", station)
                
                # add list of files
                s_xml.metadata.idinfo.descript.supplinf.text.replace(
                    "{STATION_FILES}",
                    "\n\t\t\t".join(
                    [
                        "{0}.edi".format(station),
                        "{0}.png".format(station),
                        os.path.basename(mth5_fn),
                    ]
                ))            
                
                for ii in range(3):
                    s_xml.metadata.eainfo.overview[ii].eaover.text.replace("{STATION}", station)
                    s_xml.metadata.eainfo.overview[ii].eadetcit.text.replace("{STATION}", station)
                
               
    
                # location
                s_xml.update_bounding_box(s_df.longitude.max(),
                                          s_df.longitude.min(),
                                          s_df.latitude.max(),
                                          s_df.latitude.min())
    
                # start and end time
                s_xml.update_time_period(s_df.start_date, s_df.stop_date)
    
                # write station xml
                s_xml.write_xml_file(
                    os.path.join(station_save_dir, "{0}_meta.xml".format(station)),
                    write_station=True,
                )
            if not make_xml and os.path.exists(xml_path):
                shutil.copy(os.path.join(xml_path, '{0}.png'.format(station)),
                            os.path.join(station_save_dir, '{0}.png'.format(station)))

            station_et = datetime.datetime.now()
            t_diff = station_et - station_st
            print("Took --> {0:.2f} seconds".format(t_diff.total_seconds()))

        ####------------------------------------------------------------------
        #### Upload data to science base
        #### -----------------------------------------------------------------
        if upload_data:
            try:
                archive.sb_upload_data(
                    page_id, station_save_dir, username, password, f_types=upload_files
                )
            except Exception as error:
                print("xxx FAILED TO UPLOAD {0} xxx".format(station))
                print(error)

        log_fn = os.path.join(station_save_dir, "archive_{0}.log".format(station))
        try:
            with open(log_fn, "w") as log_fid:
                log_fid.write("\n".join(output))
        except Exception as error:
            print("\tCould not write log file for {0}".format(station))
            print(error)

# =============================================================================
# Combine all information into a database
# =============================================================================
if summarize:
    survey_df, survey_csv = archive.combine_survey_csv(save_dir)

    ### write shape file
    shp_fn = archive.write_shp_file(survey_csv)

    ### write survey xml
    # adjust survey information to align with data
    survey_xml = sb_xml.XMLMetadata()
    survey_xml.read_config_file(xml_cfg_fn)
    survey_xml.supplement_info = survey_xml.supplement_info.replace("\\n", "\n\t\t\t")

    # location
    survey_xml.survey.east = survey_df.longitude.min()
    survey_xml.survey.west = survey_df.longitude.max()
    survey_xml.survey.south = survey_df.latitude.min()
    survey_xml.survey.north = survey_df.latitude.max()

    # get elevation min and max from station locations, not sure if this is correct
    survey_xml.survey.elev_min = survey_df.elevation.min()
    survey_xml.survey.elev_max = survey_df.elevation.max()

    # dates
    survey_xml.survey.begin_date = survey_df.start_date.min()
    survey_xml.survey.end_date = survey_df.stop_date.max()

    ### --> write survey xml file
    survey_xml.write_xml_file(os.path.join(save_dir, "{0}.xml".format("mp_survey")))

# print timing
et = datetime.datetime.now()
t_diff = et - st
print(
    "--> Archiving took: {0}:{1:05.2f}, finished at {2}".format(
        int(t_diff.total_seconds() // 60),
        t_diff.total_seconds() % 60,
        datetime.datetime.ctime(datetime.datetime.now()),
    )
)

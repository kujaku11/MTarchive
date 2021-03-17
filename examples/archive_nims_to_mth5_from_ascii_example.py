# -*- coding: utf-8 -*-
"""
Created on Mon Jul  6 15:07:59 2020

Read in a ascii files for a single station.  The ascii files are made from 
nims data and convert it to MTH5. 

If you want to do multiple stations you will need to write a for loop.

You will need to populate the configuration files as you do for Z3D files but
this will be more manual input because there is not a lot of metadata stored
in the BIN file.  Follow the template in the example files.

You should also copy edi and png files to the appropriate folders
    * final_edi
    * final_png

Not sure what to do about calibrations, assuming that all calibrations are
already done because the data are in physical units.

:copyright:
    author: Jared Peacock
    
:license:
    MIT
    
"""

# =============================================================================
# Imports
# =============================================================================

from pathlib import Path
import shutil
import getpass
import datetime

from usgs_archive import usgs_archive
from mth5 import mth5
import usgs_archive.usgs_sb_xml as sb_xml

# =============================================================================
# Input parameters
# =============================================================================
# station directory
station_dir = Path(r"C:\Users\jpeacock\Downloads")

# name of the station, needs to be verbatim what's in the ascii files.
station = "test"

# ascii file name
nims_ascii_fn_list = station_dir.glob("*.asc")

# path to save mth5 file to
station_save_dir = Path(r"C:\Users\jpeacock\Downloads\test_ascii")

### path to survey parameter spread sheet
### this can be made by running this code and setting csv_fn to None
# csv_fn =
csv_fn = r"c:\Users\jpeacock\Documents\GitHub\MTarchive\examples\imush_archive_summary_edited.csv"

### path to mth5 configuration file
### this is a configuration file that has metadata explaining most of the
### common information needed by the user.  See example files
cfg_fn = r"c:\Users\jpeacock\Documents\GitHub\MTarchive\examples\example_mth5_cfg.txt"

### path to xml configuration file
### this is a file that has metadata common to the xml files that go into
### science base, see examples files
xml_cfg_fn = r"c:\Users\jpeacock\Documents\GitHub\MTarchive\examples\example_xml_configuration.cfg"

### path to calibration files
### path to the calibrations.  These are assumed to be
### in the format (frequency, real, imaginary) for each coil with the
### coil name in the file name, e.g. ant2284.[cal, txt, csv]
### see example script
# calibration_dir = r"/mnt/hgfs/MTData/Ant_calibrations"

### paths to edi and png files if not already copied over
### typically all edi files are stored in one folder, but to make it easier
### to archive the code copies the edi and png files into the archve/station
### folder that makes it easier to upload to science base
### if copy_files is True, look for edi and png files in the paths below for
### the station {station}.{edi, png}
copy_files = False

edi_path = Path(r"/mnt/hgfs/MTData/Geysers/final_edi")
png_path = Path(r"/mnt/hgfs/MTData/Geysers/final_png")

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
summarize = False

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
# Open files and convert to MTH5
# =============================================================================
### capture output to put into a log file
with usgs_archive.Capturing() as output:
    station_st = datetime.datetime.now()

    # read in ascii file
    # it reads in all components into a panda data frame with column names the
    # same as the channel names
    # open an mth5 file
    mth5_obj = mth5.MTH5()
    mth5_obj.open_mth5(station_save_dir.joinpath(f"{station}.mth5"))

    # update the metadata from a cfg file
    mth5_obj.update_metadata_from_cfg(cfg_fn)

    # if you have a spread sheet
    # meta_series = usgs_archive.get_station_info_from_csv(csv_fn, station)

    for nims_ascii_fn in nims_ascii_fn_list:
        asc_obj = usgs_archive.USGSasc()
        asc_obj.read_asc_file(nims_ascii_fn)

        station = f"{asc_obj.SurveyID}{asc_obj.SiteID}"

        # make a schedule object that can be put into an mth5 file
        schedule_obj = mth5.Schedule(asc_obj.RunID)
        schedule_obj.from_ascii(asc_obj)

        # write the run to a csv file
        schedule_obj.write_metadata_csv(station_save_dir)

        # add schedule to mth5 file
        mth5_obj.add_schedule(schedule_obj)

    # close file after all schedules are added.
    mth5_obj.close_mth5()

    ### copy edi and png into archive directory
    if copy_files:
        if not station_save_dir.joinpath(f"{station}.edi").is_file():
            shutil.copy(
                edi_path.joinpath(f"{station}.edi".format(station)),
                station_save_dir.joinpath(f"{station}.edi"),
            )
        if not station_save_dir.joinpath(f"{station}.png").is_file():
            shutil.copy(
                edi_path.joinpath(f"{station}.png".format(station)),
                station_save_dir.joinpath(f"{station}.png"),
            )
    ####------------------------------------------------------------------
    #### Make xml file for science base
    ####------------------------------------------------------------------
    # make a station database
    s_df, run_csv_fn = usgs_archive.combine_station_runs(station_save_dir)
    # summarize the runs
    s_df = usgs_archive.summarize_station_runs(s_df)
    # make xml file
    s_xml = sb_xml.XMLMetadata()
    s_xml.read_config_file(xml_cfg_fn)
    s_xml.supplement_info = s_xml.supplement_info.replace("\\n", "\n\t\t\t")

    # add station name to title
    s_xml.title += ", station {0}".format(station)

    # location
    s_xml.survey.east = s_df.longitude
    s_xml.survey.west = s_df.longitude
    s_xml.survey.north = s_df.latitude
    s_xml.survey.south = s_df.latitude

    # get elevation from national map
    s_elev = usgs_archive.get_nm_elev(s_df.latitude, s_df.longitude)
    s_xml.survey.elev_min = s_elev
    s_xml.survey.elev_max = s_elev

    # start and end time
    s_xml.survey.begin_date = s_df.start_date
    s_xml.survey.end_date = s_df.stop_date

    # add list of files
    s_xml.supplement_info += "\n\t\t\tFile List:\n\t\t\t" + "\n\t\t\t".join(
        [
            "{0}.edi".format(station),
            "{0}.png".format(station),
            Path(mth5_obj.mth5_fn).name,
        ]
    )

    # write station xml
    s_xml.write_xml_file(
        station_save_dir.joinpath("{0}_meta.xml".format(station)), write_station=True
    )

    station_et = datetime.datetime.now()
    t_diff = station_et - station_st
    print("Took --> {0:.2f} seconds".format(t_diff.total_seconds()))

####------------------------------------------------------------------
#### Upload data to science base
#### -----------------------------------------------------------------
if upload_data:
    try:
        usgs_archive.sb_upload_data(
            page_id, station_save_dir, username, password, f_types=upload_files
        )
    except Exception as error:
        print("xxx FAILED TO UPLOAD {0} xxx".format(station))
        print(error)


log_fn = station_save_dir.joinpath("archive_{0}.log".format(station))
try:
    with open(log_fn, "w") as log_fid:
        log_fid.write("\n".join(output))
except Exception as error:
    print("\tCould not write log file for {0}".format(station))
    print(error)

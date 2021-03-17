# -*- coding: utf-8 -*-
"""
Created on Mon Dec 10 16:53:51 2018

@author: jpeacock
"""

# =============================================================================
# Imports
# =============================================================================

import numpy as np
import mth5.mth5 as mth5
import usgs_archive.usgs_archive as archive
import datetime

# =============================================================================
# Inputs
# =============================================================================
z3d_dir = r"c:\Users\jpeacock\Documents\imush\mshH020"
csv_fn = r"c:\Users\jpeacock\Documents\imush\imush_archive_summary_edited.csv"
cfg_fn = r"C:\Users\jpeacock\Documents\GitHub\MTarchive\examples\example_mth5_cfg.txt"
# =============================================================================
# File
# =============================================================================
# need to over write existing files

### get the file names for each block of z3d files
zc = archive.Z3DCollection()
fn_list = zc.get_time_blocks(z3d_dir)

st = datetime.datetime.now()
### Use with so that it will close if something goes amiss
m = mth5.MTH5()
m.open_mth5(r"c:\Users\jpeacock\Documents\imush\mshH020_test.mth5")
if not m.h5_is_write:
    raise mth5.MTH5Error("Something is fucked")

m.update_metadata_from_cfg(cfg_fn)
m.update_metadata_from_series(archive.get_station_info_from_csv(csv_fn, "mshH020"))
m.write_metadata()

for ii, fn_block in enumerate(fn_list, 1):
    sch_obj = zc.merge_z3d(fn_block)
    sch_obj.name = "schedule_{0:02}".format(ii)

    ### create group for schedule action
    m.add_schedule(sch_obj)

### add calibrations
for hh in ["hx", "hy", "hz"]:
    cal_hx = mth5.Calibration()
    cal_hx.from_numpy_array(np.zeros((3, 20)))
    cal_hx.name = hh
    cal_hx.calibration_person.email = "test@email.com"
    cal_hx.calibration_person.name = "test"
    cal_hx.calibration_person.organization = "house"
    cal_hx.calibration_person.organization_url = "www.house.com"
    cal_hx.calibration_date = "2010-10-01"
    cal_hx.units = "mV/nT"

    m.add_calibration(cal_hx)

m.close_mth5()

et = datetime.datetime.now()
t_diff = et - st
print("Took --> {0:.2f} seconds".format(t_diff.total_seconds()))

# return self.hdf5_fn

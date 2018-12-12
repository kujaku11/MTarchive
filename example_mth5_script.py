# -*- coding: utf-8 -*-
"""
Created on Mon Dec 10 16:53:51 2018

@author: jpeacock
"""

# =============================================================================
# Imports
# =============================================================================
import mth5
import usgs_archive as archive
import datetime 
#import numpy as np

# =============================================================================
# Inputs
# =============================================================================
z3d_dir = r"c:\Users\jpeacock\Documents\imush\mshH020"
csv_fn = r"c:\Users\jpeacock\Documents\imush\imush_archive_summary_edited.csv"
cfg_fn = r"C:\Users\jpeacock\Documents\GitHub\MTarchive\example_mth5_cfg.txt"
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
    raise mth5.MTH5Error('Something is fucked')

m.read_mth5_cfg(cfg_fn)    
m.update_metadata_from_series(archive.get_station_info_from_csv(csv_fn, 
                                                               'mshH020'))
m.write_metadata()

#lat_list = []
#lon_list = []
#instr_id_list = []
#start_list = []
#stop_list = []

for ii, fn_block in enumerate(fn_list, 1):
    sch_obj = zc.merge_z3d(fn_block)

    ### create group for schedule action
    m.add_schedule(sch_obj, 'schedule_{0:02}'.format(ii))
    
m.close_mth5()
    
#### calculate the lat and lon
#station_lat = np.median(np.array(lat_list, dtype=np.float))
#station_lon = np.median(np.array(lon_list, dtype=np.float))
#
#### set main attributes
#h5_obj.attrs['station'] = self.station
#h5_obj.attrs['coordinate_system'] = self.coordinate_system 
#h5_obj.attrs['datum'] = self.datum
#h5_obj.attrs['latitude'] = station_lat
#h5_obj.attrs['longitude'] = station_lon
#h5_obj.attrs['elevation'] = get_nm_elev(station_lat, station_lon)
#h5_obj.attrs['instrument_id'] = list(set(instr_id_list))[0]
#h5_obj.attrs['units'] = self.units
#h5_obj.attrs['start'] = sorted(start_list)[0]
#h5_obj.attrs['stop'] = sorted(stop_list)[-1]
#
#run_df, run_csv = combine_station_runs(archive_dir)
#
et = datetime.datetime.now()
t_diff = et-st
print('Took --> {0:.2f} seconds'.format(t_diff.total_seconds()))

#return self.hdf5_fn

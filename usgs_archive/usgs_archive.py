# -*- coding: utf-8 -*-
"""
USGS Archive
==============

    * Collect z3d files into logical scheduled blocks
    * Merge Z3D files into USGS ascii format
    * Collect metadata information
    * make .csv, .xml, .shp files.

Created on Tue Aug 29 16:38:28 2017

@author: jpeacock
"""
#==============================================================================

import os
import time
import datetime
import sys
import glob
from cStringIO import StringIO

import gzip
import urllib2 as url
import xml.etree.ElementTree as ET

import numpy as np
import scipy.signal as sps
import pandas as pd

import mtpy.usgs.zen as zen
import mtpy.usgs.zonge as zonge
import mtpy.utils.gis_tools as gis_tools
import mtpy.utils.configfile as mtcfg

import mth5.mth5 as mth5 

# for writing shape file
import geopandas as gpd
from shapely.geometry import Point

# science base
import sciencebasepy as sb

# =============================================================================
# data base error
# =============================================================================
class ArchiveError(Exception):
    pass
# =============================================================================
# class for capturing the output to store in a file
# =============================================================================
# this should capture all the print statements
class Capturing(list):
    def __enter__(self):
        self._stdout = sys.stdout
        sys.stdout = self._stringio = StringIO()
        return self
    def __exit__(self, *args):
        self.extend(self._stringio.getvalue().splitlines())
        sys.stdout = self._stdout
#==============================================================================
# Need a dummy utc time zone for the date time format
#==============================================================================
class UTC(datetime.tzinfo):
    def utcoffset(self, df):
        return datetime.timedelta(hours=0)
    def dst(self, df):
        return datetime.timedelta(0)
    def tzname(self, df):
        return "UTC"

# =============================================================================
# Collect Z3d files
# =============================================================================
class Z3DCollection(object):
    """
    Collects .z3d files into useful arrays and lists

    ================= ============================= ===========================
    Attribute         Description                   Default
    ================= ============================= ===========================
    chn_order         list of the order of channels [hx, ex, hy, ey, hz]
    meta_notes        extraction of notes from      None
                      the .z3d files
    leap_seconds      number of leap seconds for    16 [2016]
                      a given year
    ================= ============================= ===========================

    ===================== =====================================================
    Methods               Description
    ===================== =====================================================
    get_time_blocks       Get a list of files for each schedule action
    check_sampling_rate   Check the sampling rate a given time block
    check_time_series     Get information for a given time block
    merge_ts              Merge a given schedule block making sure that they
                          line up in time.
    get_chn_order         Get the appropriate channels, in case some are
                          missing
    ===================== =====================================================

    :Example: ::

        >>> import mtpy.usgs.usgs_archive as archive
        >>> z3d_path = r"/Data/Station_00"
        >>> zc = archive.Z3DCollection()
        >>> fn_list = zc.get_time_blocks(z3d_path)

    """

    def __init__(self):

        self.chn_order = ['hx','ex','hy','ey','hz']
        self.meta_notes = None
        self.verbose = True
        self._pd_dt_fmt = '%Y-%m-%d %H:%M:%S.%f'
        self._meta_dtype = np.dtype([('comp', 'S3'),
                                     ('start', np.int64),
                                     ('stop', np.int64),
                                     ('fn', 'S140'),
                                     ('sampling_rate', np.float32),
                                     ('latitude', np.float32),
                                     ('longitude', np.float32),
                                     ('elevation', np.float32),
                                     ('ch_azimuth', np.float32),
                                     ('ch_length', np.float32),
                                     ('ch_num', np.int32),
                                     ('ch_sensor', 'S10'),
                                     ('n_samples', np.int32),
                                     ('t_diff', np.int32),
                                     ('standard_deviation', np.float32),
                                     ('station', 'S12')])

    def _empty_meta_arr(self):
        """
        Create an empty pandas Series
        """
        dtype_list = [('station', 'S10'),
                      ('latitude', np.float),
                      ('longitude', np.float),
                      ('elevation', np.float),
                      ('start', np.int64),
                      ('stop', np.int64),
                      ('sampling_rate', np.float),
                      ('n_chan', np.int),
                      ('n_samples', np.int),
                      ('instrument_id', 'S10'),
                      ('collected_by', 'S30'),
                      ('notes', 'S200'),
                      ('comp', 'S24')]
        
        for cc in ['ex', 'ey', 'hx', 'hy', 'hz']:
            for name, n_dtype in self._meta_dtype.fields.items():
                if name in ['station', 'latitude', 'longitude', 'elevation',
                            'sampling_rate', 'comp']:
                    continue
                elif 'ch' in name:
                    m_name = name.replace('ch', cc)
                else:
                    m_name = '{0}_{1}'.format(cc, name)
                dtype_list.append((m_name, n_dtype[0]))
        ### make an empy data frame, for now just 1 set.
        df = pd.DataFrame(np.zeros(1, dtype=dtype_list))
        
        ### return a pandas series, easier to access than dataframe
        return df.iloc[0]

    def get_time_blocks(self, z3d_dir):
        """
        Organize z3d files into blocks based on start time and sampling rate
        in the file name.

        .. note:: This assumes the z3d file is named
                  * station_date_time_samplingrate_chn.z3d

        :param z3d_dir: full path to z3d files
        :type z3d_dir: string

        :returns: nested list of files for each time block, sorted by time

        :Example: ::

            >>> import mtpy.usgs.usgs_archive as archive
            >>> zc = archive.Z3DCollection()
            >>> fn_list = zc.get_time_blocks(r"/home/mt_data/station_01")

        """
        fn_list = [os.path.join(z3d_dir, fn) for fn in os.listdir(z3d_dir) 
                   if fn.lower().endswith('.z3d')]
        
        merge_list = []
        
        for fn in fn_list:
            z3d_obj = zen.Zen3D(fn=fn)
            z3d_obj.read_all_info()
            merge_list.append({'fn':fn, 'start_date':z3d_obj.zen_schedule, 
                               'df':z3d_obj.df})
        
        if merge_list == []:
            raise ArchiveError('No .z3d files in {0}'.format(z3d_dir))
            
        df = pd.DataFrame(merge_list)
        
        start_list = list(set(df['start_date']))
        
        merge_fn_list = []
        for start in start_list:
            merge_fn_list.append(df[df.start_date == start]['fn'].tolist())

        return merge_fn_list

    #==================================================    
    def merge_z3d(self, fn_list, decimate=1):
        """
        Merge a block of z3d files into a MTH5.Schedule Object
        
        :param fn_list: list of z3d files from same schedule action
        :type fn_list: list of strings
        
        :returns: Schedule object that contains metadata and TS dataframes
        :rtype: mth5.Schedule
        
        :Example: ::
            >>> zc = archive.Z3DCollection()
            >>> fn_blocks = zc.get_time_blocks(r"/home/mt/station_00")
            >>> sch_obj = zc.merge_z3d(fn_blocks[0])
        """
        # length of file list
        n_fn = len(fn_list)
        
        ### get empty series to fill
        meta_df = self._empty_meta_arr()
        
        ### need to get some statistics from the files, sometimes a file can
        ### be corrupt so we can make some of these lists
        lat = np.zeros(n_fn)
        lon = np.zeros(n_fn)
        elev = np.zeros(n_fn)
        station = np.zeros(n_fn, dtype='S12')
        sampling_rate = np.zeros(n_fn)
        zen_num = np.zeros(n_fn, dtype='S4')
        start = []
        stop = []
        n_samples = []
        ts_list = []
        
        print('-'*50)
        for ii, fn in enumerate(fn_list):
            z3d_obj = zen.Zen3D(fn)
            try:
                z3d_obj.read_z3d()
            except zen.ZenGPSError:
                print('xxxxxx BAD FILE: Skipping {0} xxxx'.format(fn))
                continue
            # get the components from the file
            comp = z3d_obj.metadata.ch_cmp.lower()
            # convert the time index into an integer
            dt_index = z3d_obj.ts_obj.ts.data.index.astype(np.int64)/10.**9

            # extract useful data that will be for the full station
            sampling_rate[ii] = z3d_obj.df
            lat[ii] = z3d_obj.header.lat
            lon[ii] = z3d_obj.header.long
            elev[ii] = z3d_obj.header.alt
            station[ii] = z3d_obj.station
            zen_num[ii] = int(z3d_obj.header.box_number)
            
            #### get channel setups
            meta_df['comp'] += '{} '.format(comp)
            meta_df['{0}_{1}'.format(comp, 'start')] = dt_index[0]
            meta_df['{0}_{1}'.format(comp, 'stop')] = dt_index[-1]
            start.append(dt_index[0])
            stop.append(dt_index[-1])
            meta_df['{0}_{1}'.format(comp, 'fn')] = fn
            meta_df['{0}_{1}'.format(comp, 'azimuth')] = z3d_obj.metadata.ch_azimuth
            if 'e' in comp:
                meta_df['{0}_{1}'.format(comp, 'length')] = z3d_obj.metadata.ch_length
            ### get sensor number
            elif 'h' in comp:
                meta_df['{0}_{1}'.format(comp, 'sensor')] = int(z3d_obj.metadata.ch_number.split('.')[0])
            meta_df['{0}_{1}'.format(comp, 'num')] = ii+1
            meta_df['{0}_{1}'.format(comp,'n_samples')] = z3d_obj.ts_obj.ts.shape[0]
            n_samples.append(z3d_obj.ts_obj.ts.shape[0])
            meta_df['{0}_{1}'.format(comp,'t_diff')] = int((dt_index[-1]-dt_index[0])*z3d_obj.df)-\
                                      z3d_obj.ts_obj.ts.shape[0]
            # give deviation in percent
            meta_df['{0}_{1}'.format(comp,'standard_deviation')] = \
                                100*abs(z3d_obj.ts_obj.ts.std()[0]/\
                                        z3d_obj.ts_obj.ts.median()[0])
            try:
                meta_df['notes'] = z3d_obj.metadata.notes.replace('\r', ' ').replace('\x00', '').rstrip()
            except AttributeError:
                pass
            
            ts_list.append(z3d_obj.ts_obj)

        ### fill in meta data for the station
        meta_df.latitude = self._median_value(lat)
        meta_df.longitude = self._median_value(lon)
        meta_df.elevation = get_nm_elev(meta_df.latitude,
                                        meta_df.longitude)
        meta_df.station = self._median_value(station)
        meta_df.instrument_id = 'ZEN{0}'.format(self._median_value(zen_num))
        meta_df.sampling_rate = self._median_value(sampling_rate)
        
        ### merge time series into a single data base
        sch_obj = self.merge_ts_list(ts_list, decimate=decimate)
        meta_df.start = sch_obj.start_seconds_from_epoch
        meta_df.stop = sch_obj.stop_seconds_from_epoch
        meta_df.n_chan = sch_obj.n_channels
        meta_df.n_samples = sch_obj.n_samples
        ### add metadata DataFrame to the schedule object
        sch_obj.meta_df = meta_df
        
        return sch_obj
    
    def check_start_times(self, ts_list, tol=10):
        """
        check to make sure the start times align
        """
        dt_index_list = [ts_obj.ts.data.index.astype(np.int64)/10.**9
                         for ts_obj in ts_list]
        
        ### check for unique start times
        start_list = np.array([dt[0] for dt in dt_index_list])
        starts, counts = np.unique(start_list, return_counts=True)
        if len(np.unique(start_list)) > 1:
            start = starts[np.where(counts == counts.max())][0]
            off_index = np.where((start_list < start-tol) | (start_list > start+tol))[0]
            if len(off_index) > 0:
                for off in off_index:
                    off = int(off)
                    print('xxx TS for {0} {1} is off xxx'.format(ts_list[off].station,
                          ts_list[off].component))
                    print('xxx Setting time index to match rest of block xxx')
                    ts_list[off].start_time_epoch_sec = start 
                
        dt_index_list = [ts_obj.ts.data.index.astype(np.int64)/10.**9
                         for ts_obj in ts_list]
        # get start and stop times
        start = max([dt[0] for dt in dt_index_list])
        stop = min([dt[-1] for dt in dt_index_list])
        
        return ts_list, start, stop
        
    
    def merge_ts_list(self, ts_list, decimate=1):
        """
        Merge time series from a list of TS objects.
        
        Looks for the maximum start time and the minimum stop time to align
        the time series.  Indexed by UTC time.
        
        :param ts_list: list of mtpy.core.ts.TS objects from z3d files
        :type ts_list: list
        
        :param decimate: factor to decimate the data by
        :type decimate: int
        
        :returns: merged time series
        :rtype: mth5.Schedule object
        """
        comp_list = [ts_obj.component.lower() for ts_obj in ts_list]
        df = ts_list[0].sampling_rate
        
        ts_list, start, stop = self.check_start_times(ts_list)
        
        ### make start time in UTC
        dt_struct = datetime.datetime.utcfromtimestamp(start)
        start_time_utc = datetime.datetime.strftime(dt_struct, self._pd_dt_fmt)

        # figure out the max length of the array, getting the time difference into
        # seconds and then multiplying by the sampling rate
        max_ts_len = int((stop-start)*df)
        ts_len = min([ts_obj.ts.size for ts_obj in ts_list]+[max_ts_len])
        if decimate > 1:
            ts_len /= decimate

        ### make an empty pandas dataframe to put data into, seems like the
        ### fastes way so far.
        ts_db = pd.DataFrame(np.zeros((ts_len, len(comp_list))),
                             columns=comp_list,
                             dtype=np.float32)
            
        for ts_obj in ts_list:
            comp = ts_obj.component.lower()
            dt_index = ts_obj.ts.data.index.astype(np.int64)/10**9
            index_0 = np.where(dt_index == start)[0][0]
            index_1 = min([ts_len-index_0, ts_obj.ts.shape[0]-index_0])

            ### check to see what the time difference is, should be 0,
            ### but sometimes not, then need to account for that.
            t_diff = ts_len-(index_1-index_0)
            if decimate > 1:
                 ts_db[comp][0:(ts_len-t_diff)/decimate] = \
                                 sps.resample(ts_obj.ts.data[index_0:index_1],
                                              ts_len,
                                              window='hanning')

            else:
                ts_db[comp][0:ts_len-t_diff] = ts_obj.ts.data[index_0:index_1]

        # reorder the columns
        ts_db = ts_db[self.get_chn_order(comp_list)]

        # set the index to be UTC time
        dt_freq = '{0:.0f}N'.format(1./(df)*1E9)
        dt_index = pd.date_range(start=start_time_utc,
                                 periods=ts_db.shape[0],
                                 freq=dt_freq)
        ts_db.index = dt_index
        
        schedule_obj = mth5.Schedule()
        schedule_obj.from_dataframe(ts_db)
        
        return schedule_obj

    def get_chn_order(self, chn_list):
        """
        Get the order of the array channels according to the components.

        .. note:: If you want to change the channel order, change the
                  parameter Z3DCollection.chn_order

        :param chn_list: list of channels in data
        :type chn_list: list

        :return: channel order list
        """

        if len(chn_list) == 5:
            return self.chn_order
        else:
            chn_order = []
            for chn_00 in self.chn_order:
                for chn_01 in chn_list:
                    if chn_00.lower() == chn_01.lower():
                        chn_order.append(chn_00.lower())
                        continue

            return chn_order
        
    def _median_value(self, value_array):
        """
        get the median value from a metadata entry
        """
        try:
            return np.median(value_array[np.nonzero(value_array)])
        except TypeError:
            return list(set(value_array))[0]
        


# =============================================================================
#  Metadata for usgs ascii file
# =============================================================================
class AsciiMetadata(object):
    """
    Container for all the important metadata in a USGS ascii file.

    ========================= =================================================
    Attributes                Description
    ========================= =================================================
    SurveyID                  Survey name
    SiteID                    Site name
    RunID                     Run number
    SiteLatitude              Site latitude in decimal degrees WGS84
    SiteLongitude             Site longitude in decimal degrees WGS84
    SiteElevation             Site elevation according to national map meters
    AcqStartTime              Start time of station YYYY-MM-DDThh:mm:ss UTC
    AcqStopTime               Stop time of station YYYY-MM-DDThh:mm:ss UTC
    AcqSmpFreq                Sampling rate samples/second
    AcqNumSmp                 Number of samples
    Nchan                     Number of channels
    CoordinateSystem          [ Geographic North | Geomagnetic North ]
    ChnSettings               Channel settings, see below
    MissingDataFlag           Missing data value
    ========================= =================================================

    *ChnSettings*
    ========================= =================================================
    Keys                      Description
    ========================= =================================================
    ChnNum                    SiteID+channel number
    ChnID                     Component [ ex | ey | hx | hy | hz ]
    InstrumentID              Data logger + sensor number
    Azimuth                   Setup angle of componet in degrees relative to
                              CoordinateSystem
    Dipole_Length             Dipole length in meters
    ========================= =================================================


    """
    def __init__(self, fn=None, sch_obj=None, **kwargs):
        self.fn = fn
        self.SurveyID = None
        self.RunID = None
        self.sch_obj = sch_obj
        self.MissingDataFlag = np.NaN
        self.CoordinateSystem = None
        self._time_fmt = '%Y-%m-%dT%H:%M:%S %Z'
        self._metadata_len = 30
        self.declination = 0.0

        self._key_list = ['SurveyID',
                          'SiteID',
                          'RunID',
                          'SiteLatitude',
                          'SiteLongitude',
                          'SiteElevation',
                          'AcqStartTime',
                          'AcqStopTime',
                          'AcqSmpFreq',
                          'AcqNumSmp',
                          'Nchan',
                          'CoordinateSystem',
                          'ChnSettings',
                          'MissingDataFlag',
                          'DataSet']

        self._chn_settings = ['ChnNum',
                              'ChnID',
                              'InstrumentID',
                              'Azimuth',
                              'Dipole_Length']
        self._chn_fmt = {'ChnNum':'<8',
                         'ChnID':'<6',
                         'InstrumentID':'<12',
                         'Azimuth':'>7.1f',
                         'Dipole_Length':'>14.1f'}

        for key in kwargs.keys():
            setattr(self, key, kwargs[key])

    @property
    def SiteID(self):
        return self.sch_obj.meta_df.station
    @SiteID.setter
    def SiteID(self, station):
        self.sch_obj.meta_df.station = station

    @property
    def SiteLatitude(self):
        return self._latitude
        #return gis_tools.convert_position_float2str(self._latitude)

    @SiteLatitude.setter
    def SiteLatitude(self, lat):
        self._latitude = gis_tools.assert_lat_value(lat)

    @property
    def SiteLongitude(self):
        return self._longitude
        #return gis_tools.convert_position_float2str(self._longitude)

    @SiteLongitude.setter
    def SiteLongitude(self, lon):
        self._longitude = gis_tools.assert_lon_value(lon)

    @property
    def SiteElevation(self):
        """
        get elevation from national map
        """
        # the url for national map elevation query
        nm_url = r"https://nationalmap.gov/epqs/pqs.php?x={0:.5f}&y={1:.5f}&units=Meters&output=xml"

        # call the url and get the response
        try:
            response = url.urlopen(nm_url.format(self._longitude, self._latitude))
        except url.HTTPError:
            print nm_url.format(self._longitude, self._latitude)
            return -666

        # read the xml response and convert to a float
        info = ET.ElementTree(ET.fromstring(response.read()))
        info = info.getroot()
        for elev in info.iter('Elevation'):
            nm_elev = float(elev.text)
        return nm_elev

    @property
    def AcqStartTime(self):
        return self._start_time.strftime(self._time_fmt)

    @AcqStartTime.setter
    def AcqStartTime(self, time_string):
        if type(time_string) in [int, np.int64]:
            dt = datetime.datetime.utcfromtimestamp(time_string)
        elif type(time_string) in [str]:
            dt = datetime.datetime.strptime(time_string, self._time_fmt)
        self._start_time = datetime.datetime(dt.year, dt.month, dt.day,
                                             dt.hour, dt.minute, dt.second,
                                             dt.microsecond, tzinfo=UTC())

    @property
    def AcqStopTime(self):
        return self._stop_time.strftime(self._time_fmt)

    @AcqStopTime.setter
    def AcqStopTime(self, time_string):
        if type(time_string) in [int, np.int64]:
            dt = datetime.datetime.utcfromtimestamp(time_string)
        elif type(time_string) in [str]:
            dt = datetime.datetime.strptime(time_string, self._time_fmt)
        self._stop_time = datetime.datetime(dt.year, dt.month, dt.day,
                                            dt.hour, dt.minute, dt.second,
                                            dt.microsecond, tzinfo=UTC())

    @property
    def Nchan(self):
        return self._chn_num

    @Nchan.setter
    def Nchan(self, n_channel):
        try:
            self._chn_num = int(n_channel)
        except ValueError:
            print("{0} is not a number, setting Nchan to 0".format(n_channel))

    @property
    def AcqSmpFreq(self):
        return self._sampling_rate
    @AcqSmpFreq.setter
    def AcqSmpFreq(self, df):
        self._sampling_rate = float(df)

    @property
    def AcqNumSmp(self):
        return self._n_samples

    @AcqNumSmp.setter
    def AcqNumSmp(self, n_samples):
        self._n_samples = int(n_samples)

    def read_metadata(self, fn=None, meta_lines=None):
        """
        Read in a meta from the raw string or file.  Populate all metadata
        as attributes.

        :param fn: full path to USGS ascii file
        :type fn: string

        :param meta_lines: lines of metadata to read
        :type meta_lines: list
        """
        chn_find = False
        comp = 0
        self.channel_dict = {}
        if fn is not None:
            self.fn = fn
        if self.fn is not None:
            with open(self.fn, 'r') as fid:
                meta_lines = [fid.readline() for ii in range(self._metadata_len)]
        for ii, line in enumerate(meta_lines):
            if line.find(':') > 0:
                key, value = line.strip().split(':', 1)
                value = value.strip()
                if len(value) < 1 and key == 'DataSet':
                    chn_find = False
                    # return the line that the data starts on that way can
                    # read in as a numpy object or pandas
                    return ii+1
                elif len(value) < 1:
                    chn_find = True
                setattr(self, key, value)
            elif 'coordinate' in line:
                self.CoordinateSystem = ' '.join(line.strip().split()[-2:])
            else:
                if chn_find is True:
                    if 'chnnum' in line.lower():
                        ch_key = line.strip().split()
                    else:
                        line_list = line.strip().split()
                        if len(line_list) == 5:
                            comp += 1
                            self.channel_dict[comp] = {}
                            for key, value in zip(ch_key, line_list):
                                if key.lower() in ['azimuth', 'dipole_length']:
                                    value = float(value)
                                self.channel_dict[comp][key] = value
                        else:
                            print('Not sure what line this is')

    def write_metadata(self, chn_list=['Ex', 'Ey', 'Hx', 'Hy', 'Hz']):
        """
        Write out metadata in the format of USGS ascii.

        :return: list of metadate lines.

        .. note:: meant to use '\n'.join(lines) to write out in a file.
        """

        lines = []
        for key in self._key_list:
            if key in ['ChnSettings']:
                lines.append('{0}:'.format(key))
                lines.append(' '.join(self._chn_settings))
                for chn_key in chn_list:
                    chn_line = []
                    try:
                        for comp_key in self._chn_settings:
                            chn_line.append('{0:{1}}'.format(self.channel_dict[chn_key][comp_key],
                                            self._chn_fmt[comp_key]))
                        lines.append(''.join(chn_line))
                    except KeyError:
                        pass
            elif key in ['DataSet']:
                lines.append('{0}:'.format(key))
                return lines
            else:
                if key in ['SiteLatitude', 'SiteLongitude']:
                    lines.append('{0}: {1:.5f}'.format(key, getattr(self, key)))
                else:
                    lines.append('{0}: {1}'.format(key, getattr(self, key)))

        return lines


# =============================================================================
# Class for the asc file
# =============================================================================
class USGSasc(AsciiMetadata):
    """
    Read and write USGS ascii formatted time series.

    =================== =======================================================
    Attributes          Description
    =================== =======================================================
    ts                  Pandas dataframe holding the time series data
    fn                  Full path to .asc file
    station_dir         Full path to station directory
    meta_notes          Notes of how the station was collected
    =================== =======================================================

    ============================== ============================================
    Methods                        Description
    ============================== ============================================
    get_z3d_db                     Get Pandas dataframe for schedule block
    locate_mtft24_cfg_fn           Look for a mtft24.cfg file in station_dir
    get_metadata_from_mtft24       Get metadata from mtft24.cfg file
    get_metadata_from_survey_csv   Get metadata from survey csv file
    fill_metadata                  Fill Metadata container from a meta_array
    read_asc_file                  Read in USGS ascii file
    convert_electrics              Convert electric channels to mV/km
    write_asc_file                 Write an USGS ascii file
    write_station_info_metadata    Write metadata to a .cfg file
    ============================== ============================================

    :Example: ::

        >>> zc = Z3DCollection()
        >>> fn_list = zc.get_time_blocks(z3d_path)
        >>> zm = USGSasc()
        >>> zm.SurveyID = 'iMUSH'
        >>> zm.get_z3d_db(fn_list[0])
        >>> zm.read_mtft24_cfg()
        >>> zm.CoordinateSystem = 'Geomagnetic North'
        >>> zm.SurveyID = 'MT'
        >>> zm.write_asc_file(str_fmt='%15.7e')
        >>> zm.write_station_info_metadata()
    """

    def __init__(self, **kwargs):
        AsciiMetadata.__init__(self)
        self.ts = None
        self.fn = None
        self.station_dir = os.getcwd()
        self.meta_notes = None
        for key in kwargs.keys():
            setattr(self, key, kwargs[key])

    def get_z3d_db(self, fn_list):
        """
        Merge time series from Z3D files into a pandas database

        :param fn_list: list of Z3D files to merge (full paths)
        :type fn_list: list

        Fills ts attribute as pandas database.
        """
        zc_obj = Z3DCollection()
        self.ts, meta_arr = zc_obj.merge_ts(fn_list)
        self.fill_metadata(meta_arr)
        self.meta_notes = zc_obj.meta_notes

    def locate_mtft24_cfg_fn(self):
        """
        Try to automatically detect mtft24 file

        :return: path to mtft24.cfg file
        """
        for fn in os.listdir(self.station_dir):
            if 'mtft24' in fn and fn.endswith('cfg'):
                return os.path.join(self.station_dir, fn)

        return None

    def get_metadata_from_mtft24_cfg(self, mtft24_cfg_fn=None):
        """
        Read in a MTFT24 configuration file and fill in meta data

        :param mtft24_cfg_fn: full path to mtft24.cfg
        :type: string
        """
        if mtft24_cfg_fn is None:
            mtft24_cfg_fn = self.locate_mtft24_cfg_fn()

        zm = zonge.ZongeMTFT()
        try:
            zm.read_cfg(mtft24_cfg_fn)
        except TypeError:
            print('*** No MTFT24 file for {0} ***'.format(self.SiteID))
            return False

        # need to update channel dict
        # figure out channel order first
        chn_order = dict([(cc.lower(), ii) for ii, cc in enumerate(zm.Chn_Cmp)])
        for chn in self.channel_dict.keys():
            index = chn_order[chn.lower()]
            # get coil number
            if 'h' in chn.lower():
                stem = self.channel_dict[chn]['InstrumentID'].split('-')[0]
                try:
                    inst = self.channel_dict[chn]['InstrumentID'].split('-')[1]
                    if inst != zm.Chn_ID[index]:
                        self.channel_dict[chn]['InstrumentID'] = '{0}-{1}'.format(stem,
                                                                                 zm.Chn_ID[index])
                except IndexError:
                    self.channel_dict[chn]['InstrumentID'] = '{0}-{1}'.format(stem,
                                                                             zm.Chn_ID[index])

            # get azimuth direction
            if 'geographic' in self.CoordinateSystem.lower() and chn.lower() != 'hz':
                azm = float(zm.Chn_Azimuth[index])+self.declination
            else:
                azm = float(zm.Chn_Azimuth[index])
            if np.isnan(self.channel_dict[chn]['Azimuth']):
                self.channel_dict[chn]['Azimuth'] = azm
            elif int(np.nan_to_num(self.channel_dict[chn]['Azimuth'])) != int(azm):
                self.channel_dict[chn]['Azimuth'] = azm

            # get dipole length
            if float(np.nan_to_num(self.channel_dict[chn]['Dipole_Length'])) != float(zm.Chn_Length[index]):
                if 'e' in chn.lower():
                    self.channel_dict[chn]['Dipole_Length'] = float(zm.Chn_Length[index])
        return True

    def get_metadata_from_survey_csv(self, survey_fn):
        """
        get station information from a survey .csv file

        :param survey_fn: full path to survey summary .csv file
        :type survey_fn: string

        """

        try:
            station_db = get_station_info_from_csv(survey_fn, self.SiteID)
        except ValueError:
            print('Could not find information for {0}'.format(self.SiteID))
            return False

        # fill metadata
        for chn in self.channel_dict.keys():
            if 'h' in chn.lower():
                #stem = self.channel_dict[chn]['InstrumentID'].split('-', 1)[0]
                stem = station_db.zen_num
                h_attr = '{0}_{1}'.format(chn.lower(), 'id')
                h_id = getattr(station_db, h_attr)
                self.channel_dict[chn]['InstrumentID'] = '{0}-{1}'.format(stem,
                                                                          h_id)
            elif 'e' in chn.lower():
                self.channel_dict[chn]['InstrumentID'] = station_db.zen_num
                e_attr = '{0}_{1}'.format(chn.lower(), 'len')
                e_len = getattr(station_db, e_attr)
                self.channel_dict[chn]['Dipole_Length'] = e_len

            azm_attr = '{0}_{1}'.format(chn.lower(), 'azm')
            azm_value = getattr(station_db, azm_attr)
            if 'geographic' in self.CoordinateSystem:
                azm_value += self.declination
            self.channel_dict[chn]['Azimuth'] = azm_value
            self.channel_dict[chn]['ChnNum'] = '{0}{1}'.format(self.channel_dict[chn]['ChnNum'][:-1],
                                                               int(getattr(station_db,
                                                                       '{0}_num'.format(chn.lower()))))


        # get location
        self.SiteLatitude = float(station_db.lat)
        self.SiteLongitude = float(station_db.lon)

        return True

    def fill_metadata(self, meta_arr):
        """
        Fill in metadata from time array made by
        Z3DCollection.check_time_series.

        :param meta_arr: structured array of metadata for the Z3D files to be
                         combined.
        :type meta_arr: np.ndarray
        """
        try:
            self.AcqNumSmp = self.ts.shape[0]
        except AttributeError:
            pass
        self.AcqSmpFreq = meta_arr['df'].mean()
        self.AcqStartTime = meta_arr['start'].max()
        self.AcqStopTime = meta_arr['stop'].min()
        try:
            self.Nchan = self.ts.shape[1]
        except AttributeError:
            self.Nchan = meta_arr.shape[0]
        self.RunID = 1
        self.SiteLatitude = np.median(meta_arr['lat'])
        self.SiteLongitude = np.median(meta_arr['lon'])
        self.SiteID = os.path.basename(meta_arr['fn'][0]).split('_')[0]
        self.station_dir = os.path.dirname(meta_arr['fn'][0])

        # if geographic coordinates add in declination
        if 'geographic' in self.CoordinateSystem.lower():
            meta_arr['ch_azimuth'][np.where(meta_arr['comp'] != 'hz')] += self.declination

        # fill channel dictionary with appropriate values
        self.channel_dict = dict([(comp.capitalize(),
                                   {'ChnNum':'{0}{1}'.format(self.SiteID, ii+1),
                                    'ChnID':meta_arr['comp'][ii].capitalize(),
                                    'InstrumentID':meta_arr['ch_box'][ii],
                                    'Azimuth':meta_arr['ch_azimuth'][ii],
                                    'Dipole_Length':meta_arr['ch_length'][ii],
                                    'n_samples':meta_arr['n_samples'][ii],
                                    'n_diff':meta_arr['t_diff'][ii],
                                    'std':meta_arr['std'][ii],
                                    'start':meta_arr['start'][ii]})
                                   for ii, comp in enumerate(meta_arr['comp'])])
        for ii, comp in enumerate(meta_arr['comp']):
            if 'h' in comp.lower():
                self.channel_dict[comp.capitalize()]['InstrumentID'] += '-{0}'.format(meta_arr['ch_num'])

    def read_asc_file(self, fn=None):
        """
        Read in a USGS ascii file and fill attributes accordingly.

        :param fn: full path to .asc file to be read in
        :type fn: string
        """
        if fn is not None:
            self.fn = fn
        st = datetime.datetime.now()
        data_line = self.read_metadata()
        self.ts = pd.read_csv(self.fn,
                              delim_whitespace=True,
                              skiprows=data_line,
                              dtype=np.float32)
        et = datetime.datetime.now()
        read_time = et-st
        print('Reading took {0}'.format(read_time.total_seconds()))

    def convert_electrics(self):
        """
        Convert electric fields into mV/km
        """

        try:
            self.ts.ex /= (self.channel_dict['Ex']['Dipole_Length']/1000.)
        except AttributeError:
            print('No EX')


        try:
            self.ts.ey /= (self.channel_dict['Ey']['Dipole_Length']/1000.)
        except AttributeError:
            print('No EY')

    def _make_file_name(self, save_path=None, compression=True,
                        compress_type='zip'):
        """
        get the file name to save to

        :param save_path: full path to directory to save file to
        :type save_path: string

        :param compression: compress file
        :type compression: [ True | False ]

        :return: save_fn
        :rtype: string

        """
        # make the file name to save to
        if save_path is not None:
            save_fn = os.path.join(save_path,
                                   '{0}_{1}T{2}_{3:.0f}.asc'.format(self.SiteID,
                                    self._start_time.strftime('%Y-%m-%d'),
                                    self._start_time.strftime('%H%M%S'),
                                    self.AcqSmpFreq))
        else:
            save_fn = os.path.join(self.station_dir,
                                   '{0}_{1}T{2}_{3:.0f}.asc'.format(self.SiteID,
                                    self._start_time.strftime('%Y-%m-%d'),
                                    self._start_time.strftime('%H%M%S'),
                                    self.AcqSmpFreq))

        if compression:
            if compress_type == 'zip':
                save_fn = save_fn + '.zip'
            elif compress_type == 'gzip':
                save_fn = save_fn + '.gz'

        return save_fn

    def write_asc_file(self, save_fn=None, chunk_size=1024, str_fmt='%15.7e',
                       full=True, compress=False, save_dir=None,
                       compress_type='zip'):
        """
        Write an ascii file in the USGS ascii format.

        :param save_fn: full path to file name to save the merged ascii to
        :type save_fn: string

        :param chunck_size: chunck size to write file in blocks, larger numbers
                            are typically slower.
        :type chunck_size: int

        :param str_fmt: format of the data as written
        :type str_fmt: string

        :param full: write out the complete file, mostly for testing.
        :type full: boolean [ True | False ]

        :param compress: compress file
        :type compress: boolean [ True | False ]

        :param compress_type: compress file using zip or gzip
        :type compress_type: boolean [ zip | gzip ]
        """
        # get the filename to save to
        save_fn = self._make_file_name(save_path=save_dir,
                                       compression=compress,
                                       compress_type=compress_type)
        # get the number of characters in the desired string
        s_num = int(str_fmt[1:str_fmt.find('.')])

        # convert electric fields into mV/km
        self.convert_electrics()

        print('==> {0}'.format(save_fn))
        print('START --> {0}'.format(time.ctime()))
        st = datetime.datetime.now()

        # write meta data first
        # sort channel information same as columns
        meta_lines = self.write_metadata(chn_list=[c.capitalize() for c in self.ts.columns])
        if compress == True and compress_type == 'gzip':
            with gzip.open(save_fn, 'wb') as fid:
                h_line = [''.join(['{0:>{1}}'.format(c.capitalize(), s_num)
                          for c in self.ts.columns])]
                fid.write('\n'.join(meta_lines+h_line) + '\n')

                # write out data
                if full is False:
                    out = np.array(self.ts[0:chunk_size])
                    out[np.where(out == 0)] = float(self.MissingDataFlag)
                    out = np.char.mod(str_fmt, out)
                    lines = '\n'.join([''.join(out[ii, :]) for ii in range(out.shape[0])])
                    fid.write(lines+'\n')
                    print('END --> {0}'.format(time.ctime()))
                    et = datetime.datetime.now()
                    write_time = et-st
                    print('Writing took: {0} seconds'.format(write_time.total_seconds()))
                    return

                for chunk in range(int(self.ts.shape[0]/chunk_size)):
                    out = np.array(self.ts[chunk*chunk_size:(chunk+1)*chunk_size])
                    out[np.where(out == 0)] = float(self.MissingDataFlag)
                    out = np.char.mod(str_fmt, out)
                    lines = '\n'.join([''.join(out[ii, :]) for ii in range(out.shape[0])])
                    fid.write(lines+'\n')

        else:
            if compress == True and compress_type == 'zip':
                print('ZIPPING')
                save_fn = save_fn[0:-4]
                zip_file = True
                print(zip_file)
            with open(save_fn, 'w') as fid:
                h_line = [''.join(['{0:>{1}}'.format(c.capitalize(), s_num)
                          for c in self.ts.columns])]
                fid.write('\n'.join(meta_lines+h_line) + '\n')

                # write out data
                if full is False:
                    out = np.array(self.ts[0:chunk_size])
                    out[np.where(out == 0)] = float(self.MissingDataFlag)
                    out = np.char.mod(str_fmt, out)
                    lines = '\n'.join([''.join(out[ii, :]) for ii in range(out.shape[0])])
                    fid.write(lines+'\n')
                    print('END --> {0}'.format(time.ctime()))
                    et = datetime.datetime.now()
                    write_time = et-st
                    print('Writing took: {0} seconds'.format(write_time.total_seconds()))
                    return

                for chunk in range(int(self.ts.shape[0]/chunk_size)):
                    out = np.array(self.ts[chunk*chunk_size:(chunk+1)*chunk_size])
                    out[np.where(out == 0)] = float(self.MissingDataFlag)
                    out = np.char.mod(str_fmt, out)
                    lines = '\n'.join([''.join(out[ii, :]) for ii in range(out.shape[0])])
                    fid.write(lines+'\n')

        # for some fucking reason, all interal variables don't exist anymore
        # and if you try to do the zipping nothing happens, so have to do
        # it externally.  WTF
        print('END -->   {0}'.format(time.ctime()))
        et = datetime.datetime.now()
        write_time = et-st
        print('Writing took: {0} seconds'.format(write_time.total_seconds()))

    def write_station_info_metadata(self, save_dir=None, mtft_bool=False):
        """
        write out station info that can later be put into a data base

        the data we need is
            - site name
            - site id number
            - lat
            - lon
            - national map elevation
            - hx azimuth
            - ex azimuth
            - hy azimuth
            - hz azimuth
            - ex length
            - ey length
            - start date
            - end date
            - instrument type (lp, bb)
            - number of channels

        """
        if save_dir is not None:
            save_fn = os.path.join(save_dir,
                                   '{0}_{1}T{2}_{3:.0f}.cfg'.format(self.SiteID,
                                    self._start_time.strftime('%Y-%m-%d'),
                                    self._start_time.strftime('%H%M%S'),
                                    self.AcqSmpFreq))
        else:
            save_fn = os.path.join(self.station_dir,
                                       '{0}_{1}T{2}_{3:.0f}.cfg'.format(self.SiteID,
                                        self._start_time.strftime('%Y-%m-%d'),
                                        self._start_time.strftime('%H%M%S'),
                                        self.AcqSmpFreq))
        meta_dict = {}
        key = '{0}_{1}T{2}_{3:.0f}'.format(self.SiteID,
                                    self._start_time.strftime('%Y-%m-%d'),
                                    self._start_time.strftime('%H%M%S'),
                                    self.AcqSmpFreq)
        meta_dict[key] = {}
        meta_dict[key]['site'] = self.SiteID
        meta_dict[key]['lat'] = self._latitude
        meta_dict[key]['lon'] = self._longitude
        meta_dict[key]['elev'] = self.SiteElevation
        meta_dict[key]['mtft_file'] = mtft_bool
        try:
            meta_dict[key]['hx_azimuth'] = self.channel_dict['Hx']['Azimuth']
            meta_dict[key]['hx_id'] = self.channel_dict['Hx']['InstrumentID'].split('-')[1]
            meta_dict[key]['hx_nsamples'] = self.channel_dict['Hx']['n_samples']
            meta_dict[key]['hx_ndiff'] = self.channel_dict['Hx']['n_diff']
            meta_dict[key]['hx_std'] = self.channel_dict['Hx']['std']
            meta_dict[key]['hx_start'] = self.channel_dict['Hx']['start']
            meta_dict[key]['zen_num'] = self.channel_dict['Hx']['InstrumentID'].split('-')[0]
            meta_dict[key]['hx_num'] = self.channel_dict['Hx']['ChnNum'][-1]
        except KeyError:
            meta_dict[key]['hx_azimuth'] = None
            meta_dict[key]['hx_id'] = None
            meta_dict[key]['hx_nsamples'] = None
            meta_dict[key]['hx_ndiff'] = None
            meta_dict[key]['hx_std'] = None
            meta_dict[key]['hx_start'] = None
            meta_dict[key]['hx_num'] = None

        try:
            meta_dict[key]['hy_azimuth'] = self.channel_dict['Hy']['Azimuth']
            meta_dict[key]['hy_id'] = self.channel_dict['Hy']['InstrumentID'].split('-')[1]
            meta_dict[key]['hy_nsamples'] = self.channel_dict['Hy']['n_samples']
            meta_dict[key]['hy_ndiff'] = self.channel_dict['Hy']['n_diff']
            meta_dict[key]['hy_std'] = self.channel_dict['Hy']['std']
            meta_dict[key]['hy_start'] = self.channel_dict['Hy']['start']
            meta_dict[key]['zen_num'] = self.channel_dict['Hy']['InstrumentID'].split('-')[0]
            meta_dict[key]['hy_num'] = self.channel_dict['Hy']['ChnNum'][-1:]
        except KeyError:
            meta_dict[key]['hy_azimuth'] = None
            meta_dict[key]['hy_id'] = None
            meta_dict[key]['hy_nsamples'] = None
            meta_dict[key]['hy_ndiff'] = None
            meta_dict[key]['hy_std'] = None
            meta_dict[key]['hy_start'] = None
            meta_dict[key]['hy_num'] = None
        try:
            meta_dict[key]['hz_azimuth'] = self.channel_dict['Hz']['Azimuth']
            meta_dict[key]['hz_id'] = self.channel_dict['Hz']['InstrumentID'].split('-')[1]
            meta_dict[key]['hz_nsamples'] = self.channel_dict['Hz']['n_samples']
            meta_dict[key]['hz_ndiff'] = self.channel_dict['Hz']['n_diff']
            meta_dict[key]['hz_std'] = self.channel_dict['Hz']['std']
            meta_dict[key]['hz_start'] = self.channel_dict['Hz']['start']
            meta_dict[key]['zen_num'] = self.channel_dict['Hz']['InstrumentID'].split('-')[0]
            meta_dict[key]['hz_num'] = self.channel_dict['Hz']['ChnNum'][-1:]
        except KeyError:
            meta_dict[key]['hz_azimuth'] = None
            meta_dict[key]['hz_id'] = None
            meta_dict[key]['hz_nsamples'] = None
            meta_dict[key]['hz_ndiff'] = None
            meta_dict[key]['hz_std'] = None
            meta_dict[key]['hz_start'] = None
            meta_dict[key]['hz_num'] = None

        try:
            meta_dict[key]['ex_azimuth'] = self.channel_dict['Ex']['Azimuth']
            meta_dict[key]['ex_id'] = self.channel_dict['Ex']['InstrumentID']
            meta_dict[key]['ex_len'] = self.channel_dict['Ex']['Dipole_Length']
            meta_dict[key]['ex_nsamples'] = self.channel_dict['Ex']['n_samples']
            meta_dict[key]['ex_ndiff'] = self.channel_dict['Ex']['n_diff']
            meta_dict[key]['ex_std'] = self.channel_dict['Ex']['std']
            meta_dict[key]['ex_start'] = self.channel_dict['Ex']['start']
            meta_dict[key]['zen_num'] = self.channel_dict['Ex']['InstrumentID']
            meta_dict[key]['ex_num'] = self.channel_dict['Ex']['ChnNum'][-1:]
        except KeyError:
            meta_dict[key]['ex_azimuth'] = None
            meta_dict[key]['ex_id'] = None
            meta_dict[key]['ex_len'] = None
            meta_dict[key]['ex_nsamples'] = None
            meta_dict[key]['ex_ndiff'] = None
            meta_dict[key]['ex_std'] = None
            meta_dict[key]['ex_start'] = None
            meta_dict[key]['ex_num'] = None
        try:
            meta_dict[key]['ey_azimuth'] = self.channel_dict['Ey']['Azimuth']
            meta_dict[key]['ey_id'] = self.channel_dict['Ey']['InstrumentID']
            meta_dict[key]['ey_len'] = self.channel_dict['Ey']['Dipole_Length']
            meta_dict[key]['ey_nsamples'] = self.channel_dict['Ey']['n_samples']
            meta_dict[key]['ey_ndiff'] = self.channel_dict['Ey']['n_diff']
            meta_dict[key]['ey_std'] = self.channel_dict['Ey']['std']
            meta_dict[key]['ey_start'] = self.channel_dict['Ey']['start']
            meta_dict[key]['zen_num'] = self.channel_dict['Ey']['InstrumentID']
            meta_dict[key]['ey_num'] = self.channel_dict['Ey']['ChnNum'][-1:]
        except KeyError:
            meta_dict[key]['ey_azimuth'] = None
            meta_dict[key]['ey_id'] = None
            meta_dict[key]['ey_len'] = None
            meta_dict[key]['ey_nsamples'] = None
            meta_dict[key]['ey_ndiff'] = None
            meta_dict[key]['ey_std'] = None
            meta_dict[key]['ey_start'] = None
            meta_dict[key]['ey_num'] = None

        meta_dict[key]['start_date'] = self.AcqStartTime
        meta_dict[key]['stop_date'] = self.AcqStopTime
        meta_dict[key]['sampling_rate'] = self.AcqSmpFreq
        meta_dict[key]['n_samples'] = self.AcqNumSmp
        meta_dict[key]['n_chan'] = self.Nchan


        if meta_dict[key]['zen_num'] in [24, 25, 26, 46, '24', '25', '26', '46',
                                        'ZEN24', 'ZEN25', 'ZEN26', 'ZEN46']:
            meta_dict[key]['collected_by'] = 'USGS'
        else:
            meta_dict[key]['collected_by'] = 'OSU'

        # in the old OSU z3d files there are notes in the metadata section
        # pass those on
        meta_dict[key]['notes'] = self.meta_notes

        mtcfg.write_dict_to_configfile(meta_dict, save_fn)

        return save_fn

# =============================================================================
# Get national map elevation data from internet
# =============================================================================
def get_nm_elev(lat, lon):
    """
    Get national map elevation for a given lat and lon.

    Queries the national map website for the elevation value.

    :param lat: latitude in decimal degrees
    :type lat: float

    :param lon: longitude in decimal degrees
    :type lon: float

    :return: elevation (meters)
    :rtype: float

    :Example: ::

        >>> import mtpy.usgs.usgs_archive as archive
        >>> archive.get_nm_elev(35.467, -115.3355)
        >>> 809.12

    .. note:: Needs an internet connection to work.

    """
    nm_url = r"https://nationalmap.gov/epqs/pqs.php?x={0:.5f}&y={1:.5f}&units=Meters&output=xml"

    # call the url and get the response
    try:
        response = url.urlopen(nm_url.format(lon, lat))
    except url.HTTPError:
        print('GET_ELEVATION_ERROR: Could not connect to internet')
        return -666

    # read the xml response and convert to a float
    info = ET.ElementTree(ET.fromstring(response.read()))
    info = info.getroot()
    for elev in info.iter('Elevation'):
        nm_elev = float(elev.text)
    return nm_elev

# =============================================================================
# Functions to analyze csv files
# =============================================================================
def read_pd_series(csv_fn):
    """
    read a pandas series and turn it into a dataframe
    
    :param csv_fn: full path to schedule csv
    :type csv_fn: string
    
    :returns: pandas dataframe 
    :rtype: pandas.DataFrame
    """
    series = pd.read_csv(csv_fn, index_col=0, header=None, squeeze=True)
    
    return pd.DataFrame(dict([(key, [value]) for key, value in zip(series.index,
                                                                   series.values)]))

def combine_station_runs(csv_dir):
    """
    combine all scheduled runs into a single data frame
    
    :param csv_dir: full path the station csv files
    :type csv_dir: string
    
    """
    station = os.path.basename(csv_dir)

    csv_fn_list = sorted([os.path.join(csv_dir, fn) for fn in os.listdir(csv_dir)
                          if 'runs' not in fn and fn.endswith('.csv')])

    count = 0
    for ii, csv_fn in enumerate(csv_fn_list):
        if ii == 0:
            run_df = read_pd_series(csv_fn)

        else:
            run_df = run_df.append(read_pd_series(csv_fn), ignore_index=True)
            count += 1
            
    ### replace any None with 0, makes it easier
    try:
        run_df = run_df.replace('None', '0')
    except UnboundLocalError:
        return None, None

    ### make lat and lon floats
    run_df.latitude = run_df.latitude.astype(np.float)
    run_df.longitude = run_df.longitude.astype(np.float)

    ### write combined csv file
    csv_fn = os.path.join(csv_dir, '{0}_runs.csv'.format(station))
    run_df.to_csv(csv_fn, index=False)
    return run_df, csv_fn

def summarize_station_runs(run_df):
    """
    summarize all runs into a pandas.Series to be appended to survey df
    
    :param run_df: combined run dataframe for a single station
    :type run_df: pd.DataFrame
    
    :returns: single row data frame with summarized information
    :rtype: pd.Series
    """
    station_dict = pd.compat.OrderedDict() 
    for col in run_df.columns:
        if '_fn' in col:
            continue
        if col == 'start':
            value = run_df['start'].min()
            start_date = datetime.datetime.fromtimestamp(float(value))
            station_dict['start_date'] = start_date.isoformat()+' UTC'
        elif col == 'stop':
            value = run_df['stop'].max()
            stop_date = datetime.datetime.fromtimestamp(float(value))
            station_dict['stop_date'] = stop_date.isoformat()+' UTC'
        else:
            try:
                value = run_df[col].median()
            except (TypeError, ValueError):
                value = list(set(run_df[col]))[0]
        station_dict[col] = value
        
    return pd.Series(station_dict)

def combine_survey_csv(survey_dir, skip_stations=None):
    """
    Combine all stations into a single data frame
    
    :param survey_dir: full path to survey directory
    :type survey_dir: string
    
    :param skip_stations: list of stations to skip
    :type skip_stations: list
    
    :returns: data frame with all information summarized
    :rtype: pandas.DataFrame
    
    :returns: full path to csv file
    :rtype: string
    """
    
    if not isinstance(skip_stations, list):
        skip_stations = [skip_stations]
        
    count = 0
    for station in os.listdir(survey_dir):
        station_dir = os.path.join(survey_dir, station)
        if not os.path.isdir(station_dir):
            continue
        if station in skip_stations:
            continue
        
        # get the database and write a csv file
        run_df, run_fn = combine_station_runs(station_dir)
        if run_df is None:
            print('*** No Information for {0} ***'.format(station))
            continue
        if count == 0:
            survey_df = pd.DataFrame(summarize_station_runs(run_df)).T
            count += 1
        else:
            survey_df = survey_df.append(pd.DataFrame(summarize_station_runs(run_df)).T)
            count += 1
            
    survey_df.latitude = survey_df.latitude.astype(np.float)
    survey_df.longitude = survey_df.longitude.astype(np.float)
    
    csv_fn = os.path.join(survey_dir, 'survey_summary.csv')
    survey_df.to_csv(csv_fn, index=False)
    
    return survey_df, csv_fn

def read_survey_csv(survey_csv):
    """
    Read in a survey .csv file that will overwrite existing metadata
    parameters.

    :param survey_csv: full path to survey_summary.csv file
    :type survey_csv: string

    :return: survey summary database
    :rtype: pandas dataframe
    """
    db = pd.read_csv(survey_csv,
                     dtype={'latitude':np.float,
                            'longitude':np.float})
    for key in ['hx_sensor', 'hy_sensor', 'hz_sensor']:
        db[key] = db[key].fillna(0)
        db[key] = db[key].astype(np.int)

    return db

def get_station_info_from_csv(survey_csv, station):
    """
    get station information from a survey .csv file

    :param survey_csv: full path to survey_summary.csv file
    :type survey_csv: string

    :param station: station name
    :type station: string

    :return: station database
    :rtype: pandas dataframe

    .. note:: station must be verbatim for whats in summary.
    """

    db = read_survey_csv(survey_csv)
    try:
        station_index = db.index[db.station == station].tolist()[0]
    except IndexError:
        raise ArchiveError('Could not find {0}, check name'.format(station))

    return db.iloc[station_index]

def write_shp_file(survey_csv_fn, save_path=None):
        """
        write a shape file with important information

        :param survey_csv_fn: full path to survey_summary.csv
        :type survey_csf_fn: string

        :param save_path: directory to save shape file to
        :type save_path: string

        :return: full path to shape files
        :rtype: string
        """
        if save_path is not None:
            save_fn = save_path
        else:
            save_fn = os.path.join(os.path.dirname(survey_csv_fn),
                                   'survey_sites.shp')

        survey_db = pd.read_csv(survey_csv_fn)
        geometry = [Point(x, y) for x, y in zip(survey_db.longitude,
                                                survey_db.latitude)]
        crs = {'init':'epsg:4326'}
        #survey_db = survey_db.drop(['latitude', 'longitude'], axis=1)
        survey_db = survey_db.rename(columns={'collected_by':'operator',
                                              'instrument_id':'instr_id',
                                              'station':'siteID'})

        # list of columns to take from the database
        col_list = ['siteID',
                    'latitude', 
                    'longitude',
                    'elevation',
                    'hx_azimuth',
                    'hy_azimuth',
                    'hz_azimuth',
                    'hx_sensor',
                    'hy_sensor',
                    'hz_sensor',
                    'ex_length',
                    'ey_length',
                    'ex_azimuth',
                    'ey_azimuth',
                    'n_chan',
                    'instr_id',
                    'operator',
                    'type',
                    'quality',
                    'start_date',
                    'stop_date']

        survey_db = survey_db[col_list]

        geo_db = gpd.GeoDataFrame(survey_db,
                                  crs=crs,
                                  geometry=geometry)

        geo_db.to_file(save_fn)

        print('*** Wrote survey shapefile to {0}'.format(save_fn))
        return survey_db, save_fn

# =============================================================================
# Science Base Functions
# =============================================================================
def sb_locate_child_item(sb_session, station, sb_page_id):
    """
    See if there is a child item already for the given station.  If there is
    not an existing child item returns False.

    :param sb_session: sciencebase session object
    :type sb_session: sciencebasepy.SbSession

    :param station: station to archive
    :type station: string

    :param sb_page_id: page id of the sciencebase database to download to
    :type sb_page_id: string

    :returns: page id for the station child item
    :rtype: string or False
    """
    for item_id in sb_session.get_child_ids(sb_page_id):
        ### for some reason there is a child item that doesn't play nice
        ### so have to skip it
        try:
            item_title = sb_session.get_item(item_id, {'fields':'title'})['title']
        except:
            continue
        if station in item_title:
            return item_id

    return False

def sb_sort_fn_list(fn_list):
    """
    sort the file name list to xml, edi, png

    :param fn_list: list of files to sort
    :type fn_list: list

    :returns: sorted list ordered by xml, edi, png, zip files
    """

    fn_list_sort = [None, None, None]
    index_dict = {'xml':0, 'edi':1, 'png':2}

    for ext in ['xml', 'edi', 'png']:
        for fn in fn_list:
            if fn.endswith(ext):
                fn_list_sort[index_dict[ext]] = fn
                fn_list.remove(fn)
                break
    fn_list_sort += sorted(fn_list)

    # check to make sure all the files are there
    if fn_list_sort[0] is None:
        print('\t\t!! No .xml file found !!')
    if fn_list_sort[1] is None:
        print('\t\t!! No .edi file found !!')
    if fn_list_sort[2] is None:
        print('\t\t!! No .png file found !!')

    # get rid of any Nones in the list in case there aren't all the files
    fn_list_sort[:] = (value for value in fn_list_sort if value is not None)

    return fn_list_sort

def sb_session_login(sb_session, sb_username, sb_password=None):
    """
    login in to sb session using the input credentials.  Checks to see if
    you are already logged in.  If no password is given, the password will be
    requested through the command prompt.

    .. note:: iPython shells will echo your password.  Use a Python command
              shell to not have your password echoed.

    :param sb_session: sciencebase session object
    :type sb_session: sciencebasepy.SbSession

    :param sb_username: sciencebase username, typically your full USGS email
    :type sb_username: string

    :param sb_password: AD password
    :type sb_password: string

    :returns: logged in sciencebasepy.SbSession
    """

    if not sb_session.is_logged_in():
        if sb_password is None:
            sb_session.loginc(sb_username)
        else:
            sb_session.login(sb_username, sb_password)
        time.sleep(5)

    return sb_session

def sb_get_fn_list(archive_dir, 
                   f_types=['.zip', '.edi', '.png', '.xml', '.mth5']):
    """
    Get the list of files to archive looking for .zip, .edi, .png within the
    archive directory.  Sorts in the order of xml, edi, png, zip

    :param archive_dir: full path to the directory to be archived
    :type archive_dir: string

    :returns: list of files to archive ordered by xml, edi, png, zip

    """
    fn_list = []
    for f_type in f_types:
        fn_list += glob.glob(os.path.join(archive_dir, '*{0}'.format(f_type)))

    return sb_sort_fn_list(fn_list)


def sb_upload_data(sb_page_id, archive_station_dir, sb_username,
                   sb_password=None, f_types=['.zip', '.edi', '.png', '.xml',
                                              '.mth5']):
    """
    Upload a given archive station directory to a new child item of the given
    sciencebase page.

    .. note:: iPython shells will echo your password.  Use a Python command
              shell to not have your password echoed.


    :param sb_page_id: page id of the sciencebase database to download to
    :type sb_page_id: string

    :param archive_station_dir: full path to the station directory to archive
    :type archive_station_dir: string

    :param sb_username: sciencebase username, typically your full USGS email
    :type sb_username: string

    :param sb_password: AD password
    :type sb_password: string

    :returns: child item created on the sciencebase page
    :rtype: dictionary

    :Example: ::
        >>> import mtpy.usgs.usgs_archive as archive
        >>> sb_page = 'sb_page_number'
        >>> child_item = archive.sb_upload_data(sb_page,
                                                r"/home/mt/archive_station",
                                                'jdoe@usgs.gov')
    """
    ### initialize a session
    session = sb.SbSession()

    ### login to session, note if you run this in a console your password will
    ### be visible, otherwise run from a command line > python sciencebase_upload.py
    sb_session_login(session, sb_username, sb_password)

    station = os.path.basename(archive_station_dir)

    ### File to upload
    upload_fn_list = sb_get_fn_list(archive_station_dir, f_types=f_types)

    ### check if child item is already created
    child_id = sb_locate_child_item(session, station, sb_page_id)
    ## it is faster to remove the child item and replace it all
    if child_id:
        session.delete_item(session.get_item(child_id))
        sb_action = 'Updated'

    else:
        sb_action = 'Created'

    ### make a new child item
    new_child_dict = {'title':'station {0}'.format(station),
                      'parentId':sb_page_id,
                      'summary': 'Magnetotelluric data'}
    new_child = session.create_item(new_child_dict)

    # sort list so that xml, edi, png, zip files
    # upload data
    try:
        item = session.upload_files_and_upsert_item(new_child, upload_fn_list)
    except:
        sb_session_login(session, sb_username, sb_password)
        # if you want to keep the order as read on the sb page,
        # need to reverse the order cause it sorts by upload date.
        for fn in upload_fn_list[::-1]:
            try:
                item = session.upload_file_to_item(new_child, fn)
            except:
                print('\t +++ Could not upload {0} +++'.format(fn))
                continue

    print('==> {0} child for {1}'.format(sb_action, station))

    session.logout()

    return item
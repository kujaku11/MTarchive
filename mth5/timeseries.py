# -*- coding: utf-8 -*-
"""
.. module:: timeseries
   :synopsis: Deal with MT time series

.. moduleauthor:: Jared Peacock <jpeacock@usgs.gov>
"""

#==============================================================================
# Imports
#==============================================================================
import numpy as np
import pandas as pd
import xarray as xr
import logging

from mth5 import metadata
from mth5.utils.mttime import MTime

#==============================================================================

#==============================================================================
class MTTS(object):
    """
    MT time series object that will read/write data in different formats
    including hdf5, txt, miniseed.

    The foundations are based on Pandas Python package.

    The data are store in the variable ts, which is a pandas dataframe with
    the data in the column 'data'.  This way the data can be indexed as a
    numpy array:

        >>> MTTS.ts['data'][0:256]

        or

        >>> MTTS.ts.data[0:256]

    Also, the data can be indexed by time (note needs to be exact time):

        >>> MTTS.ts['2017-05-04 12:32:00.0078125':'2017-05-05 12:35:00]

    Input ts as a numpy.ndarray or Pandas DataFrame

    ==================== ==================================================
    Metadata              Description
    ==================== ==================================================
    azimuth              clockwise angle from coordinate system N (deg)
    calibration_fn       file name for calibration data
    component            component name [ 'ex' | 'ey' | 'hx' | 'hy' | 'hz']
    coordinate_system    [ geographic | geomagnetic ]
    datum                datum of geographic location ex. WGS84
    declination          geomagnetic declination (deg)
    dipole_length        length of dipole (m)
    data_logger          data logger type
    instrument_id        ID number of instrument for calibration
    lat                  latitude of station in decimal degrees
    lon                  longitude of station in decimal degrees
    n_samples            number of samples in time series
    sampling_rate        sampling rate in samples/second
    start_time_epoch_sec start time in epoch seconds
    start_time_utc       start time in UTC
    station              station name
    units                units of time series
    ==================== ==================================================

    .. note:: Currently only supports hdf5 and text files

    ======================= ===============================================
    Method                  Description
    ======================= ===============================================
    read_hdf5               read an hdf5 file
    write_hdf5              write an hdf5 file
    write_ascii_file        write an ascii file
    read_ascii_file         read an ascii file
    ======================= ===============================================


    :Example: ::

        >>> import mtpy.core.ts as ts
        >>> import numpy as np
        >>> MTTS = ts.MTTS()
        >>> MTTS.ts = np.random.randn(1024)
        >>> MTTS.station = 'test'
        >>> MTTS.lon = 30.00
        >>> MTTS.lat = -122.00
        >>> MTTS.component = 'HX'
        >>> MTTS.units = 'counts'
        >>> MTTS.write_hdf5(r"/home/test.h5")


    """

    def __init__(self, channel_type, data, channel_metadata, **kwargs):
        self.logger = logging.getLogger('{0}.{1}'.format(__name__, 
                                                         self._class_name))
        if channel_type in ['electric']:
            self.metadata = metadata.Electric()
        elif channel_type in ['magnetic']:
            self.metadata = metadata.Magnetic()
        elif channel_type in ['auxiliary']:
            self.metadata = metadata.Channel()
        else:
            msg = ('Channel type is undefined, must be [ electric | ' + 
                   'magnetic | auxiliary ]')
            self.logger.error(msg)
            raise MTTSError(msg)
            
        if channel_metadata is not None:
            if not isinstance(channel_metadata, self.metadata):
                msg = "input metadata must be type {0} not {1}".format(
                    type(self.metadata), type(channel_metadata))
                self.logger.error(msg)
                raise MTTSError(msg)
            self.metadata = channel_metadata
            
        self._ts = xr.DataArray([1], coords=[('time', [1])])
        self.update_xarray_metadata()
        if data is not None:
            self.ts = data
        
        for key in list(kwargs.keys()):
            setattr(self, key, kwargs[key])

    ###-------------------------------------------------------------
    ## make sure some attributes have the correct data type
    # make sure that the time series is a pandas data frame
    @property
    def _class_name(self):
        return self.__class__.__name__
    
    @property
    def ts(self):
        return self._ts

    @ts.setter
    def ts(self, ts_arr):
        """
        if setting ts with a pandas data frame, make sure the data is in a
        column name 'data'
        """
        if isinstance(ts_arr, np.ndarray):
            dt = self._set_dt_index(self.start_time_utc, 
                                    self.sampling_rate,
                                    ts_arr.size)
            self._ts = xr.DataArray(ts_arr, coords=[('time', dt)])

        elif isinstance(ts_arr, pd.core.frame.DataFrame):
            try:
                dt = self._make_dt_index(self.start_time_utc, 
                                         self.sampling_rate,
                                         ts_arr['data'].size)
                self._ts = xr.DataArray(ts_arr['data'],
                                        coords=[('time', dt)])

            except AttributeError:
                msg = ("Data frame needs to have a column named `data` " +\
                       "where the time series data is stored")
                self.logger.error(msg)
                raise MTTSError(msg)
                
        elif isinstance(ts_arr, xr.DataArray):
            # TODO: need to validate the input xarray
            self._ts = ts_arr
            
        else:
            msg = ("Data type {0} not supported".format(type(ts_arr)) +\
                   ", ts needs to be a numpy.ndarray, pandas DataFrame, " +\
                   "or xarray.DataArray.")
            raise MTTSError()

        self._n_samples = self.ts.data.size
        
    def update_xarray_metadata(self):
        """
        
        :return: DESCRIPTION
        :rtype: TYPE

        """
        
        self._ts.attrs.update(self.metadata.to_dict())
        

    #--> number of samples just to make sure there is consistency
    @property
    def n_samples(self):
        """number of samples"""
        return int(self.ts.size)

    @n_samples.setter
    def n_samples(self, num_samples):
        """number of samples (int)"""
        self.logger.warning('Cannot set the number of samples')

    def _check_for_index(self):
        """
        check to see if there is an index in the time series
        """
        if len(self._ts) > 1:
            return True
        else:
            return False

    #--> sampling rate
    @property
    def sampling_rate(self):
        """sampling rate in samples/second"""
        if self._check_for_index():
            sr = 1E9/self._ts.coords.indexes['time'][0].freq.nanos
        else:
            self.logger.info("Data has not been set yet, " +
                             " sample rate is from metadata")
            sr = self.metadata.sample_rate
            if sr is None:
                sr = 0.0
        return np.round(sr, 0)

    @sampling_rate.setter
    def sampling_rate(self, sampling_rate):
        """
        sampling rate in samples/second

        type float
        """
        self.logger.warning("Cannot set sample rate.  If you want to " +
                            "change the sampling rate use method `resample`.")


    ## set time and set index
    @property
    def start_time_utc(self):
        """start time in UTC given in time format"""
        if self._check_for_index():
            mtime = MTime(self._ts.coords.indexes['time'][0].isoformat())
            return mtime.iso_str
        else:
            self.logger.info("Data not set yet, pulling start time from " +
                             "metadata.time_period.start")
            return self.metadata.time_period.start

    @start_time_utc.setter
    def start_time_utc(self, start_time):
        """
        start time of time series in UTC given in some format or a datetime
        object.

        Resets epoch seconds if the new value is not equivalent to previous
        value.

        Resets how the ts data frame is indexed, setting the starting time to
        the new start time.
        """

        if not isinstance(start_time, MTime):
            start_time = Mtime(start_time)

        self.metadata.time_period.start = start_time.iso_str
        if self._check_for_index():
            if start_time == Mtime(self.ts.coords.indexex[0].isoformat()):
                return
            else:
                new_dt = self._make_dt_coordinates(start_time,
                                                   self._sampling_rate)
                self.ts.coords['time'] = new_dt
                

        # make a time series that the data can be indexed by
        else:
            raise MTTSError('No Data to set start time for, set data first')

    ## epoch seconds
    @property
    def start_time_epoch_sec(self):
        """start time in epoch seconds"""
        if self._check_for_index():
            if isinstance(self._ts.index[0], int):
                return None
            else:
                return self.ts.index[0].timestamp()
        else:
            return None

    @start_time_epoch_sec.setter
    def start_time_epoch_sec(self, epoch_sec):
        """
        start time in epoch seconds

        Resets start_time_utc if different

        Resets how ts data frame is indexed.
        """
        try:
            epoch_sec = float(epoch_sec)
        except ValueError:
            raise MTTSError("Need to input epoch_sec as a float not {0} {1".format(type(epoch_sec), self.fn_ascii))

        dt_struct = datetime.datetime.utcfromtimestamp(epoch_sec)
        # these should be self cosistent
        try:
            if self.ts.index[0] != dt_struct:
                self.start_time_utc = dt_struct
        except IndexError:
            print('setting time')
            self.start_time_utc = dt_struct

    @property
    def stop_time_epoch_sec(self):
        """
        End time in epoch seconds
        """
        if self._check_for_index():
            if isinstance(self._ts.index[-1], int):
                return None
            else:
                return self.ts.index[-1].timestamp()
        else:
            return None

    @property
    def stop_time_utc(self):
        """
        End time in UTC
        """
        if self._check_for_index():
            if isinstance(self._ts.index[-1], int):
                return None
            else:
                return self._ts.index[-1].isoformat()

    def _make_dt_coordinates(self, start_time, sampling_rate, n_samples):
        """
        get the date time index from the data

        :param start_time: start time in time format
        :type start_time: string
        """
        if len(self.ts) == 0:
            return
        
        if start_time is None:
            self.logger.warning('Start time is None, skipping calculating index')
            return
        
        if not isinstance(start_time, MTime):
            if isinstance(start_time, (str, int, float)):
                start_time = MTime(start_time)
            elif isinstance(start_time, (np.datatime64, np.ndarray)):
                start_time = MTime(str(start_time))
            else:
                msg = "Type {0} is not understood for `start_time`".format(
                    type(start_time))
                self.logger.error(msg)
                raise MTTSError(msg)

        dt_freq = '{0:.0f}N'.format(1. / (sampling_rate) * 1E9)

        dt_index = pd.date_range(start=start_time.iso_utc.split('+', 1)[0],
                                 periods=n_samples,
                                 freq=dt_freq)

        return dt_index

    # decimate data
    def decimate(self, dec_factor=1):
        """
        decimate the data by using scipy.signal.decimate

        :param dec_factor: decimation factor
        :type dec_factor: int

        * refills ts.data with decimated data and replaces sampling_rate

        """
        pass
        # # be sure the decimation factor is an integer
        # dec_factor = int(dec_factor)

        # if dec_factor > 1:
        #     if dec_factor > 8:
        #         n_dec = np.log2(dec_factor)/np.log2(8)
        #         dec_list = [8] * int(n_dec) + [int(2**(3 * n_dec % 1))]
        #         decimated_data = signal.decimate(self.ts.data, 8, n=8)
        #         for dec in dec_list[1:]:
        #             if dec == 0:
        #                 break
        #             decimated_data = signal.decimate(decimated_data,
        #                                              dec,
        #                                              n=8)
        #     else:
        #         decimated_data = signal.decimate(self.ts.data, dec_factor, n=8)
        #     start_time = str(self.start_time_utc)
        #     self.ts = decimated_data
        #     self.sampling_rate /= float(dec_factor)
        #     self._set_dt_index(start_time, self.sampling_rate)

    def low_pass_filter(self, low_pass_freq=15, cutoff_freq=55):
        """
        low pass the data

        :param low_pass_freq: low pass corner in Hz
        :type low_pass_freq: float

        :param cutoff_freq: cut off frequency in Hz
        :type cutoff_freq: float

        * filters ts.data
        """
        pass
        # self.ts = mtfilter.low_pass(self.ts.data,
        #                             low_pass_freq,
        #                             cutoff_freq,
        #                             self.sampling_rate)
        
    # def plot_spectra(self, spectra_type='welch', **kwargs):
    #     """
    #     Plot spectra using the spectral type

    #     .. note:: Only spectral type supported is welch

    #     :param spectra_type: [ 'welch' ]
    #     :type spectral_type: string

    #     :Example: ::

    #         >>> ts_obj = mtts.MTTS()
    #         >>> ts_obj.read_hdf5(r"/home/MT/mt01.h5")
    #         >>> ts_obj.plot_spectra()

    #     """

    #     s = Spectra()
    #     param_dict = {}
    #     if spectra_type == 'welch':
    #         param_dict['fs'] = kwargs.pop('sampling_rate',
    #                                                    self.sampling_rate)
    #         param_dict['nperseg'] = kwargs.pop('nperseg', 2**12)
    #         s.compute_spectra(self.ts.data, spectra_type, **param_dict)

#==============================================================================
# Error classes
#==============================================================================
class MTTSError(Exception):
    pass

# #==============================================================================
# #  spectra
# #==============================================================================
# class Spectra(object):
#     """
#     compute spectra of time series
#     """

#     def __init__(self, **kwargs):
#         self.spectra_type = 'welch'

#     def compute_spectra(self, data, spectra_type, **kwargs):
#         """
#         compute spectra according to input type
#         """

#         if spectra_type.lower() == 'welch':
#             self.welch_method(data, **kwargs)

#     def welch_method(self, data, plot=True, **kwargs):
#         """
#         Compute the spectra using the Welch method, which is an average
#         spectra of the data.  Computes short time window of length nperseg and
#         averages them to reduce noise.

#         Arguments
#         ------------

#         """

#         f, p = signal.welch(data, **kwargs)

#         if plot:
#             fig = plt.figure()
#             ax = fig.add_subplot(1, 1, 1)
#             ax.loglog(f, p, lw=1.5)
#             ax.set_xlabel('Frequency (Hz)',
#                           fontdict={'size':10, 'weight':'bold'})
#             ax.set_ylabel('Power (dB)',
#                           fontdict={'size':10, 'weight':'bold'})
#             ax.axis('tight')
#             ax.grid(which='both')

#             plt.show()

#         return f, p





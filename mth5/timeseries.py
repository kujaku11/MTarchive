# -*- coding: utf-8 -*-
"""
.. module:: timeseries
   :synopsis: Deal with MT time series

:copyright:
    Jared Peacock (jpeacock@usgs.gov)
    
:license: 
    MIT
"""

# ==============================================================================
# Imports
# ==============================================================================
import numpy as np
import pandas as pd
import xarray as xr
import logging

from mth5 import metadata
from mth5.utils.mttime import MTime

# ==============================================================================

# ==============================================================================
class MTTS(object):
    """
    
    .. note:: Assumes equally spaced samples from the start time.
    
    
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
    sample_rate          sample rate in samples/second
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


    :Example: 

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

    def __init__(self, channel_type, data=None, channel_metadata=None, **kwargs):
        self.logger = logging.getLogger("{0}.{1}".format(__name__, self._class_name))

        # get correct metadata class
        if channel_type in ["electric"]:
            self.metadata = metadata.Electric()
        elif channel_type in ["magnetic"]:
            self.metadata = metadata.Magnetic()
        elif channel_type in ["auxiliary"]:
            self.metadata = metadata.Channel()
        else:
            msg = (
                "Channel type is undefined, must be [ electric | "
                + "magnetic | auxiliary ]"
            )
            self.logger.error(msg)
            raise MTTSError(msg)

        if channel_metadata is not None:
            if isinstance(channel_metadata, type(self.metadata)):
                self.metadata.from_dict(channel_metadata.to_dict())
                self.logger.debug(
                    "Loading from metadata class {0}".format(type(self.metadata))
                )
            elif isinstance(channel_metadata, dict):
                self.metadata.from_dict(channel_metadata)
                self.logger.debug("Loading from metadata dict")

            else:
                msg = "input metadata must be type {0} or dict, not {1}".format(
                    type(self.metadata), type(channel_metadata)
                )
                self.logger.error(msg)
                raise MTTSError(msg)

        self._ts = xr.DataArray([1], coords=[("time", [1])])
        self.update_xarray_metadata()
        if data is not None:
            self.ts = data

        for key in list(kwargs.keys()):
            setattr(self, key, kwargs[key])

    def __str__(self):
        return self.ts.__str__()

    def __repr__(self):
        return self.ts.__repr__()

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
            dt = self._make_dt_coordinates(self.start, self.sample_rate, ts_arr.size)
            self._ts = xr.DataArray(ts_arr, coords=[("time", dt)])
            self.update_xarray_metadata()

        elif isinstance(ts_arr, pd.core.frame.DataFrame):
            try:
                dt = self._make_dt_index(
                    self.start_time_utc, self.sample_rate, ts_arr["data"].size
                )
                self._ts = xr.DataArray(ts_arr["data"], coords=[("time", dt)])

            except AttributeError:
                msg = (
                    "Data frame needs to have a column named `data` "
                    + "where the time series data is stored"
                )
                self.logger.error(msg)
                raise MTTSError(msg)

        elif isinstance(ts_arr, xr.DataArray):
            # TODO: need to validate the input xarray
            self._ts = ts_arr
            meta_dict = dict([(k, v) for k, v in ts_arr.attrs.items()])
            self.metadata.from_dict({self.metadata.type: meta_dict})

        else:
            msg = (
                "Data type {0} not supported".format(type(ts_arr))
                + ", ts needs to be a numpy.ndarray, pandas DataFrame, "
                + "or xarray.DataArray."
            )
            raise MTTSError()

    def update_xarray_metadata(self):
        """
        
        :return: DESCRIPTION
        :rtype: TYPE

        """
        self.metadata.time_period.start = self.start_time_utc
        self.metadata.time_period.end = self.end_time_utc
        self.metadata.sample_rate = self.sample_rate

        self._ts.attrs.update(self.metadata.to_dict()[self.metadata._class_name])

    # --> number of samples just to make sure there is consistency
    @property
    def n_samples(self):
        """number of samples"""
        return int(self.ts.size)

    @n_samples.setter
    def n_samples(self, n_samples):
        """number of samples (int)"""
        self.logger.warning(
            "Cannot set the number of samples, " + "Use `MTTS.resample`"
        )

    def _check_for_index(self):
        """
        check to see if there is an index in the time series
        """
        if len(self._ts) > 1:
            return True
        else:
            return False

    # --> sample rate
    @property
    def sample_rate(self):
        """sample rate in samples/second"""
        if self._check_for_index():
            sr = 1e9 / self._ts.coords.indexes["time"][0].freq.nanos
        else:
            self.logger.info(
                "Data has not been set yet, " + " sample rate is from metadata"
            )
            sr = self.metadata.sample_rate
            if sr is None:
                sr = 0.0
        return np.round(sr, 0)

    @sample_rate.setter
    def sample_rate(self, sample_rate):
        """
        sample rate in samples/second

        type float
        """
        self.metadata.sample_rate = sample_rate
        self.logger.warning(
            "Setting MTTS.metadata.sample_rate. "
            + "If you want to change the time series sample"
            + " rate use method `resample`."
        )

    ## set time and set index
    @property
    def start(self):
        """MTime object"""
        if self._check_for_index():
            return MTime(self._ts.coords.indexes["time"][0].isoformat())
        else:
            self.logger.info(
                "Data not set yet, pulling start time from "
                + "metadata.time_period.start"
            )
            return MTime(self.metadata.time_period.start)

    @start.setter
    def start(self, start_time):
        """
        start time of time series in UTC given in some format or a datetime
        object.

        Resets epoch seconds if the new value is not equivalent to previous
        value.

        Resets how the ts data frame is indexed, setting the starting time to
        the new start time.
        """

        if not isinstance(start_time, MTime):
            start_time = MTime(start_time)

        self.metadata.time_period.start = start_time.iso_str
        if self._check_for_index():
            if start_time == MTime(self.ts.coords.indexes["time"][0].isoformat()):
                return
            else:
                new_dt = self._make_dt_coordinates(
                    start_time, self.sample_rate, self.n_samples
                )
                self.ts.coords["time"] = new_dt

        # make a time series that the data can be indexed by
        else:
            self.logger.warning("No data, just updating metadata start")

    ## epoch seconds
    @property
    def start_time_utc(self):
        """start time in UTC given in time format"""
        return self.start.iso_str

    @start_time_utc.setter
    def start_time_utc(self):
        self.logger.warning(
            "Cannot set `start_time_utc`. " + "Use >>> MTTS.start = new_time"
        )

    @property
    def start_time_epoch_sec(self):
        """start time in epoch seconds"""
        return self.start.epoch_seconds

    @start_time_epoch_sec.setter
    def start_time_epoch_sec(self):
        self.logger.warning(
            "Cannot set `start_time_epoch_seconds`. " + "Use >>> MTTS.start = new_time"
        )

    @property
    def end(self):
        """MTime object"""
        if self._check_for_index():
            return MTime(self._ts.coords.indexes["time"][-1].isoformat())
        else:
            self.logger.info(
                "Data not set yet, pulling end time from " + "metadata.time_period.end"
            )
            return MTime(self.metadata.time_period.end)

    @end.setter
    def end(self, end_time):
        """
        end time of time series in UTC given in some format or a datetime
        object.

        Resets epoch seconds if the new value is not equivalent to previous
        value.

        Resets how the ts data frame is indexed, setting the starting time to
        the new start time.
        """
        self.logger.warning(
            "Cannot set `end`. If you want a slice, then "
            + "use MTTS.ts.sel['time'=slice(start, end)]"
        )

        # if not isinstance(end_time, MTime):
        #     end_time = MTime(end_time)

        # self.metadata.time_period.end = end_time.iso_str
        # if self._check_for_index():
        #     if start_time == MTime(self.ts.coords.indexes['time'][0].isoformat()):
        #         return
        #     else:
        #         new_dt = self._make_dt_coordinates(start_time,
        #                                            self.sample_rate,
        #                                            self.n_samples)
        #         self.ts.coords['time'] = new_dt

        # # make a time series that the data can be indexed by
        # else:
        #     self.logger.warning("No data, just updating metadata start")

    @property
    def end_time_epoch_sec(self):
        """
        End time in epoch seconds
        """
        return self.end.epoch_seconds

    @end_time_epoch_sec.setter
    def end_time_epoch_sec(self):
        self.logger.warning(
            "Cannot set `end_time_epoch_seconds`. " + "Use >>> MTTS.end = new_time"
        )

    @property
    def end_time_utc(self):
        """
        End time in UTC
        """
        return self.end.iso_str

    @end_time_utc.setter
    def end_time_utc(self):
        self.logger.warning(
            "Cannot set `end_time_utc`. " + "Use >>> MTTS.end = new_time"
        )

    def _make_dt_coordinates(self, start_time, sample_rate, n_samples):
        """
        get the date time index from the data

        :param start_time: start time in time format
        :type start_time: string
        """
        if len(self.ts) == 0:
            return

        if sample_rate in [0, None]:
            msg = (
                f"Need to input a valid sample rate. Not {sample_rate}, "
                + "returning a time index assuming a sample rate of 1"
            )
            self.logger.warning(msg)
            sample_rate = 1

        if start_time is None:
            msg = (
                f"Need to input a valid sample rate. Not {start_time}, "
                + "returning a time index with start time of "
                + "1980-01-01T00:00:00"
            )
            self.logger.warning(msg)
            start_time = "1980-01-01T00:00:00"

        if n_samples < 1:
            msg = f"Need to input a valid n_samples. Not {n_samples}"
            self.logger.error(msg)
            raise ValueError(msg)

        if not isinstance(start_time, MTime):
            start_time = MTime(start_time)

        dt_freq = "{0:.0f}N".format(1.0e9 / (sample_rate))

        dt_index = pd.date_range(
            start=start_time.iso_str.split("+", 1)[0], periods=n_samples, freq=dt_freq
        )

        return dt_index

    def get_slice(self, start, end):
        """
        Get a slice from the time series given a start and end time.
        
        Looks for >= start & <= end
        
        Uses loc to be exact with milliseconds
        
        :param start: DESCRIPTION
        :type start: TYPE
        :param end: DESCRIPTION
        :type end: TYPE
        :return: DESCRIPTION
        :rtype: TYPE

        """

        if not isinstance(start, MTime):
            start = MTime(start)
        if not isinstance(end, MTime):
            end = MTime(end)

        new_ts = self.ts.loc[
            (self.ts.indexes["time"] >= start.iso_no_tz)
            & (self.ts.indexes["time"] <= end.iso_no_tz)
        ]
        new_ts.attrs["time_period.start"] = new_ts.coords.indexes["time"][0].isoformat()
        new_ts.attrs["time_period.end"] = new_ts.coords.indexes["time"][-1].isoformat()

        return new_ts

    # decimate data
    def resample(self, dec_factor=1, inplace=False):
        """
        decimate the data by using scipy.signal.decimate

        :param dec_factor: decimation factor
        :type dec_factor: int

        * refills ts.data with decimated data and replaces sample_rate

        """

        new_dt_freq = "{0:.0f}N".format(1e9 / (self.sample_rate / dec_factor))

        new_ts = self.ts.resample(time=new_dt_freq).nearest(tolerance=new_dt_freq)
        new_ts.attrs["sample_rate"] = self.sample_rate / dec_factor
        self.metadata.sample_rate = new_ts.attrs["sample_rate"]

        if inplace:
            self.ts = new_ts

        else:
            new_ts.attrs.update(self.metadata.to_dict()[self.metadata._class_name])
            # return new_ts
            return MTTS(self.metadata.type, data=new_ts, metadata=self.metadata)

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
        #                             self.sample_rate)

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
    #         param_dict['fs'] = kwargs.pop('sample_rate',
    #                                                    self.sample_rate)
    #         param_dict['nperseg'] = kwargs.pop('nperseg', 2**12)
    #         s.compute_spectra(self.ts.data, spectra_type, **param_dict)


# ==============================================================================
# Error classes
# ==============================================================================
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

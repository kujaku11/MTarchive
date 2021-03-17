# -*- coding: utf-8 -*-
"""
==================
MTH5
==================

This module deals with reading and writing MTH5 files, which are HDF5 files
developed for magnetotelluric (MT) data.  The code is based on h5py and
attributes use JSON encoding.

.. note:: Currently the convenience methods support read only.  
          Working on developing the write convenience methods.

Created on Sun Dec  9 20:50:41 2018

@author: J. Peacock
"""

# =============================================================================
# Imports
# =============================================================================
import os
import datetime
import time
import json
import dateutil

import h5py
import pandas as pd
import numpy as np

# =============================================================================
#  global parameters
# =============================================================================
dt_fmt = "%Y-%m-%dT%H:%M:%S.%f %Z"

# ==============================================================================
# Need a dummy utc time zone for the date time format
# ==============================================================================
class UTC(datetime.tzinfo):
    """
    An class to hold information about UTC
    """

    def utcoffset(self, df):
        return datetime.timedelta(hours=0)

    def dst(self, df):
        return datetime.timedelta(0)

    def tzname(self, df):
        return "UTC"


class Generic(object):
    """
    A generic class that is common to most of the Metadata objects
    
    Includes:
        * to_json
        * from_json
    """

    def __init__(self, **kwargs):

        for key, value in kwargs.items():
            setattr(self, key, value)

    def to_dict(self):
        """
        return a dictionary
        """
        rdict = {}
        for key, value in self.__dict__.items():
            rdict[f"{self.__class__.__name__}.{key}"] = value

        return rdict

    def to_json(self):
        """
        Write a json string from a given object, taking into account other
        class objects contained within the given object.
        """
        return to_json(self)

    def from_json(self, json_str):
        """
        read in a json string and update attributes of an object

        :param json_str: json string
        :type json_str: string
    
        """
        from_json(json_str, self)


# ==============================================================================
# Location class, be sure to put locations in decimal degrees, and note datum
# ==============================================================================
class Location(Generic):
    """
    location details including:
        * latitude
        * longitude
        * elevation
        * datum
        * coordinate_system
        * declination
    """

    def __init__(self, **kwargs):
        super(Location, self).__init__()
        self.datum = "WGS84"
        self.declination = None
        self.declination_epoch = None

        self._elevation = None
        self._latitude = None
        self._longitude = None

        self.elev_units = "m"
        self.coordinate_system = "Geographic North"

        for key, value in kwargs.items():
            setattr(self, key, value)

    @property
    def latitude(self):
        return self._latitude

    @latitude.setter
    def latitude(self, lat):
        self._latitude = self._assert_lat_value(lat)

    @property
    def longitude(self):
        return self._longitude

    @longitude.setter
    def longitude(self, lon):
        self._longitude = self._assert_lon_value(lon)

    @property
    def elevation(self):
        return self._elevation

    @elevation.setter
    def elevation(self, elev):
        self._elevation = self._assert_elevation_value(elev)

    def _assert_lat_value(self, latitude):
        """
        Make sure the latitude value is in decimal degrees, if not change it.
        And that the latitude is within -90 < lat > 90.
        
        :param latitude: latitude in decimal degrees or other format
        :type latitude: float or string
        """
        if latitude in [None, "None"]:
            return None
        try:
            lat_value = float(latitude)

        except TypeError:
            return None

        except ValueError:
            lat_value = self._convert_position_str2float(latitude)

        if abs(lat_value) >= 90:
            print("==> The lat_value =", lat_value)
            raise ValueError("|Latitude| > 90, unacceptable!")

        return lat_value

    def _assert_lon_value(self, longitude):
        """
        Make sure the longitude value is in decimal degrees, if not change it.
        And that the latitude is within -180 < lat > 180.
        
        :param latitude: longitude in decimal degrees or other format
        :type latitude: float or string
        """
        if longitude in [None, "None"]:
            return None
        try:
            lon_value = float(longitude)

        except TypeError:
            return None

        except ValueError:
            lon_value = self._convert_position_str2float(longitude)

        if abs(lon_value) >= 180:
            print("==> The longitude_value =", lon_value)
            raise ValueError("|Longitude| > 180, unacceptable!")

        return lon_value

    def _assert_elevation_value(self, elevation):
        """
        make sure elevation is a floating point number
        
        :param elevation: elevation as a float or string that can convert
        :type elevation: float or str
        """

        try:
            elev_value = float(elevation)
        except (ValueError, TypeError):
            elev_value = 0.0

        return elev_value

    def _convert_position_float2str(self, position):
        """
        Convert position float to a string in the format of DD:MM:SS.

        :param position: decimal degrees of latitude or longitude
        :type position: float
                           
        :returns: latitude or longitude in format of DD:MM:SS.ms
        """

        assert type(position) is float, "Given value is not a float"

        deg = int(position)
        sign = 1
        if deg < 0:
            sign = -1

        deg = abs(deg)
        minutes = (abs(position) - deg) * 60.0
        # need to round seconds to 4 decimal places otherwise machine precision
        # keeps the 60 second roll over and the string is incorrect.
        sec = np.round((minutes - int(minutes)) * 60.0, 4)
        if sec >= 60.0:
            minutes += 1
            sec = 0

        if int(minutes) == 60:
            deg += 1
            minutes = 0

        position_str = "{0}:{1:02.0f}:{2:05.2f}".format(
            sign * int(deg), int(minutes), sec
        )

        return position_str

    def _convert_position_str2float(self, position_str):
        """
        Convert a position string in the format of DD:MM:SS to decimal degrees
        
         :param position: latitude or longitude om DD:MM:SS.ms
        :type position: float
                           
        :returns: latitude or longitude as a float
        """

        if position_str in [None, "None"]:
            return None

        p_list = position_str.split(":")
        if len(p_list) != 3:
            raise ValueError(
                "{0} not correct format, should be DD:MM:SS".format(position_str)
            )

        deg = float(p_list[0])
        minutes = self._assert_minutes(float(p_list[1]))
        sec = self._assert_seconds(float(p_list[2]))

        # get the sign of the position so that when all are added together the
        # position is in the correct place
        sign = 1
        if deg < 0:
            sign = -1

        position_value = sign * (abs(deg) + minutes / 60.0 + sec / 3600.0)

        return position_value

    def _assert_minutes(self, minutes):
        assert (
            0 <= minutes < 60.0
        ), "minutes needs to be <60 and >0, currently {0:.0f}".format(minutes)

        return minutes

    def _assert_seconds(self, seconds):
        assert (
            0 <= seconds < 60.0
        ), "seconds needs to be <60 and >0, currently {0:.3f}".format(seconds)
        return seconds


# ==============================================================================
# Site details
# ==============================================================================
class Site(Location):
    """
    Information on the site, including location, id, etc.

    Holds the following information:

    ================= =========== =============================================
    Attributes         Type        Explanation
    ================= =========== =============================================
    aqcuired_by       string       name of company or person whom aqcuired the
                                   data.
    id                string       station name
    Location          object       Holds location information, lat, lon, elev
                      Location     datum, easting, northing see Location class
    start_date        string       YYYY-MM-DD start date of measurement
    stop_date         string       YYYY-MM-DD end date of measurement
    year_collected    string       year data collected
    survey            string       survey name
    project           string       project name
    run_list          string       list of measurment runs ex. [mt01a, mt01b]
    ================= =========== =============================================

    More attributes can be added by inputing a key word dictionary

    >>> Site(**{'state':'Nevada', 'Operator':'MTExperts'})

    """

    def __init__(self, **kwargs):
        super(Site, self).__init__()
        self.acquired_by = Person()
        self._start_date = None
        self._stop_date = None
        self.id = None
        self.survey = None
        self._attrs_list = [
            "acquired_by",
            "start_date",
            "stop_date",
            "id",
            "survey",
            "latitude",
            "longitude",
            "elevation",
            "datum",
            "declination",
            "declination_epoch",
            "elev_units",
            "coordinate_system",
        ]

        for key, value in kwargs.items():
            setattr(self, key, value)

    @property
    def start_date(self):
        try:
            return self._start_date.strftime(dt_fmt)
        except (TypeError, AttributeError):
            return None

    @start_date.setter
    def start_date(self, start_date):
        self._start_date = dateutil.parser.parse(start_date)
        if self._start_date.tzname() is None:
            self._start_date = self._start_date.replace(tzinfo=UTC())

    @property
    def stop_date(self):
        try:
            return self._stop_date.strftime(dt_fmt)
        except (TypeError, AttributeError):
            return None

    @stop_date.setter
    def stop_date(self, stop_date):
        self._stop_date = dateutil.parser.parse(stop_date)
        if self._stop_date.tzname() is None:
            self._stop_date = self._stop_date.replace(tzinfo=UTC())


# ==============================================================================
# Field Notes
# ==============================================================================
class FieldNotes(Generic):
    """
    Field note information.


    Holds the following information:

    ================= =========== =============================================
    Attributes         Type        Explanation
    ================= =========== =============================================
    data_quality      DataQuality notes on data quality
    electrode         Instrument      type of electrode used
    data_logger       Instrument      type of data logger
    magnetometer      Instrument      type of magnetotmeter
    ================= =========== =============================================

    More attributes can be added by inputing a key word dictionary

    >>> FieldNotes(**{'electrode_ex':'Ag-AgCl 213', 'magnetometer_hx':'102'})
    """

    def __init__(self, **kwargs):
        super(FieldNotes, self).__init__()
        self._electric_channel = {
            "length": None,
            "azimuth": None,
            "chn_num": None,
            "units": "mV",
            "gain": 1,
            "contact_resistance": 1,
        }
        self._magnetic_channel = {
            "azimuth": None,
            "chn_num": None,
            "units": "mV",
            "gain": 1,
        }

        self.data_quality = DataQuality()
        self.data_logger = Instrument()
        self.electrode_ex = Instrument(**self._electric_channel)
        self.electrode_ey = Instrument(**self._electric_channel)

        self.magnetometer_hx = Instrument(**self._magnetic_channel)
        self.magnetometer_hy = Instrument(**self._magnetic_channel)
        self.magnetometer_hz = Instrument(**self._magnetic_channel)

        for key, value in kwargs.items():
            setattr(self, key, value)


# ==============================================================================
# Instrument
# ==============================================================================
class Instrument(Generic):
    """
    Information on an instrument that was used.

    Holds the following information:

    ================= =========== =============================================
    Attributes         Type        Explanation
    ================= =========== =============================================
    id                string      serial number or id number of data logger
    manufacturer      string      company whom makes the instrument
    type              string      Broadband, long period, something else
    ================= =========== =============================================

    More attributes can be added by inputing a key word dictionary

    >>> Instrument(**{'ports':'5', 'gps':'time_stamped'})
    """

    def __init__(self, **kwargs):
        super(Instrument, self).__init__()
        self.id = None
        self.manufacturer = None
        self.type = None

        for key, value in kwargs.items():
            setattr(self, key, value)

    def get_length(self):
        """
        get dipole length
        """

        try:
            return np.sqrt((self.x2 - self.x) ** 2 + (self.y2 - self.y) ** 2)
        except AttributeError:
            return 0


# ==============================================================================
# Data Quality
# ==============================================================================
class DataQuality(Generic):
    """
    Information on data quality.

    Holds the following information:

    ================= =========== =============================================
    Attributes         Type        Explanation
    ================= =========== =============================================
    comments          string      comments on data quality
    good_from_period  float       minimum period data are good
    good_to_period    float       maximum period data are good
    rating            int         [1-5]; 1 = poor, 5 = excellent
    warrning_comments string      any comments on warnings in the data
    warnings_flag     int         [0-#of warnings]
    ================= =========== =============================================

    More attributes can be added by inputing a key word dictionary

    >>> DataQuality(**{'time_series_comments':'Periodic Noise'})
    """

    def __init__(self, **kwargs):
        super(DataQuality, self).__init__()
        self.comments = None
        self.rating = None
        self.warnings_comments = None
        self.warnings_flag = 0
        self.author = None

        for key, value in kwargs.items():
            setattr(self, key, value)


# ==============================================================================
# Citation
# ==============================================================================
class Citation(Generic):
    """
    Information for a citation.

    Holds the following information:

    ================= =========== =============================================
    Attributes         Type        Explanation
    ================= =========== =============================================
    author            string      Author names
    title             string      Title of article, or publication
    journal           string      Name of journal
    doi               string      DOI number (doi:10.110/sf454)
    year              int         year published
    ================= =========== =============================================

    More attributes can be added by inputing a key word dictionary

    >>> Citation(**{'volume':56, 'pages':'234--214'})
    """

    def __init__(self, **kwargs):
        super(Citation, self).__init__()
        self.author = None
        self.title = None
        self.journal = None
        self.volume = None
        self.doi = None
        self.year = None

        for key, value in kwargs.items():
            setattr(self, key, value)


# ==============================================================================
# Copyright
# ==============================================================================
class Copyright(Generic):
    """
    Information of copyright, mainly about how someone else can use these
    data. Be sure to read over the conditions_of_use.

    Holds the following information:

    ================= =========== =============================================
    Attributes         Type        Explanation
    ================= =========== =============================================
    citation          Citation    citation of published work using these data
    conditions_of_use string      conditions of use of these data
    release_status    string      release status [ open | public | proprietary]
    ================= =========== =============================================

    More attributes can be added by inputing a key word dictionary

    >>> Copyright(**{'owner':'University of MT', 'contact':'Cagniard'})
    """

    def __init__(self, **kwargs):
        super(Copyright, self).__init__()
        self.citation = Citation()
        self.conditions_of_use = "".join(
            [
                "All data and metadata for this survey are ",
                "available free of charge and may be copied ",
                "freely, duplicated and further distributed ",
                "provided this data set is cited as the ",
                "reference. While the author(s) strive to ",
                "provide data and metadata of best possible ",
                "quality, neither the author(s) of this data ",
                "set, not IRIS make any claims, promises, or ",
                "guarantees about the accuracy, completeness, ",
                "or adequacy of this information, and expressly ",
                "disclaim liability for errors and omissions in ",
                "the contents of this file. Guidelines about ",
                "the quality or limitations of the data and ",
                "metadata, as obtained from the author(s), are ",
                "included for informational purposes only.",
            ]
        )
        self.release_status = None
        self.additional_info = None

        for key, value in kwargs.items():
            setattr(self, key, value)


# ==============================================================================
# Provenance
# ==============================================================================
class Provenance(Generic):
    """
    Information of the file history, how it was made

    Holds the following information:

    ====================== =========== ========================================
    Attributes             Type        Explanation
    ====================== =========== ========================================
    creation_time          string      creation time of file YYYY-MM-DD,hh:mm:ss
    creating_application   string      name of program creating the file
    creator                Person      person whom created the file
    submitter              Person      person whom is submitting file for
                                       archiving
    ====================== =========== ========================================

    More attributes can be added by inputing a key word dictionary

    >>> Provenance(**{'archive':'IRIS', 'reprocessed_by':'grad_student'})
    """

    def __init__(self, **kwargs):
        super(Provenance, self).__init__()
        self.creation_time = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())
        self.creating_application = "MTH5"
        self.creator = Person()
        self.submitter = Person()

        for key, value in kwargs.items():
            setattr(self, key, value)


# ==============================================================================
# Person
# ==============================================================================
class Person(Generic):
    """
    Information for a person

    Holds the following information:

    ================= =========== =============================================
    Attributes         Type        Explanation
    ================= =========== =============================================
    email             string      email of person
    name              string      name of person
    organization      string      name of person's organization
    organization_url  string      organizations web address
    ================= =========== =============================================

    More attributes can be added by inputing a key word dictionary

    >>> Person(**{'phone':'650-888-6666'})
    """

    def __init__(self, **kwargs):
        super(Person, self).__init__()
        self.email = None
        self.name = None
        self.organization = None
        self.organization_url = None

        for key, value in kwargs.items():
            setattr(self, key, value)


# ==============================================================================
# Software
# ==============================================================================
class Software(Generic):
    """
    software
    """

    def __init__(self, **kwargs):
        super(Software, self).__init__()
        self.name = None
        self.version = None
        self.author = Person()

        for key, value in kwargs.items():
            setattr(self, key, value)


# =============================================================================
# schedule
# =============================================================================
class Schedule(object):
    """
    Container for a single schedule item

    :Metadata keywords:

          ===================== =======================================
          name                  description
          ===================== =======================================
          station               station name
          latitude              latitude of station (decimal degrees)
          longitude             longitude of station (decimal degrees)
          hx_azimuth            azimuth of HX (degrees from north=0)
          hy_azimuth            azimuth of HY (degrees from north=0)
          hz_azimuth            azimuth of HZ (degrees from horizon=0)
          ex_azimuth            azimuth of EX (degrees from north=0)
          ey_azimuth            azimuth of EY (degrees from north=0)
          hx_sensor             instrument id number for HX
          hy_sensor             instrument id number for HY
          hz_sensor             instrument id number for HZ
          ex_sensor             instrument id number for EX
          ey_sensor             instrument id number for EY
          ex_length             dipole length (m) for EX
          ey_length             dipole length (m) for EX
          ex_num                channel number of EX
          ey_num                channel number of EX
          hx_num                channel number of EX
          hy_num                channel number of EX
          hz_num                channel number of EX
          instrument_id         instrument id
          ===================== =======================================
    """

    def __init__(self, name=None, meta_df=None):

        self.ex = None
        self.ey = None
        self.hx = None
        self.hy = None
        self.hz = None
        self.dt_index = None
        self.name = name

        self._comp_list = ["ex", "ey", "hx", "hy", "hz"]
        self._attrs_list = [
            "name",
            "start_time",
            "stop_time",
            "start_seconds_from_epoch",
            "stop_seconds_from_epoch",
            "n_samples",
            "n_channels",
            "sampling_rate",
        ]

        self.meta_keys = [
            "station",
            "latitude",
            "longitude",
            "hx_azimuth",
            "hy_azimuth",
            "hz_azimuth",
            "ex_azimuth",
            "ey_azimuth",
            "hx_sensor",
            "hy_sensor",
            "hz_sensor",
            "ex_sensor",
            "ey_sensor",
            "ex_length",
            "ey_length",
            "ex_num",
            "ey_num",
            "hx_num",
            "hy_num",
            "hz_num",
            "instrument_id",
        ]

        # self.ts_df = time_series_dataframe
        self.meta_df = meta_df

    @property
    def start_time(self):
        """
        Start time in UTC string format
        """
        return "{0}".format(self.dt_index[0].strftime(dt_fmt))

    @property
    def stop_time(self):
        """
        Stop time in UTC string format
        """
        return "{0}".format(self.dt_index[-1].strftime(dt_fmt))

    @property
    def start_seconds_from_epoch(self):
        """
        Start time in epoch seconds
        """
        return self.dt_index[0].to_datetime64().astype(np.int64) / 1e9

    @property
    def stop_seconds_from_epoch(self):
        """
        sopt time in epoch seconds
        """
        return self.dt_index[-1].to_datetime64().astype(np.int64) / 1e9

    @property
    def n_channels(self):
        """
        number of channels
        """

        return len(self.comp_list)

    @property
    def sampling_rate(self):
        """
        sampling rate
        """
        return np.round(1.0e9 / self.dt_index[0].freq.nanos, decimals=1)

    @property
    def n_samples(self):
        """
        number of samples
        """
        return self.dt_index.shape[0]

    @property
    def comp_list(self):
        """
        component list for the given schedule
        """
        return [comp for comp in self._comp_list if getattr(self, comp) is not None]

    def make_dt_index(self, start_time, sampling_rate, stop_time=None, n_samples=None):
        """
        make time index array

        .. note:: date-time format should be YYYY-M-DDThh:mm:ss.ms UTC

        :param start_time: start time
        :type start_time: string

        :param end_time: end time
        :type end_time: string

        :param sampling_rate: sampling_rate in samples/second
        :type sampling_rate: float
        """

        # set the index to be UTC time
        dt_freq = "{0:.0f}N".format(1.0 / (sampling_rate) * 1e9)
        if stop_time is not None:
            dt_index = pd.date_range(
                start=start_time, end=stop_time, freq=dt_freq, closed="left", tz="UTC"
            )
        elif n_samples is not None:
            dt_index = pd.date_range(
                start=start_time.split("UTC")[0],
                periods=n_samples,
                freq=dt_freq,
                tz="UTC",
            )
        else:
            raise ValueError("Need to input either stop_time or n_samples")

        return dt_index

    def from_dataframe(self, ts_dataframe):
        """
        update attributes from a pandas dataframe.

        Dataframe should have columns:
            * ex
            * ey
            * hx
            * hy
            * hz
        and should be indexed by time.

        :param ts_dataframe: dataframe holding the data
        :type ts_datarame: pandas.DataFrame
        """
        try:
            assert isinstance(ts_dataframe, pd.DataFrame) is True
        except AssertionError:
            raise TypeError(
                "ts_dataframe is not a pandas.DataFrame object.\n",
                "ts_dataframe is {0}".format(type(ts_dataframe)),
            )

        for col in ts_dataframe.columns:
            try:
                setattr(self, col.lower(), ts_dataframe[col])
            except AttributeError:
                print("\t xxx skipping {0} xxx".format(col))
        self.dt_index = ts_dataframe.index

        return

    def from_ascii(self, ascii_object):
        """
        From an MT ascii object
        """
        translator = {
            "ChnNum": "num",
            "ChnID": "comp",
            "InstrumentID": "sensor",
            "Azimuth": "azimuth",
            "Dipole_Length": "length",
        }
        start = datetime.datetime.strptime(
            ascii_object.AcqStartTime, "%Y-%m-%dT%H:%M:%S %Z"
        ).timestamp()

        self.from_dataframe(ascii_object.ts)
        meta_dict = {}
        for chn_num, entry in ascii_object.channel_dict.items():
            comp = entry.pop("ChnID").lower()
            if "e" in comp:
                meta_dict[f"{comp}_length"] = entry.pop("Dipole_Length")
            else:
                entry.pop("Dipole_Length")
            for key, value in entry.items():
                meta_dict[f"{comp}_{translator[key]}"] = value
            meta_dict[f"{comp}_nsamples"] = getattr(self, comp).size
            meta_dict[f"{comp}_ndiff"] = 0
            meta_dict[f"{comp}_std"] = getattr(self, comp).std()
            meta_dict[f"{comp}_start"] = start
        meta_dict["station"] = f"{ascii_object.SurveyID}{ascii_object.SiteID}"
        meta_dict["latitude"] = ascii_object.SiteLatitude
        meta_dict["longitude"] = ascii_object.SiteLongitude
        meta_dict["elev"] = ascii_object.SiteElevation
        meta_dict["instrument_id"] = entry["InstrumentID"]
        meta_dict["start_date"] = ascii_object.AcqStartTime
        meta_dict["stop_date"] = ascii_object.AcqStopTime
        meta_dict["notes"] = None
        meta_dict["mtft_file"] = False
        meta_dict["n_chan"] = ascii_object.Nchan
        meta_dict["n_samples"] = ascii_object.AcqNumSmp
        meta_dict["collected_by"] = "USGS"
        meta_dict["sampling_rate"] = ascii_object.AcqSmpFreq

        self.meta_df = pd.Series(meta_dict)

    def from_mth5(self, mth5_obj, name):
        """
        make a schedule object from mth5 file

        :param mth5_obj: an open mth5 object
        :type mth5_obj: mth5.MTH5 open object

        :param name: name of schedule to use
        :type name: string
        """
        mth5_schedule = mth5_obj[name]

        self.name = name

        for comp in self._comp_list:
            try:
                setattr(self, comp, mth5_schedule[comp])
            except KeyError:
                print("\t xxx No {0} data for {1} xxx".format(comp, self.name))
                continue

        self.dt_index = self.make_dt_index(
            mth5_schedule.attrs["start_time"],
            mth5_schedule.attrs["sampling_rate"],
            n_samples=mth5_schedule.attrs["n_samples"],
        )
        assert self.dt_index.shape[0] == getattr(self, self.comp_list[0]).shape[0]
        return

    def from_numpy_array(self, schedul_np_array, start_time, stop_time, sampling_rate):
        """
        TODO
        update attributes from a numpy array
        """
        pass

    def write_metadata_csv(self, csv_dir):
        """
        write metadata to a csv file
        """
        if self.meta_df is None:
            self.meta_df = pd.Series(
                dict([(k, getattr(self, k)) for k in self._attrs_list])
            )
        csv_fn = self._make_csv_fn(csv_dir)
        self.meta_df.to_csv(csv_fn, header=False)

        return csv_fn

    def _make_csv_fn(self, csv_dir):
        """
        create csv file name from data.
        """
        if not isinstance(self.meta_df, pd.Series):
            raise ValueError(
                "meta_df is not a Pandas Series, {0}".format(type(self.meta_df))
            )
        csv_fn = "{0}_{1}_{2}_{3}.csv".format(
            self.name,
            self.dt_index[0].strftime("%Y%m%d"),
            self.dt_index[0].strftime("%H%M%S"),
            int(self.sampling_rate),
        )

        return os.path.join(csv_dir, csv_fn)


# =============================================================================
# Calibrations
# =============================================================================
class Calibration(Generic):
    """
    container for insturment calibrations

    Each instrument should be a separate class

    Metadata should be:
        * instrument_id
        * calibration_date
        * calibration_person
        * units
    """

    def __init__(self, name=None):
        super(Calibration, self).__init__()
        self.name = name
        self.instrument_id = None
        self.units = None
        self.calibration_date = None
        self.calibration_person = Person()
        self.frequency = None
        self.real = None
        self.imaginary = None
        self._col_list = ["frequency", "real", "imaginary"]
        self._attrs_list = [
            "name",
            "instrument_id",
            "units",
            "calibration_date",
            "calibration_person",
        ]

    def from_dataframe(self, cal_dataframe, name=None):
        """
        updated attributes from a pandas DataFrame

        :param cal_dataframe: dataframe with columns frequency, real, imaginary
        :type cal_dataframe: pandas.DataFrame

        """
        assert isinstance(cal_dataframe, pd.DataFrame) is True

        if name is not None:
            self.name = name

        for col in cal_dataframe.columns:
            setattr(self, col, cal_dataframe[col])

    def from_numpy_array(self, cal_np_array, name=None):
        """
        update attributes from a numpy array

        :param cal_np_array: array of values for calibration, see below
        :type cal_np_array: numpy.ndarray

        if array is a numpy structured array names need to be:
            * frequency
            * real
            * imaginary

        if array is just columns, needs to be ordered:
            * frequency (index 0)
            * real (index 1)
            * imaginary (index 2)

        """
        if name is not None:
            self.name = name

        ### assume length of 1 is a structured array
        if len(cal_np_array.shape) == 1:
            assert cal_np_array.dtype.names == ("frequency", "real", "imaginary")
            for key in cal_np_array.dtype.names:
                setattr(self, key, cal_np_array[key])

        ### assume an unstructured array (f, r, i)
        if len(cal_np_array.shape) == 2 and cal_np_array.shape[0] == 3:
            for ii, key in enumerate(["frequency", "real", "imaginary"]):
                setattr(self, key, cal_np_array[ii, :])

        return

    def from_mth5(self, mth5_obj, name):
        """
        update attribues from mth5 file
        """
        self.name = name
        for key in mth5_obj["/calibrations/{0}".format(self.name)].keys():
            setattr(self, key, mth5_obj["/calibrations/{0}/{1}".format(self.name, key)])

        ### read in attributes
        self.from_json(
            mth5_obj["/calibrations/{0}".format(self.name)].attrs["metadata"]
        )

    def from_csv(self, cal_csv, name=None, header=False):
        """
        Read a csv file that is in the format frequency,real,imaginary
        
        :param cal_csv: full path to calibration csv file
        :type cal_csv: string
        
        :param name: instrument id
        :type name: string
        
        :param header: boolean if there is a header in the csv file
        :type header: [ True | False ]
        
        """
        if not header:
            cal_df = pd.read_csv(cal_csv, header=None, names=self._col_list)
        else:
            cal_df = pd.read_csv(cal_csv, names=self._col_list)

        if name is not None:
            self.name
        self.from_dataframe(cal_df)


# =============================================================================
# MT HDF5 file
# =============================================================================
class MTH5(object):
    """
    MT HDF5 file

    Class object to deal with reading and writing an MTH5 file.

    ======================= ===================================================
    Attribute               Description
    ======================= ===================================================
    copyright               Copyright object containing information on
                            copyright information
    field_notes             FieldNotes object containing information on how
                            the data was collected
    mth5_fn                 full path to MTH5 file
    mth5_obj                HDF5 object from h5py
    provenance              Provenance object containing information on when
                            and by whom the data was collected
    site                    Site object containing information about the
                            location of the station
    software                Software object containing information on the
                            software used to make the file
    schedule_##             Schedule object where ## is the number of the
                            schedule if a MTH5 file was read in
    calibration_##          Calibration object where ## is the component of
                            the calibration
    ======================= ===================================================

    .. seealso:: mth5.Copyright, mth5.FieldNotes, mth5.Provenance, mth5.Site
                 mth5.Software, mth5.Schedule, mth5.Calibration, h5py

    ============================ ==============================================
    Method                       Description
    ============================ ==============================================
    open_mth5                    load in a MTH5 file
    close_mth5                   flushes any changes and closes MTH5 file
    add_schedule                 add a schedule data set
    add_calibration              add instrument calibration to /root/calibrations
    write_metadata               write root metadata
    update_metadata_from_cfg     update metadata attributes from a cfg file
    update_metadata_from_series  update metadata attributes from pandas series
    h5_is_write                  check if MTH5 file is open and writeable
    ============================ ==============================================

    * Example: Load MTH5 File
    
    >>> import mth5.mth5 as mth5
    >>> data = mth5.MTH5.open_mth5(r"/home/mtdata/mt01.mth5")

    * Example: Update metadata from cfg file
    
    >>> data = mth5.MTH5()
    >>> # read in configuration file to update attributes
    >>> data.update_metadata_from_cfg(r"/home/survey_mth5.cfg")
    >>> data.write_metadata()
    
    * Example: Add schedule to MTH5 File
    
    >>> schedule_obj = mth5.Schedule()
    >>> # make schedule object from a pandas dataframe
    >>> import pandas as pd
    >>> sdf = df = pd.DataFrame(np.random.random((256*3600+1, 5)),
    ...                         columns=['ex', 'ey', 'hx', 'hy', 'hz'],
    ...                         index=pd.date_range(start='2018-01-01T01:00:00',
    ...                                             end='2018-01-01T02:00:00',
    ...                                             freq='{0:.0f}N'.format(1./256.*1E9)))
    >>> data.schedule_01 = schedule_obj.from_dataframe(sdf, 'schedule_01')
        
    * Example: Add calibration from structured numpy array

    >>> import numpy as np
    >>> cal = mth5.Calibration()
    >>> cal_dtype = [(name, np.float) for name in ['frequency', 'real', 'imaginary']]
    >>> cal.from_numpy_array(np.zeros(20), dtype=cal_dtype)
    >>> cal.frequency = np.logspace(-3, 3, 20)
    >>> cal.real = np.random.random(20)
    >>> cal.imaginary = np.random.random(20)
    >>> cal.name = 'hx'
    >>> cal.instrument_id = 2284
    >>> cal.calibration_date = '2018-01-01'
    >>> cal.calibration_person.name = 'tester name'
    >>> cal.calibration_person.organization = 'tester company'
    >>> data.calibrations.calibration_hx = data.add_calibration(cal, 'hx')
    
    * Example: Update data
    
    >>> data.schedule_01.ex[0:10] = np.nan
    >>> data.calibration_hx[...] = np.logspace(-4, 4, 20)
    
    .. note:: if replacing an entire array with a new one you need to use [...]
              otherwise the data will not be updated.  
              
    .. warning:: You can only replace entire arrays with arrays of the same 
                 size.  Otherwise you need to delete the existing data and 
                 make a new dataset.  
                 
    .. seealso:: https://www.hdfgroup.org/ and h5py()
    """

    def __init__(self):
        self.mth5_fn = None
        self.mth5_obj = None
        self.site = Site()
        self.field_notes = FieldNotes()
        self.copyright = Copyright()
        self.software = Software()
        self.provenance = Provenance()

    def h5_is_write(self):
        """
        check to see if the hdf5 file is open and writeable
        """
        if isinstance(self.mth5_obj, h5py.File):
            try:
                if "w" in self.mth5_obj.mode or "+" in self.mth5_obj.mode:
                    return True
                elif self.mth5_obj.mode == "r":
                    return False
            except ValueError:
                return False
        return False

    def open_mth5(self, mth5_fn):
        """
        write an mth5 file
        """
        self.mth5_fn = mth5_fn

        if os.path.isfile(self.mth5_fn):
            print("*** Overwriting {0}".format(mth5_fn))

        self.mth5_obj = h5py.File(self.mth5_fn, "w")
        self.mth5_obj.create_group("calibrations")

    def close_mth5(self):
        """
        close mth5 file to make sure everything is flushed to the file
        """

        self.mth5_obj.flush()
        self.write_metadata()
        self.mth5_obj.close()

    def write_metadata(self):
        """
        Write metadata to the HDf5 file as json strings under the headings:
            * site
            * field_notes
            * copyright
            * provenance
            * software
        """
        if self.h5_is_write():
            for attr in ["site", "field_notes", "copyright", "provenance", "software"]:
                self.mth5_obj.attrs.update(getattr(self, attr).to_dict())

    def add_schedule(self, schedule_obj, compress=True):
        """
        add a schedule object to the HDF5 file

        :param schedule_obj: container holding the time series data as a
                             pandas.DataFrame with columns as components
                             and indexed by time.
        :type schedule_obj: mtf5.Schedule object
        
        :param bool compress: [ True | False ] to internally compress the data
        
        .. note:: will name the schedule according to schedule_obj.name.  
                  Should be schedule_## where ## is the order of the schedule
                  as a 2 character digit [0-9][0-9] 
        """

        if self.h5_is_write():
            ### create group for schedule action
            schedule = self.mth5_obj.require_group(schedule_obj.name)
            ### add metadata
            for attr in schedule_obj._attrs_list:
                schedule.attrs[attr] = getattr(schedule_obj, attr)

            ### add datasets for each channel
            for comp in schedule_obj.comp_list:
                if compress:
                    schedule.create_dataset(
                        comp.lower(),
                        data=getattr(schedule_obj, comp),
                        compression="gzip",
                        compression_opts=9,
                    )
                else:
                    schedule.create_dataset(
                        comp.lower(), data=getattr(schedule_obj, comp)
                    )
            ### set the convenience attribute to the schedule
            setattr(self, schedule_obj.name, Schedule())
            getattr(self, schedule_obj.name).from_mth5(self.mth5_obj, schedule_obj.name)

        else:
            raise MTH5Error("{0} is not writeable".format(self.mth5_fn))

    def remove_schedule(self, schedule_name):
        """
        Remove a schedule item given schedule name.
        
        :param str schedule_name: schedule name verbatim of the one you want
                                  to delete.
                                  
        .. note:: This does not free up memory, it just simply deletes the 
                  link to the schedule item.  See
                  http://docs.h5py.org/en/stable/high/group.html.  The best
                  method would be to build a different file without the data
                  your are trying to delete.
        """
        if self.h5_is_write():
            try:
                delattr(self, schedule_name)
                del self.mth5_obj["/{0}".format(schedule_name)]
            except AttributeError:
                print("Could not find {0}, not an attribute".format(schedule_name))

        else:
            raise MTH5Error("File not open")

    def add_calibration(self, calibration_obj, compress=True):
        """
        add calibrations for sensors

        :param calibration_obj: calibration object that has frequency, real,
                                imaginary attributes
        :type calibration_obj: mth5.Calibration

        """

        if self.h5_is_write():
            cal = self.mth5_obj["/calibrations"].require_group(calibration_obj.name)
            cal.attrs["metadata"] = calibration_obj.to_json()
            for col in calibration_obj._col_list:
                if compress:
                    cal.create_dataset(
                        col.lower(),
                        data=getattr(calibration_obj, col),
                        compression="gzip",
                        compression_opts=9,
                    )
                else:
                    cal.create_dataset(col.lower(), data=getattr(calibration_obj, col))

            ### set the convenience attribute to the calibration
            setattr(self, calibration_obj.name, Calibration())
            getattr(self, calibration_obj.name).from_mth5(
                self.mth5_obj, calibration_obj.name
            )
        else:
            raise MTH5Error("{0} is not writeable".format(self.mth5_fn))

    def remove_calibration(self, calibration_name):
        """
        Remove a calibration item given calibration name.
        
        :param str calibration_name: calibration name verbatim of the one you
                                     want to delete.
                                  
        .. note:: This does not free up memory, it just simply deletes the 
                  link to the schedule item.  See
                  http://docs.h5py.org/en/stable/high/group.html.  The best
                  method would be to build a different file without the data
                  your are trying to delete.
        """
        if self.h5_is_write():
            try:
                delattr(self, calibration_name)
                del self.mth5_obj["calibrations/{0}".format(calibration_name)]
            except AttributeError:
                print("Could not find {0}, not an attribute".format(calibration_name))
        else:
            raise MTH5Error("File not open")

    def update_schedule_metadata(self):
        """
        update schedule metadata on the HDF file
        """

        for key in self.__dict__.keys():
            if "sch" in key:
                for attr in getattr(self, key)._attrs_list:
                    value = getattr(getattr(self, key), attr)
                    self.mth5_obj[key].attrs[attr] = value

    def read_mth5(self, mth5_fn):
        """
        Read MTH5 file and update attributes
        
        :param str mth5_fn: full path to mth5 file
        """

        if not os.path.isfile(mth5_fn):
            raise MTH5Error("Could not find {0}, check path".format(mth5_fn))

        self.mth5_fn = mth5_fn
        ### read in file and give write permissions in case the user wants to
        ### change any parameters
        self.mth5_obj = h5py.File(self.mth5_fn, "r+")
        for attr in ["site", "field_notes", "copyright", "provenance", "software"]:
            getattr(self, attr).from_json(self.mth5_obj.attrs[attr])

        for key in self.mth5_obj.keys():
            if "sch" in key:
                setattr(self, key, Schedule())
                getattr(self, key).from_mth5(self.mth5_obj, key)
            elif "cal" in key:
                try:
                    for ckey in self.mth5_obj[key].keys():
                        m_attr = "calibration_{0}".format(ckey)
                        setattr(self, m_attr, Calibration())
                        getattr(self, m_attr).from_mth5(self.mth5_obj, ckey)
                except KeyError:
                    print("No Calibration Data")

    def update_metadata_from_cfg(self, mth5_cfg_fn):
        """
        read a configuration file for all the mth5 attributes

        :param mth5_cfg_fn: full path to configuration file for mth5 file
        :type mth5_cfg_fn: string

        The configuration file has the format::
            
            ###===================================================###
            ### Metadata Configuration File for Science Base MTH5 ###
            ###===================================================###

            ### Site information --> mainly for location
            site.id = MT Test
            site.coordinate_system = Geomagnetic North
            site.datum = WGS84
            site.declination = 15.5
            site.declination_epoch = 1995
            site.elevation = 1110
            site.elev_units = meters
            site.latitude = 40.12434
            site.longitude = -118.345
            site.survey = Test
            site.start_date = 2018-05-07T20:10:00.0
            site.end_date = 2018-07-07T10:20:30.0
            #site._date_fmt = None

            ### Field Notes --> for instrument setup
            # Data logger information
            field_notes.data_logger.id = ZEN_test
            field_notes.data_logger.manufacturer = Zonge
            field_notes.data_logger.type = 32-Bit 5-channel GPS synced
        """
        usgs_str = "U.S. Geological Survey"
        # read in the configuration file
        with open(mth5_cfg_fn, "r") as fid:
            lines = fid.readlines()

        for line in lines:
            # skip comment lines
            if line.find("#") == 0 or len(line.strip()) < 2:
                continue
            # make a key = value pair
            key, value = [item.strip() for item in line.split("=", 1)]

            if value == "usgs_str":
                value = usgs_str
            if value.find("[") >= 0 and value.find("]") >= 0 and value.find("<") != 0:
                value = value.replace("[", "").replace("]", "")
                value = [v.strip() for v in value.split(",")]
            if value.find(".") > 0:
                try:
                    value = float(value)
                except ValueError:
                    pass
            else:
                try:
                    value = int(value)
                except ValueError:
                    pass

            # if there is a dot, meaning an object with an attribute separate
            if key.count(".") == 0:
                setattr(self, key, value)
            elif key.count(".") == 1:
                obj, obj_attr = key.split(".")
                setattr(getattr(self, obj), obj_attr, value)
            elif key.count(".") == 2:
                obj, obj_attr_01, obj_attr_02 = key.split(".")
                setattr(getattr(getattr(self, obj), obj_attr_01), obj_attr_02, value)

    def update_metadata_from_series(self, station_series, update_time=False):
        """
        Update metadata from a pandas.Series with old keys as columns:
            * station
            * latitude
            * longitude
            * elevation
            * declination
            * start_date
            * stop_date
            * datum
            * coordinate_system
            * units
            * instrument_id
            * ex_azimuth
            * ex_length
            * ex_sensor
            * ex_num
            * ey_azimuth
            * ey_length
            * ey_sensor
            * ey_num
            * hx_azimuth
            * hx_sensor
            * hx_num
            * hy_azimuth
            * hy_sensor
            * hy_num
            * hz_azimuth
            * hz_sensor
            * hz_num
            * quality

        :param station_series: pandas.Series with the above index values
        :type station_series: pandas.Series
        
        :param update_time: boolean to update the start and stop time
        :type update_time: [ True | False ]
        """
        if isinstance(station_series, pd.DataFrame):
            station_series = station_series.iloc[0]

        assert isinstance(
            station_series, pd.Series
        ), "station_series is not a pandas.Series"

        for key in station_series.index:
            value = getattr(station_series, key)
            if key in self.site._attrs_list:
                setattr(self.site, key, value)
            elif key == "start_date":
                if not update_time:
                    continue
                attr = key
                setattr(self.site, attr, value)
            elif key == "stop_date":
                if not update_time:
                    continue
                attr = "end_date"
                setattr(self.site, attr, value)
            elif key == "instrument_id":
                self.field_notes.data_logger.id = value
            elif key == "quality":
                self.field_notes.data_quality.rating = value
            elif key == "notes":
                self.field_notes.data_quality.comments = value
            elif key == "station":
                self.site.id = value
            elif key == "units":
                self.site.elev_units = value
            elif key[0:2] in ["ex", "ey", "hx", "hy", "hz"]:
                comp = key[0:2]
                attr = key.split("_")[1]
                if attr == "num":
                    attr = "chn_num"
                if attr == "sensor":
                    attr = "id"
                if "e" in comp:
                    setattr(
                        getattr(self.field_notes, "electrode_{0}".format(comp)),
                        attr,
                        value,
                    )
                elif "h" in comp:
                    setattr(
                        getattr(self.field_notes, "magnetometer_{0}".format(comp)),
                        attr,
                        value,
                    )


# =============================================================================
#  read and write json for attributes
# =============================================================================
class NumpyEncoder(json.JSONEncoder):
    """
    Need to encode numpy ints and floats for json to work
    """

    def default(self, obj):
        if isinstance(
            obj,
            (
                np.int_,
                np.intc,
                np.intp,
                np.int8,
                np.int16,
                np.int32,
                np.int64,
                np.uint8,
                np.uint16,
                np.uint32,
                np.uint64,
            ),
        ):
            return int(obj)

        elif isinstance(obj, (np.float_, np.float16, np.float32, np.float64)):
            return float(obj)

        elif isinstance(obj, (np.ndarray)):
            return obj.tolist()

        return json.JSONEncoder.default(self, obj)


def to_json(obj):
    """
    write a json string from a given object, taking into account other class
    objects contained within the given object.

    :param obj: class object to transform into string
    """
    if isinstance(obj, (Site, Calibration)):
        keys = obj._attrs_list
    else:
        keys = obj.__dict__.keys()

    obj_dict = {}
    for key in keys:
        if key.find("_") == 0:
            continue
        value = getattr(obj, key)

        if isinstance(
            value,
            (
                FieldNotes,
                Instrument,
                DataQuality,
                Citation,
                Provenance,
                Person,
                Software,
            ),
        ):
            obj_dict[key] = {}
            for o_key, o_value in value.__dict__.items():
                if o_key.find("_") == 0:
                    continue
                obj_dict[key][o_key] = o_value

        elif isinstance(value, (Site, Calibration)):
            obj_dict[key] = {}
            for o_key in value._attrs_list:
                if o_key.find("_") == 0:
                    continue
                obj_dict[key][o_key] = getattr(obj, o_key)
        else:
            obj_dict[key] = value

    return json.dumps(obj_dict, cls=NumpyEncoder)


def from_json(json_str, obj):
    """
    read in a json string and update attributes of an object

    :param json_str: json string
    :type json_str:string

    :param obj: class object to update
    :type obj: class object

    :returns obj:
    """

    obj_dict = json.loads(json_str)

    for key, value in obj_dict.items():
        if isinstance(value, dict):
            for o_key, o_value in value.items():
                setattr(getattr(obj, key), o_key, o_value)
        else:
            setattr(obj, key, value)

    return obj


# ==============================================================================
#             Error
# ==============================================================================
class MTH5Error(Exception):
    pass

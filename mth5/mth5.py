# -*- coding: utf-8 -*-
"""
Class Object to deal with MTF5 files

Created on Sun Dec  9 20:50:41 2018

@author: jpeacock
"""

# =============================================================================
# Imports
# =============================================================================
import os
import datetime
import dateutil
import time
import json
import h5py
import pandas as pd
import numpy as np
import mtpy.utils.gis_tools as gis_tools
        
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
    
# ==============================================================================
# Location class, be sure to put locations in decimal degrees, and note datum
# ==============================================================================
class Location(object):
    """
    location details
    """

    def __init__(self, **kwargs):
        self.datum = 'WGS84'
        self.declination = None
        self.declination_epoch = None

        self._elevation = None
        self._latitude = None
        self._longitude = None

        self._northing = None
        self._easting = None
        self.utm_zone = None
        self.elev_units = 'm'
        self.coordinate_system = 'Geographic North'

        for key in kwargs.keys():
            setattr(self, key, kwargs[key])

    @property
    def latitude(self):
        return self._latitude

    @latitude.setter
    def latitude(self, lat):
        self._latitude = gis_tools.assert_lat_value(lat)

    @property
    def longitude(self):
        return self._longitude

    @longitude.setter
    def longitude(self, lon):
        self._longitude = gis_tools.assert_lon_value(lon)

    @property
    def elevation(self):
        return self._elevation

    @elevation.setter
    def elevation(self, elev):
        self._elevation = gis_tools.assert_elevation_value(elev)

    @property
    def easting(self):
        return self._easting

    @easting.setter
    def easting(self, easting):
        try:
            self._easting = float(easting)
        except TypeError:
            self._easting = None

    @property
    def northing(self):
        return self._northing

    @northing.setter
    def northing(self, northing):
        try:
            self._northing = float(northing)
        except TypeError:
            self._northing = None

    def project_location2utm(self):
        """
        project location coordinates into meters given the reference ellipsoid,
        for now that is constrained to WGS84

        Returns East, North, Zone
        """
        # need to convert datum to string, gdal doesn't like unicode apparently
        utm_point = gis_tools.project_point_ll2utm(self.latitude,
                                                   self.longitude,
                                                   datum=str(self.datum))

        self.easting = utm_point[0]
        self.northing = utm_point[1]
        self.utm_zone = utm_point[2]

    def project_location2ll(self):
        """
        project location coordinates into meters given the reference ellipsoid,
        for now that is constrained to WGS84

        Returns East, North, Zone
        """
        ll_point = gis_tools.project_point_utm2ll(self.easting,
                                                  self.northing,
                                                  self.utm_zone,
                                                  datum=str(self.datum))

        self.latitude = ll_point[0]
        self.longitude = ll_point[1]


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
    end_date          string       YYYY-MM-DD end date of measurement
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
        self._end_date = None
        self.id = None
        self.survey = None
        self._date_fmt = '%Y-%m-%dT%H:%M:%S.%f %Z'
        self._site_attrs = ['acquired_by',
                            'start_date',
                            'end_date',
                            'id',
                            'survey',
                            'latitude',
                            'longitude',
                            'elevation',
                            'datum',
                            'declination',
                            'declination_epoch',
                            'elev_units',
                            'coordinate_system']

        for key in kwargs.keys():
            setattr(self, key, kwargs[key])
            
    @property
    def start_date(self):
        try:
            return datetime.datetime.strftime(self._start_date, self._date_fmt)
        except TypeError:
            return None
    
    @start_date.setter
    def start_date(self, start_date):
        self._start_date = dateutil.parser.parse(start_date)
        if self._start_date.tzname() is None:
            self._start_date = self._start_date.replace(tzinfo=UTC())

    @property
    def end_date(self):
        try:
            return datetime.datetime.strftime(self._end_date, self._date_fmt)
        except TypeError:
            return None
    
    @end_date.setter
    def end_date(self, end_date):
        self._end_date = dateutil.parser.parse(end_date)
        if self._end_date.tzname() is None:
            self._end_date = self._end_date.replace(tzinfo=UTC())
            
    def to_json(self):
        """
        write json string to put into attributes
        """
        return to_json(self)
    
    def from_json(self, site_json):
        """
        read in json file for site information
        """
        from_json(site_json, self)

# ==============================================================================
# Field Notes
# ==============================================================================
class FieldNotes(object):
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
        self._electric_channel = {'length':None, 
                                  'azimuth':None,
                                  'chn_num':None,
                                  'units':'mV',
                                  'gain':1, 
                                  'contact_resistance':1}
        self._magnetic_channel = {'azimuth':None,
                                  'chn_num':None, 
                                  'units':'mV', 
                                  'gain':1}
        
        self.data_quality = DataQuality()
        self.data_logger = Instrument()
        self.electrode_ex = Instrument(**self._electric_channel)
        self.electrode_ey = Instrument(**self._electric_channel)

        self.magnetometer_hx = Instrument(**self._magnetic_channel)
        self.magnetometer_hy = Instrument(**self._magnetic_channel)
        self.magnetometer_hz = Instrument(**self._magnetic_channel)
        
        for key in kwargs.keys():
            setattr(self, key, kwargs[key])
            
    def to_json(self):
        """
        write json of FieldNotes
        """
        return to_json(self)
    
    def from_json(self, field_json):
        """
        read a json string of field notes and update attributes
        """
        from_json(field_json, self)
                
# ==============================================================================
# Instrument
# ==============================================================================
class Instrument(object):
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
        self.id = None
        self.manufacturer = None
        self.type = None

        for key in kwargs.keys():
            setattr(self, key, kwargs[key])
            
    def get_length(self):
        """
        get dipole length
        """
        
        try:
            return np.sqrt((self.x2 - self.x)**2 + (self.y2 - self.y)**2)
        except AttributeError:
            return 0


# ==============================================================================
# Data Quality
# ==============================================================================
class DataQuality(object):
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

    >>>DataQuality(**{'time_series_comments':'Periodic Noise'})
    """

    def __init__(self, **kwargs):
        self.comments = None
        self.rating = None
        self.warnings_comments = None
        self.warnings_flag = 0
        self.author = None

        for key in kwargs.keys():
            setattr(self, key, kwargs[key])
            
    def to_json(self):
        """
        write json of attributes
        """
        return to_json(self)
    
    def from_json(self, dq_json):
        """
        read data quality json string and update attributes
        """
        from_json(dq_json, self)

# ==============================================================================
# Citation
# ==============================================================================
class Citation(object):
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
        self.author = None
        self.title = None
        self.journal = None
        self.volume = None
        self.doi = None
        self.year = None

        for key in kwargs.keys():
            setattr(self, key, kwargs[key])

    def to_json(self):
        """
        write json of attributes
        """
        return to_json(self)
    
    def from_json(self, cite_json):
        """
        read data quality json string and update attributes
        """
        from_json(cite_json, self)

# ==============================================================================
# Copyright
# ==============================================================================
class Copyright(object):
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
        self.citation = Citation()
        self.conditions_of_use = ''.join(['All data and metadata for this survey are ',
                                          'available free of charge and may be copied ',
                                          'freely, duplicated and further distributed ',
                                          'provided this data set is cited as the ',
                                          'reference. While the author(s) strive to ',
                                          'provide data and metadata of best possible ',
                                          'quality, neither the author(s) of this data ',
                                          'set, not IRIS make any claims, promises, or ',
                                          'guarantees about the accuracy, completeness, ',
                                          'or adequacy of this information, and expressly ',
                                          'disclaim liability for errors and omissions in ',
                                          'the contents of this file. Guidelines about ',
                                          'the quality or limitations of the data and ',
                                          'metadata, as obtained from the author(s), are ',
                                          'included for informational purposes only.'])
        self.release_status = None
        self.additional_info = None
        for key in kwargs.keys():
            setattr(self, key, kwargs[key])
            
    def to_json(self):
        """
        write json of attributes
        """
        return to_json(self)
    
    def from_json(self, cr_json):
        """
        read copyright json string and update attributes
        """
        from_json(cr_json, self)

# ==============================================================================
# Provenance
# ==============================================================================
class Provenance(object):
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
        self.creation_time = time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime())
        self.creating_application = 'MTH5'
        self.creator = Person()
        self.submitter = Person()

        for key in kwargs.keys():
            setattr(self, key, kwargs[key])
            
    def to_json(self):
        """
        write json of attributes
        """
        return to_json(self)
    
    def from_json(self, prov_json):
        """
        read copyright json string and update attributes
        """
        from_json(prov_json, self)

# ==============================================================================
# Person
# ==============================================================================
class Person(object):
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
        self.email = None
        self.name = None
        self.organization = None
        self.organization_url = None

        for key in kwargs.keys():
            setattr(self, key, kwargs[key])
            
    def to_json(self):
        """
        write json of attributes
        """
        return to_json(self)
    
    def from_json(self, person_json):
        """
        read person json string and update attributes
        """
        from_json(person_json, self)

# ==============================================================================
# Processing
# ==============================================================================
class Processing(object):
    """
    Information for a processing

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

    >>> Person(**{'phone':'888-867-5309'})
    """

    def __init__(self, **kwargs):
        self.Software = Software()
        self.notes = None
        self.processed_by = None
        self.sign_convention = 'exp(+i \omega t)'
        self.remote_reference = None
        self.RemoteSite = Site()

        for key in kwargs.keys():
            setattr(self, key, kwargs[key])


class Software(object):
    """
    software
    """

    def __init__(self, **kwargs):
        self.name = None
        self.version = None
        self.author = Person()

        for key in kwargs:
            setattr(self, key, kwargs[key])
            
    def to_json(self):
        """
        write json of attributes
        """
        return to_json(self)
    
    def from_json(self, soft_json):
        """
        read software json string and update attributes
        """
        from_json(soft_json, self)
        
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
        
        self._comp_list = ['ex', 'ey', 'hx', 'hy', 'hz']
        self._attr_list = ['start_time',
                           'stop_time',
                           'start_seconds_from_epoch',
                           'stop_seconds_from_epoch',
                           'n_samples',
                           'n_channels',
                           'sampling_rate']
        
        #self.ts_df = time_series_dataframe
        self.meta_df = meta_df

    @property
    def start_time(self):
        """
        Start time in UTC string format
        """
        return '{0} UTC'.format(self.dt_index[0].isoformat())

    @property
    def stop_time(self):
        """
        Stop time in UTC string format
        """
        return '{0} UTC'.format(self.dt_index[-1].isoformat())
    
    @property
    def start_seconds_from_epoch(self):
        """
        Start time in epoch seconds
        """
        return self.dt_index[0].to_datetime64().astype(np.int64)/1e9
    
    @property
    def stop_seconds_from_epoch(self):
        """
        sopt time in epoch seconds
        """
        return self.dt_index[-1].to_datetime64().astype(np.int64)/1e9

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
        return np.round(1.0e9/self.dt_index[0].freq.nanos, decimals=1)

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
        return [comp for comp in self._comp_list
                if getattr(self, comp) is not None]
    
    def make_dt_index(self, start_time, sampling_rate, stop_time=None, 
                      n_samples=None):
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
        dt_freq = '{0:.0f}N'.format(1./(sampling_rate)*1E9)
        if stop_time is not None:
            dt_index = pd.date_range(start=start_time,
                                     end=stop_time,
                                     freq=dt_freq, 
                                     closed='left')
        elif n_samples is not None:
            dt_index = pd.date_range(start=start_time,
                                     periods=n_samples,
                                     freq=dt_freq)
        else:
            raise ValueError('Need to input either stop_time or n_samples')
        
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
            raise TypeError('ts_dataframe is not a pandas.DataFrame object.\n',
                            'ts_dataframe is {0}'.format(type(ts_dataframe)))
        
        for col in ts_dataframe.columns:
            try:
                setattr(self, col.lower(), ts_dataframe[col])
            except AttributeError:
                print("\t xxx skipping {0} xxx".format(col))
        self.dt_index = ts_dataframe.index
        
        return
    
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
                print('\t xxx No {0} data xxx'.format(comp))
                continue
        
        
        self.dt_index = self.make_dt_index(mth5_schedule.attrs['start_time'],
                                           mth5_schedule.attrs['sampling_rate'],
                                           n_samples=mth5_schedule.attrs['n_samples'])
        assert self.dt_index.shape[0] == getattr(self, self.comp_list[0]).shape[0]
        return 
    
    def from_numpy_array(self, schedul_np_array, start_time, stop_time, 
                         sampling_rate):
        """
        TODO
        update attributes from a numpy array
        """
        pass
        
        
    def write_metadata_csv(self, csv_dir):
        """
        write metadata to a csv file
        """
        
        csv_fn = self._make_csv_fn(csv_dir)
        self.meta_df.to_csv(csv_fn)
        
        return csv_fn
            
    def _make_csv_fn(self, csv_dir):
        if not isinstance(self.meta_df, pd.Series):
            raise ValueError('meta_df is not a Pandas Series, {0}'.format(type(self.meta_df)))
        csv_fn = '{0}_{1}_{2}_{3}.csv'.format(self.meta_df.station,
                                              self.ts_df.index[0].strftime('%Y%m%d'),
                                              self.ts_df.index[1].strftime('%H%M%S'),
                                              int(self.sampling_rate))
        
        return os.path.join(csv_dir, csv_fn)
    
# =============================================================================
# Calibrations
# =============================================================================
class Calibration(object):
    """
    container for insturment calibrations
    
    Each instrument should be a separate class
    
    Metadata should be:
        * instrument_id
        * calibration_date
        * calibration_person
        * units
    """
    
    def __int__(self, name=None):
        self.name = name
        self.instrument_id = None
        self.units = None
        self.calibration_date = None
        self.calibration_person = Person()
        self.frequency = None
        self.real = None
        self.imaginary = None
        self._col_list = ['frequency', 'real', 'imaginary']
        
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
            assert cal_np_array.dtype.names == ('frequency', 'real', 'imaginary')
            for key in cal_np_array.dtype.names:
                setattr(self, key, cal_np_array[key])
        
        ### assume an unstructured array (f, r, i)
        if len(cal_np_array.shape) == 2 and cal_np_array.shape[0] == 3:
            for ii, key in enumerate(['frequency', 'real', 'imaginary']):
                setattr(self, key, cal_np_array[ii, :])
            
        return 
    
    def to_json(self):
        """
        write json string to put into attributes
        """
        return to_json(self)
    
    def from_json(self, cal_json):
        """
        read in json file for site information
        """
        from_json(cal_json, self)
    
# =============================================================================
# MT HDF5 file
# =============================================================================
class MTH5(object):
    """
    MT HDF5 file
    """

    def __init__(self, **kwargs):
        self.mth5_fn = None
        self.mth5_obj = None
        self.site = Site()
        self.field_notes = FieldNotes()
        self.copyright = Copyright()
        self.software = Software()
        self.provenance = Provenance()
        
    def h5_is_write(self):
        """
        """
        if isinstance(self.mth5_obj, h5py.File):
            if 'w' in self.mth5_obj.mode or '+' in self.mth5_obj.mode:
                return True
            elif self.mth5_obj.mode == 'r':
                return False
        else:
            return False
        
    def open_mth5(self, mth5_fn):
        """
        write an mth5 file
        """
        self.mth5_fn = mth5_fn
        
        if os.path.isfile(self.mth5_fn):
            print('*** Overwriting {0}'.format(mth5_fn))
            
        self.mth5_obj = h5py.File(self.mth5_fn, 'w')
        self.mth5_obj.create_group('calibrations')
        
    def close_mth5(self):
        """
        close mth5 file to make sure everything is flushed to the file
        """
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
            for attr in ['site', 'field_notes', 'copyright', 'provenance',
                         'software']:
                self.mth5_obj.attrs[attr] = getattr(self, attr).to_json()
        
    def add_schedule(self, schedule_obj, schedule_name, compress=True):
        """
        add a schedule object to the HDF5 file
        
        :param schedule_obj: container holding the time series data as a 
                             pandas.DataFrame with columns as components
                             and indexed by time.
        :type schedule_obj: mtf5.Schedule object
        
        :param schedule_name: name of the schedule, convention is 'schedule_##'
        :type schedule_name: string
        
        """
        
        if self.h5_is_write():
            ### create group for schedule action
            schedule = self.mth5_obj.create_group(schedule_name)
            ### add metadata
            for attr in schedule_obj._attr_list:
                schedule.attrs[attr] = getattr(schedule_obj, attr)

            ### add datasets for each channel
            for comp in schedule_obj.comp_list:
                if compress:
                    schedule.create_dataset(comp.lower(), 
                                            data=getattr(schedule_obj, comp),
                                            compression='gzip',
                                            compression_opts=9)
                else:
                    schedule.create_dataset(comp.lower(), 
                                            data=getattr(schedule_obj, comp))
            return schedule
        else:
            return None
        
    def add_calibrations(self, calibration_obj, compress=True):
        """
        add calibrations for sensors
        
        :param calibration_obj: calibration object that has frequency, real, 
                                imaginary attributes
        :type calibration_obj: mth5.Calibration
        
        :param name: name of sensor for calibration
        :type name: string
        """
        
        if self.h5_is_write():
            cal = self.mth5_obj['/calibrations'].create_group(calibration_obj.name)
            cal.attrs['metadata'] = calibration_obj.to_json()
            for col in calibration_obj._col_list:
                if compress:
                    cal.create_dataset(col.lower(), 
                                       data=getattr(calibration_obj, col),
                                       compression='gzip',
                                       compression_opts=9)
                else:
                    cal.create_dataset(col.lower(), 
                                       data=getattr(calibration_obj, col))
        
    def read_mth5(self, mth5_fn):
        """
        Read MTH5 file and update attributes
        """
        if not os.path.isfile(mth5_fn):
            raise MTH5Error("Could not find {0}, check path".format(mth5_fn))
        
        self.mth5_fn = mth5_fn
        ### read in file and give write permissions in case the user wants to
        ### change any parameters
        self.mth5_obj = h5py.File(self.mth5_fn, 'r+')
        print("reading attributes")
        for attr in ['site', 'field_notes', 'copyright', 'provenance',
                     'software']:
            getattr(self, attr).from_json(self.mth5_obj.attrs[attr])
            
        for key in self.mth5_obj.keys():
            if 'sch' in key:
                setattr(self, key, Schedule())
                getattr(self, key).from_mth5(self.mth5_obj, key)
                
        
    
    def read_mth5_cfg(self, mth5_cfg_fn):
        """
        read a configuration file for all the mth5 attributes
        
        :param mth5_cfg_fn: full path to configuration file for mth5 file
        :type mth5_cfg_fn: string
        
        The configuration file has the format:
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
        usgs_str = 'U.S. Geological Survey'
        # read in the configuration file
        with open(mth5_cfg_fn, 'r') as fid:
            lines = fid.readlines()

        for line in lines:
            # skip comment lines
            if line.find('#') == 0 or len(line.strip()) < 2:
                continue
            # make a key = value pair
            key, value = [item.strip() for item in line.split('=', 1)]
            
            if value == 'usgs_str':
                value = usgs_str
            if value.find('[') >= 0 and value.find(']') >= 0 and value.find('<') != 0:
                value = value.replace('[', '').replace(']', '')
                value = [v.strip() for v in value.split(',')]
            if value.find('.') > 0:
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
            if key.count('.') == 0:
                setattr(self, key, value)
            elif key.count('.') == 1:
                obj, obj_attr = key.split('.')
                setattr(getattr(self, obj), obj_attr, value)
            elif key.count('.') == 2:
                obj, obj_attr_01, obj_attr_02 = key.split('.')
                setattr(getattr(getattr(self, obj), obj_attr_01), obj_attr_02,
                        value)
                
    def update_metadata_from_series(self, station_series):
        """
        Update metadata from a pandas.Series with old keys as columns:
            * station
            * latitude
            * longitude
            * elevation
            * declination
            * start
            * stop
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
            
        :param station_series: pandas.Series with the above index values
        :type station_series: pandas.Series
        """
        if isinstance(station_series, pd.DataFrame):
            station_series = station_series.iloc[0]
            
        assert isinstance(station_series, pd.Series), \
                'station_series is not a pandas.Series'
        
        for key in station_series.index:
            value = getattr(station_series, key)
            if key in self.site._site_attrs:
                setattr(self.site, key, value)
            elif key  == 'start':
                attr = '{0}_date'.format(key)
                setattr(self.site, attr, value)
            elif key  == 'stop' or key == 'stop_date':
                attr = 'end_date'
                setattr(self.site, attr, value)
            elif key == 'instrument_id':
                self.field_notes.data_logger.id = value
            elif key == 'station':
                self.site.id = value
            elif key == 'units':
                self.site.elev_units = value
            elif key[0:2] in ['ex', 'ey', 'hx', 'hy', 'hz']:
                comp = key[0:2]
                attr = key.split('_')[1]
                if attr == 'num':
                    attr = 'chn_num'
                if attr == 'sensor':
                    attr = 'id'
                if 'e' in comp:
                    setattr(getattr(self.field_notes, 'electrode_{0}'.format(comp)),
                            attr, value)
                elif 'h' in comp:
                    setattr(getattr(self.field_notes, 'magnetometer_{0}'.format(comp)),
                        attr, value)
                    
# =============================================================================
#  read and write json for attributes       
# =============================================================================
class NumpyEncoder(json.JSONEncoder):
    """ 
    Need to encode numpy ints and floats for json to work
    """
    def default(self, obj):
        if isinstance(obj, (np.int_, np.intc, np.intp, np.int8,
                            np.int16, np.int32, np.int64, np.uint8,
                            np.uint16, np.uint32, np.uint64)):
            return int(obj)
        
        elif isinstance(obj, (np.float_, np.float16, np.float32, np.float64)):
            return float(obj)
        
        elif isinstance(obj,(np.ndarray,)): 
            return obj.tolist()
        
        return json.JSONEncoder.default(self, obj)

def to_json(obj):
    """
    write a json string from a given object, taking into account other class
    objects contained within the given object.
    
    :param obj: class object to transform into string
    """
    if isinstance(obj, (Site, Location)):
        keys = obj._site_attrs
    else:
        keys = obj.__dict__.keys()
        
    obj_dict = {}
    for key in keys:
        if key.find('_') == 0:
            continue
        value = getattr(obj, key)
        
        if isinstance(value, (Site, Location, FieldNotes, Instrument,
                              DataQuality, Citation, Provenance, Person,
                              Processing, Software)):
            obj_dict[key] = {}
            for o_key, o_value in value.__dict__.items():
                if o_key.find('_') == 0:
                    continue
                obj_dict[key][o_key] = o_value
                
        elif isinstance(value, (Site, Location)):
            obj_dict[key] = {}
            for o_key in value.__dict__.keys()+['latitude', 'longitude', 'elevation']:
                if o_key.find('_') == 0:
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

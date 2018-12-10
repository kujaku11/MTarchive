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
import json
import h5py
import numpy
import datetime
import time
import mtpy.utils.gis_tools as gis_tools

# =============================================================================
# MT HDF5 file
# =============================================================================
class MTHF(object):
    """
    MT HDF5 file
    
    """

    def __init__(self, **kwargs):
        self.h5_fn = None
        self.Site = Site()
        self.FieldNotes = FieldNotes()
        self.DataQualtiy = DataQuality()
        self.Citation = Citation()
        self.Software = Software()
        
        
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
        utm_point = gis_tools.project_point_ll2utm(self._latitude,
                                                   self._longitude,
                                                   datum=self.datum)

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
                                                  datum=self.datum)

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
        self._date_fmt = '%Y-%m-%dT%H:%M:%S.%f'
        self._site_attrs = ['start_date',
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
    def start_date(self, start_date, fmt=None):
        if fmt is not None:
            self._start_date = datetime.datetime.strptime(start_date, 
                                                          fmt)
        else:
            try:
                self._start_date = datetime.datetime.strptime(start_date, 
                                                              self._date_fmt)
            except TypeError:
                print("Date format is not correct, should be {0}".format(self._date_fmt)+\
                      " or set your own using Site._date_fmt")
                self._start_date = None
    @property
    def end_date(self):
        try:
            return datetime.datetime.strftime(self._end_date, self._date_fmt)
        except TypeError:
            return None
    
    @end_date.setter
    def end_date(self, end_date, fmt=None):
        if fmt is not None:
            self._end_date = datetime.datetime.strptime(end_date, 
                                                        fmt)
        else:
            try:
                self._end_date = datetime.datetime.strptime(end_date, 
                                                            self._date_fmt)
            except TypeError:
                print("Date format is not correct, should be {0}".format(self._date_fmt)+\
                      " or set your own using Site._date_fmt")
                self._end_date = None
            
    def write_json(self):
        """
        write json string to put into attributes
        """
        site_dict = dict([(attr, getattr(self, attr)) for attr in self._site_attrs])
        site_dict['acquired_by'] = self.acquired_by.__dict__
        site_json = json.dumps(site_dict)
        
        return site_json
    
    def read_json(self, site_json):
        """
        read in json file for site information
        """
        site_dict = json.loads(site_json)
        for key, value in site_dict.items():
            if key == 'acquired_by':
                setattr(self.acquired_by, key, value)
            else:
                setattr(self, key, value)

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
        self._electric_channel = {'length':None, 'azimuth':None, 'sensor':None,
                                  'chn_num':None}
        self._magnetic_channel = {'azimuth':None, 'sensor':None, 'chn_num':None}
        
        self.DataQuality = DataQuality()
        self.DataLogger = Instrument()
        self.Electrode_ex = Instrument(**self._electric_channel)
        self.Electrode_ey = Instrument(**self._electric_channel)

        self.Magnetometer_hx = Instrument(**self._magnetic_channel)
        self.Magnetometer_hy = Instrument(**self._magnetic_channel)
        self.Magnetometer_hz = Instrument(**self._magnetic_channel)

        for key in kwargs.keys():
            setattr(self, key, kwargs[key])
            
    def write_json(self):
        """
        write json of FieldNotes
        """
        
        

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
        self.Citation = Citation()
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
        self.creating_application = 'MTpy'
        self.Creator = Person()
        self.Submitter = Person()

        for key in kwargs.keys():
            setattr(self, key, kwargs[key])


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
            
    def write_json(self):
        """
        write a json string of attributes
        """
        
        return json.dumps(self.__dict__)

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
        self.Author = Person()

        for key in kwargs:
            setattr(self, key, kwargs[key])


# ==============================================================================
#             Error
# ==============================================================================
class MTHFError(Exception):
    pass

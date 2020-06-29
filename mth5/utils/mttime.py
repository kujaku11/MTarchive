# -*- coding: utf-8 -*-
"""
Created on Wed May 13 19:10:46 2020

@author: jpeacock
"""

import datetime
import logging
import numpy as np

from dateutil import parser as dtparser
from dateutil.tz.tz import tzutc

from mth5.utils.exceptions import MTTimeError

# ==============================================================================
# convenience date-time container
# ==============================================================================
class MTime:
    """
    Date and Time container based on datetime and dateutil.parsers

    Will read in a string or a epoch seconds into a datetime.datetime object
    assuming the time zone is UTC.  If UTC is not the timezone you need to
    correct the time before inputing.  Use datetime.timezone to shift time.

    Outputs can be an ISO formatted string YYYY-MM-DDThh:mm:ss.ssssss+00:00:

        >>> t = MTtime()
        >>> t.iso_str
        '1980-01-01T00:00:00+00:00'

    .. note:: if microseconds are 0 they are omitted.

    or Epoch seconds (float):

        >>> t.epoch_seconds
        315532800.0


    Convenience getters/setters are provided as properties for the different
    parts of time.

        >>> t = MTtime()
        >>> t.year = 2020
        >>> t.year
        2020

    """

    def __init__(self, time=None):

        self.logger = logging.getLogger(
            "{0}.{1}".format(__name__, self.__class__.__name__)
        )
        self.dt_object = self.now()

        if time is not None:
            if isinstance(time, str):
                self.logger.debug("Input time is a string, will be parsed")
                self.from_str(time)

            elif isinstance(time, (int, float)):
                self.logger.debug(
                    "Input time is a number, assuming epoch " + "seconds in UTC"
                )
                self.epoch_seconds = time
            elif isinstance(time, (np.datetime64)):
                self.logger.debug(
                    "Input time is a np.datetime64 "
                    + "dt_object set to datetime64.tolist()."
                )
                self.dt_object = self.validate_tzinfo(time.tolist())

            elif isinstance(time, (datetime.datetime)):
                self.logger.debug(
                    "Input time is a np.datetime64 "
                    + "dt_object set to datetime64.tolist()."
                )
                self.dt_object = self.validate_tzinfo(time)

            else:
                msg = "input time must be a string, float, or int, not {0}"
                self.logger.error(msg.format(type(time)))

        else:
            self.logger.debug(
                "Initiated with None, dt_object is set to "
                + "default time 1980-01-01 00:00:00"
            )
            self.from_str("1980-01-01 00:00:00")

    def __str__(self):
        return self.iso_str

    def __repr__(self):
        return self.iso_str

    def __eq__(self, other):
        if isinstance(other, datetime.datetime):
            return bool(self.dt_object == other)

        elif isinstance(other, MTime):
            return bool(self.dt_object == other.dt_object)

        elif isinstance(other, str):
            return bool(self.iso_str == other)

        elif isinstance(other, (int, float)):
            return bool(self.epoch_seconds == float(other))
        else:
            msg = "Cannot compare {0} of type {1} with MTime Object".format(
                other, type(other)
            )
            self.logger.error(msg)
            raise MTTimeError(msg)

    def __ne__(self, other):
        return not self.__eq__(other)

    def __lt__(self, other):
        if isinstance(other, datetime.datetime):
            return bool(self.dt_object < other)

        elif isinstance(other, MTime):
            return bool(self.dt_object < other.dt_object)

        elif isinstance(other, str):
            return bool(self.iso_str < other)

        elif isinstance(other, (int, float)):
            return bool(self.epoch_seconds < float(other))

        else:
            msg = "Cannot compare {0} of type {1} with MTime Object".format(
                other, type(other)
            )
            self.logger.error(msg)
            raise MTTimeError(msg)

    def __le__(self, other):
        if isinstance(other, datetime.datetime):
            return bool(self.dt_object <= other)

        elif isinstance(other, MTime):
            return bool(self.dt_object <= other.dt_object)

        elif isinstance(other, str):
            return bool(self.iso_str <= other)

        elif isinstance(other, (int, float)):
            return bool(self.epoch_seconds <= float(other))
        else:
            msg = "Cannot compare {0} of type {1} with MTime Object".format(
                other, type(other)
            )
            self.logger.error(msg)
            raise MTTimeError(msg)

    def __gt__(self, other):
        return not self.__lt__(other)

    def __ge__(self, other):
        if isinstance(other, datetime.datetime):
            return bool(self.dt_object >= other)

        elif isinstance(other, MTime):
            return bool(self.dt_object >= other.dt_object)

        elif isinstance(other, str):
            return bool(self.iso_str >= other)

        elif isinstance(other, (int, float)):
            return bool(self.epoch_seconds >= float(other))
        else:
            msg = "Cannot compare {0} of type {1} with MTime Object".format(
                other, type(other)
            )
            self.logger.error(msg)
            raise MTTimeError(msg)

    def __add__(self, other):
        """
        add time only using datetime.timedelta, otherwise it does not make 
        sense to at 2 times together.  
        
        """
        if not isinstance(other, datetime.timedelta):
            msg = (
                "Adding times does not make sense, must use "
                + "datetime.timedelta to add time. \n"
                + "\t>>> add_time = datetime.timedelta(seconds=10) \n"
                + "\t>>> mtime_obj + add_time"
            )
            self.logger.error(msg)
            raise MTTimeError(msg)

        return MTime(self.dt_object + other)

    def __sub__(self, other):
        """
        Get the time difference between to times in seconds.
        
        :param other: other time value
        :type other: [ str | float | int | datetime.datetime | np.datetime64 ]
        :return: time difference in seconds
        :rtype: float

        """

        if isinstance(other, type(self)):
            other_seconds = other.epoch_seconds
        elif isinstance(other, (str)):
            other_dt = self.validate_tzinfo(dtparser.parse(other))
            other_seconds = other_dt.timestamp()
        elif isinstance(other, (float, int)):
            other_seconds = float(other)
        elif isinstance(other, (np.datetime64)):
            other_seconds = other.astype(np.float)
        elif isinstance(other, (datetime.datetime)):
            other_seconds = other.timestamp()

        else:
            msg = "Cannot compare {0} of type {1} with MTime Object".format(
                other, type(other)
            )
            self.logger.error(msg)
            raise MTTimeError(msg)

        return self.epoch_seconds - other_seconds

    @property
    def iso_str(self):
        return self.dt_object.isoformat()

    @property
    def iso_no_tz(self):
        return self.dt_object.isoformat().split("+", 1)[0]

    @property
    def epoch_seconds(self):
        return self.dt_object.timestamp()

    @epoch_seconds.setter
    def epoch_seconds(self, seconds):
        self.logger.debug(
            "reading time from epoch seconds, assuming UTC " + "time zone"
        )
        dt = datetime.datetime.utcfromtimestamp(seconds)
        dt = dt.replace(tzinfo=datetime.timezone.utc)
        self.dt_object = dt

    def from_str(self, dt_str):
        try:
            self.dt_object = self.validate_tzinfo(dtparser.parse(dt_str))
        except dtparser.ParserError as error:
            msg = (
                "{0}".format(error)
                + "Input must be a valid datetime string, see "
                + "https://docs.python.org/3.8/library/datetime.html"
            )
            self.logger.error(msg)
            raise MTTimeError(msg)

    def validate_tzinfo(self, dt_object):
        """
        make sure the timezone is UTC
        """

        if dt_object.tzinfo == datetime.timezone.utc:
            return dt_object

        elif isinstance(dt_object.tzinfo, tzutc):
            return dt_object.replace(tzinfo=datetime.timezone.utc)

        elif dt_object.tzinfo is None:
            return dt_object.replace(tzinfo=datetime.timezone.utc)

        elif dt_object.tzinfo != datetime.timezone.utc:
            raise ValueError("Time zone must be UTC")

    @property
    def date(self):
        return self.dt_object.date().isoformat()

    @property
    def year(self):
        return self.dt_object.year

    @year.setter
    def year(self, value):
        self.dt_object = self.dt_object.replace(year=value)

    @property
    def month(self):
        return self.dt_object.month

    @month.setter
    def month(self, value):
        self.dt_object = self.dt_object.replace(month=value)

    @property
    def day(self):
        return self.dt_object.day

    @day.setter
    def day(self, value):
        self.dt_object = self.dt_object.replace(day=value)

    @property
    def hour(self):
        return self.dt_object.hour

    @hour.setter
    def hour(self, value):
        self.dt_object = self.dt_object.replace(hour=value)

    @property
    def minutes(self):
        return self.dt_object.minute

    @minutes.setter
    def minutes(self, value):
        self.dt_object = self.dt_object.replace(minute=value)

    @property
    def seconds(self):
        return self.dt_object.second

    @seconds.setter
    def seconds(self, value):
        self.dt_object = self.dt_object.replace(second=value)

    @property
    def microseconds(self):
        return self.dt_object.microsecond

    @microseconds.setter
    def microseconds(self, value):
        self.dt_object = self.dt_object.replace(microsecond=value)

    def now(self):
        """
        set date time to now

        :return: current UTC time
        :rtype: datetime with UTC timezone

        """
        self.dt_object = self.validate_tzinfo(datetime.datetime.utcnow())


def get_now_utc():
    """
    Get the current time in UTC format
    :return: ISO formatted string of current time in UTC
    :rtype: string
    
    """

    m_obj = MTime()
    m_obj.now()
    return m_obj.iso_str

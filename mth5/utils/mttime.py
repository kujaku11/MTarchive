# -*- coding: utf-8 -*-
"""
Created on Wed May 13 19:10:46 2020

@author: jpeacock
"""
import datetime
from dateutil import parser as dtparser

#==============================================================================
# convenience date-time container
#==============================================================================    
class MTime(object):
    """
    date and time container
    """
    
    def __init__(self):
        self.dt_object = self.from_str('1980-01-01 00:00:00')
           
    @property
    def iso_str(self):
        return self.dt_object.isoformat()
        
    @property
    def epoch_sec(self):
        return self.dt_object.timestamp()
    
    def from_str(self, dt_str):
        return self.validate_tzinfo(dtparser.parse(dt_str))
        
    def validate_tzinfo(self, dt_object):
        """
        make sure the timezone is UTC
        """
        
        if dt_object.tzinfo == datetime.timezone.utc:
            return dt_object
        
        elif dt_object.tzinfo is None:
            return dt_object.replace(tzinfo=datetime.timezone.utc)
        
        elif dt_object.tzinfo != datetime.timezone.utc:
            raise ValueError('Time zone must be UTC')
            
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
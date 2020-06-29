Comments
----------

	* run.data_logger.power_source --> add under load voltage
		- suggested resolution: power_source.power_source.load_voltage.start/end
		
	* channel.tilt angles --> should be relative to the horizontal instead of the vertical.  0 would be parallel with the horizon and 90 would be perpendicular.
		- suggested resolution: change tilt angle to be relative to horizontal instead of vertical.
	
	* station.orientation_method --> should have expandable options for new gadgets like electronic compasses
		- suggested resolution:  add various gadgets to option list.
		
	* run.channels measured --> technically the recorded magnetic field is B
		- suggested resolution: add B to option list
		
	* channel.data_type --> The options for type of measurement RMT, AMT, ... are too fine grained.  Should be more general.
		- suggested resolution: This is meant to be a general indication of the type of measurement, could just have BBMT and LPMT. Should there be more description based on sample_rate.  You are limited by Nyquist and sensor sensitivity, is this something we should take into account with labeling data_type? 
		
	* run.end_time --> a more accurate description is start time, number of samples and sampling rate
		- suggested resolution: the impetus should be on the user to make the end time.  
		
	* run.sample_rate --> dangerous to make it a float with various compilers having different rounding errors
		- suggest resolution: Don't think this is an issue if properly accounted for in the software. 
		
	* run --> does not accommodate LSB, sensor settings, line driver, gain ranger (metronix)
		- suggested resolution: this is very specific to the instrument, I guess we need to make clear that we are indicating the must have metadata and other metadata can be added its just not standard metadata.  
	
	* electric.positive/negative and magnetic orientation --> need to describe what positive and negative means in reference frame.
		- suggested resolution: can add in a description of what postive and negative are relative to in a reference frame.
		
	* survey data --> add a description of the type of data in the file, raw, units
		- suggested resolution: add survey.data_level = [0, 1, 2] 
			- 0 = raw data in counts with metadata and responses
			- 1 = data converted to units and response removed
			- 2 = processed or manipulated data (rotated, filtered, ...)
			
		
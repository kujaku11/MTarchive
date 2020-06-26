Basics
----------

**MTH5** is written to make read/writing an *.mth5* file easier.

.. hint:: MTH5 is comprehensively logged, therefore if any problems arise you can always check the mth5_debug.log and the mth5_error.log, which will be written to your current working directory.

Each MTH5 file has default groups. A 'group' is basically like a folder that can contain other groups or datasets.  These are:
	* **Survey**    --> The master or root group of the HDF5 file
	* **Filters**   --> Holds all filters and filter information
	* **Reports**   --> Holds any reports relevant to the survey
	* **Standards** --> A summary of metadata standards used  
	* **Stations**  --> Holds all the stations an subsequent data
	
Each group also has a summary table to make it easier to search and access different parts of the file. Each entry in the table will have an HDF5 reference that can be directly used to get the appropriate group or dataset without using the path.  
	
To open a new *.mth5* file::

>>> from mth5 import mth5
>>> mth5_obj = mth5.MTH5()
>>> mth5_obj.open(r"path/to/file.mth5", mode="w")
	
To open an exiting *.mth5* file::


>>> from mth5 import mth5
>>> mth5_obj = mth5.MTH5()
>>> mth5_obj.open(r"path/to/file.mth5", mode="a")
	
.. note:: If 'w' is used for the mode, it will overwrite any file of the same name, so be careful you don't overwrite any files.  Using 'a' for the mode is safer as this will open  an existing file of the same name and will give you write privilages.

To close a file::

	>>> mth5_obj.close_mth5()
	2020-06-26T15:01:05 - mth5.mth5.MTH5.close_mth5 - INFO - Flushed and 
	closed example_02.mth5
	
.. note:: Once a MTH5 file is closed any data contained within cannot be accessed.  All groups are weakly referenced, therefore once the file closes the group can no longer access the HDF5 group and you will get a message like
	>>> 2020-06-26T15:21:47 - mth5.groups.Station.__str__ - WARNING - MTH5 file is closed and cannot be accessed. MTH5 file is closed and cannot be accessed.

A MTH5 object is represented by the file structure and
can be displayed at anytime from the command line.

	
>>> mth5_obj
/:
====================
	|- Group: Survey
	----------------
		|- Group: Filters
		-----------------
			--> Dataset: Summary
			......................
		|- Group: Reports
		-----------------
			--> Dataset: Summary
			......................
		|- Group: Standards
		-------------------
			--> Dataset: Summary
			......................
		|- Group: Stations
		------------------
			|- Group: MT001
			---------------
				--> Dataset: Summary
				......................
			--> Dataset: Summary
			......................
				
This file does not contain a lot of stations, but this can get verbose if there are a lot of stations and filter. If you want to check what stations are in the current file.

>>> mth5_obj.station_list
['Summary', 'MT001']
	
	
Each group has a group container with convenience methods.  Each group has a property attribute called `group_list` that lists all groups the next level down.

.. seealso:: `mth5.groups` for more information.   

	

	

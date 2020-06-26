Dealing with Stations
------------------------



Stations are the main groups that hold data at the channel level.  There are 2 ways to add/remove/get stations.  

Using `stations_group`
^^^^^^^^^^^^^^^^^^^^^^^

The first way to add/get/remove stations is from the :attribute:`mth5.MTH5.staions_group` which is a :class:`mth5.groups.MasterStationsGroup` object.

	>>> stations = mth5_obj.stations_group
	>>> type(stations)
	mth5.groups.MasterStationsGroup
	>>> stations
	/Survey/Stations:
	====================
		|- Group: MT001
		---------------
			|- Group: MT001a
			----------------
				--> Dataset: Ex
				.................
				--> Dataset: Ey
				.................
				--> Dataset: Hx
				.................
				--> Dataset: Hy
				.................
				--> Dataset: Hz
				.................
				--> Dataset: Summary
				......................

From the *stations_group* you can add/remove/get a station.

To add a station::
	
	>>> new_station = stations.add_station('MT002')
	>>> print(type(new_station))
	mth5.groups.StationGroup
	>>> new_station
	/Survey/Stations/MT002:
	====================
	--> Dataset: Summary
	......................
	
To get an existing station::

	>>> existing_station = stations.get_station('MT001')
	
To remove an existing station::
	
	>>> stations.remove_station('MT002')
	>>> stations.group_list
	['Summary', 'MT001']

Using Covnenience methods
^^^^^^^^^^^^^^^^^^^^^^^^^^^

The second way to add/remove/get stations is from the convenience functions in :class:`mth5.MTH5`.  These use the same methods as the :class:`mth5.groups.MasterStationsGroup` but can be accessed directly.

To add a station::

	>>> new_station = mth5_obj.add_station('MT002')
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
				|- Group: MT002
				---------------
					--> Dataset: Summary
					......................
				--> Dataset: Summary
				......................

To get an existing station::

	>>> existing_station = mth5_obj.get_station('MT002')
	
To remove an existing station::

	>>> mth5_obj.remove_station('MT002')
	
Summary Table
^^^^^^^^^^^^^^^^^^^^^^^

The station summary table summarizes all stations within the survey.

==================== ==================================================
Column               Description
==================== ==================================================
archive_id           Station archive name
start                Start time of the station (ISO format)
end                  End time of the station (ISO format)
components           All components measured by the station
measurement_type     All measurement types collected by the station 
location.latitude    Station latitude (decimal degrees)
location.longitude   Station longitude (decimal degrees) 
location.elevation   Station elevation (meters)
hdf5_reference       Internal HDF5 reference
==================== ==================================================



Dealing with Stations
------------------------

Stations are the main groups that hold data at the channel level.  There are 2 ways to add/remove/get stations.  The first is from the `stations_group`::


>>> stations = mth5_obj.stations_group
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
To add a station

	
>>> new_station = stations.add_station('MT002')
>>> print(type(new_station))
mth5.groups.StationGroup
>>> new_station
/Survey/Stations/MT002:
====================
--> Dataset: Summary
......................
	
To get an existing station

	
>>> existing_station = stations.get_station('MT001')
	
To remove an existing station

	
>>> stations.remove_station('MT002')
>>> stations.group_list
['Summary', 'MT001']
Runs
--------------

A run is a collection of channels that recorded at similar start and end times at the same sample rate for a given station.  A run is contained within a :class:`mth5.groups.RunGroup` object.  A run is the next level down from a station.  A station can contain many runs.

The main way to add/remove/get a run object is through a :class:`mth5.groups.StationGroup` object

Accessing through StationGroup
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

You can get a :class:`mth5.groups.StationGroup` using either method in the previous section.

>>> new_station = mth5_obj.add_station('MT003')

or 

>>> new_station = mth5_obj.stations_group.add_station('MT003')

Add Run
"""""""""""

>>> # if you don't already have a run name one can be assigned based on existing runs
>>> new_run_name = new_station.make_run_name()
>>> new_run = new_station.add_run(new_run_name)

Or 

>>> new_run = mth5_obj.add_run('MT003', 'MT003a')

Get Run
"""""""""""

Similar methods for get/remove a run

>>> existing_run = new_station.get_run('MT003a')

or

>>> existing_run = mth5_obj.get_run('MT003', 'MT003a')

Remove Run
"""""""""""""""

>>> new_station.remove_run('MT003a')

or 

>>> mth5_obj.remove_run('MT003', 'MT003a')

Summary Table
^^^^^^^^^^^^^^^^^^^^

The summary table summarizes all channels for that run.

==================== ==================================================
Column               Description
==================== ==================================================
component            Component name
start                Start time of the channel (ISO format) 
end                  End time of the channel (ISO format0
n_samples            Number of samples for the channel
measurement_type     Measuremnt type of the channel
units                Units of the channel data 
hdf5_reference       HDF5 internal reference
==================== ==================================================

.. seealso:: :class:`mth5.groups.RunGroup` and :class:`mth5.metadata.Run` for more information.

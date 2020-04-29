# MTarchive

The goal of MTarchive is to develop tools for archiving magnetotelluric (MT) time series data.  

The preferred format is HDF5 and has been adopted to conform to MT data.  The module mth5 contains reading/writing capabilities.  

The metadata follows the standards proposed by the IRIS-PASSCAL MT Software working group. 

Note: This is a work in progress.  Feel free to comment or send me a message at jpeacock@usgs.gov on the data format.

## Modules

* **mth5** --> includes reading and writing of HDF5 files formatted specifically for MT data.

* **usgs_archive** --> includes tools for archiving data on Science Base including xml metadata files, uploading to Science Base, changing JSON files, converting .z3d files to MTH5 files.
  
## MTH5 Format
![MTH5 Format](https://github.com/kujaku11/MTarchive/blob/tables/docs/example_mt_file_structure.png)

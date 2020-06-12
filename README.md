![MTH5 Logo](https://github.com/kujaku11/MTarchive/blob/tables/mth5_logo.png)

# MTarchive

The goal of MTarchive is to develop a standard format and tools for archiving magnetotelluric (MT) time series data.  

The preferred format is HDF5 and has been adopted to conform to MT data, something that has been needed in the EM community for some time.  The module mth5 contains reading/writing capabilities and will contain tools for retrieving data in useful ways to work with processing codes.  

The metadata follows the standards proposed by the [IRIS-PASSCAL MT Software working group](https://www.iris.edu/hq/about_iris/governance/mt_soft) and documented in [MT Metadata Standards](https://github.com/kujaku11/MTarchive/blob/tables/docs/mt_metadata_guide.pdf). 

**Note: This is a work in progress.  Feel free to comment or send me a message at jpeacock@usgs.gov on the data format.**

## Modules

* **mth5** --> This will eventually be the main module, but for now resides here.  MTH5 includes reading and writing of HDF5 files formatted specifically for MT data that adheres to the proposed metadata standards.  MTH5 based on h5py and numpy which was chosen because we are dealing mainly with arrays and will hopefully be able to be used in parallel.  

* **usgs_archive** --> includes tools for archiving data on Science Base including xml metadata files, uploading to Science Base, changing JSON files, converting .z3d and NIMS binary files to MTH5 files.
  
## MTH5 Format
* The basic format of MTH5 is illustrated below, where metadata is attached at each level.

![MTH5 Format](https://github.com/kujaku11/MTarchive/blob/tables/docs/example_mt_file_structure.png)

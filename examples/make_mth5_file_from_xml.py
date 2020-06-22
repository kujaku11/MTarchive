# -*- coding: utf-8 -*-
"""
Example script to make an MTH5 file from real data

Created on Mon Jun 22 12:20:59 2020

@author: jpeacock
"""
# =============================================================================
# imports
# =============================================================================
from pathlib import Path
from xml.etree import cElementTree as et

from mth5 import mth5

# =============================================================================
# inputs
# =============================================================================
dir_path = Path(r"c:\Users\jpeacock\Documents\mt_format_examples\mth5")


def read_xml(xml_fn):
    """
    
    :param xml_fn: DESCRIPTION
    :type xml_fn: TYPE
    :return: DESCRIPTION
    :rtype: TYPE

    """
    
    return et.parse(xml_fn).getroot()
    
# =============================================================================
# script 
# =============================================================================
# initialize mth5 object
mth5_obj = mth5.MTH5()
mth5_obj.open_mth5(dir_path.joinpath('example.mth5'), mode='w')

### add survey information
survey_element = read_xml(dir_path.joinpath('survey.xml'))
survey_obj = mth5_obj.survey_group
survey_obj.metadata.from_xml(survey_element)
survey_obj.write_metadata()

mth5_obj.close_mth5()



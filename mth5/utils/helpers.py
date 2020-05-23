# -*- coding: utf-8 -*-
"""
Created on Fri May 22 16:49:06 2020

@author: jpeacock
"""

from collections import MutableMapping 
  
# code to convert ini_dict to flattened dictionary 
# default seperater '_' 
def flatten_dict(meta_dict, parent_key=None, sep ='.'): 
    items = [] 
    for key, value in meta_dict.items(): 
        if parent_key:
            new_key = '{0}{1}{2}'.format(parent_key, sep, key) 
        else:
            new_key = key 
  
        if isinstance(value, MutableMapping): 
            items.extend(flatten_dict(value, new_key, sep=sep).items()) 
        else: 
            items.append((new_key, value)) 
    return dict(items) 

def recursive_split(key, value, remainder, sep='.'):
    """
    recursively split a dictionary
    
    :param key: DESCRIPTION
    :type key: TYPE
    :param value: DESCRIPTION
    :type value: TYPE
    :param remainder: DESCRIPTION
    :type remainder: TYPE
    :return: DESCRIPTION
    :rtype: TYPE

    """
    
    key, *other = key.split(sep, 1)
    if other:
        recursive_split(other[0], value, remainder.setdefault(key, {}))
    else:
        remainder[key] = value
    
def structure_dict(meta_dict, sep='.'):
    structured_dict = {}
    for key, value in meta_dict.items():
        recursive_split(key, value, structured_dict, sep=sep)
    return structured_dict
        
    
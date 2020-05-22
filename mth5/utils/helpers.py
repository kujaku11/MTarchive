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
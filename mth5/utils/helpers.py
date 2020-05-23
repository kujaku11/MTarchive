# -*- coding: utf-8 -*-
"""
Created on Fri May 22 16:49:06 2020

@author: jpeacock
"""

from collections import MutableMapping
from xml.etree import cElementTree as et 
from xml.dom import minidom
  
# code to convert ini_dict to flattened dictionary 
# default seperater '_' 
def flatten_dict(meta_dict, parent_key=None, sep ='.'): 
    """
    
    :param meta_dict: DESCRIPTION
    :type meta_dict: TYPE
    :param parent_key: DESCRIPTION, defaults to None
    :type parent_key: TYPE, optional
    :param sep: DESCRIPTION, defaults to '.'
    :type sep: TYPE, optional
    :return: DESCRIPTION
    :rtype: TYPE

    """
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

def recursive_split_dict(key, value, remainder, sep='.'):
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
        recursive_split_dict(other[0], value, remainder.setdefault(key, {}))
    else:
        remainder[key] = value
    
def structure_dict(meta_dict, sep='.'):
    """
    
    :param meta_dict: DESCRIPTION
    :type meta_dict: TYPE
    :param sep: DESCRIPTION, defaults to '.'
    :type sep: TYPE, optional
    :return: DESCRIPTION
    :rtype: TYPE

    """
    structured_dict = {}
    for key, value in meta_dict.items():
        recursive_split_dict(key, value, structured_dict, sep=sep)
    return structured_dict
        
def recursive_split_xml(element, item, name, reference_dict=None):
    """
    """
    name = [name]
    if isinstance(item, dict):
        for key, value in item.items():
            name.append(key)
            sub_element = et.SubElement(element, key)
            recursive_split_xml(sub_element, value, key, reference_dict)
            
    elif isinstance(item, (tuple, list)):
        for ii in item:
            sub_element = et.SubElement(element, 'i')
            recursive_split_xml(sub_element, ii)
    elif isinstance(item, str):
        element.text = item
    else:
        element.text = str(item)
     
    name = '.'.join(name)
    print(name)
    if reference_dict:
        try:
            units = reference_dict[name]['units']
            print(units)
            if units is not None:
                element.set('units', str(units))
        except KeyError:
            pass
    
        
    return element, name
    
def dict_to_xml(meta_dict, reference_dict=None):
    """
    Assumes dictionary is structured {class:{attribute_dict}}
    
    :param meta_dict: DESCRIPTION
    :type meta_dict: TYPE
    :return: DESCRIPTION
    :rtype: TYPE

    """
    class_name = list(meta_dict.keys())[0]
    root = et.Element(class_name)
        
    for key, value in meta_dict[class_name].items():
        element = et.SubElement(root, key)
        name = [key]
        r, k = recursive_split_xml(element, value, key, reference_dict)
        
        
    
    return root
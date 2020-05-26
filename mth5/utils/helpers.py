# -*- coding: utf-8 -*-
"""
Created on Fri May 22 16:49:06 2020

@author: jpeacock
"""

from collections.abc import MutableMapping
from collections import OrderedDict, defaultdict
from xml.etree import cElementTree as et 
from xml.dom import minidom
from operator import itemgetter
  
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

def get_units(name, attr_dict):
    """
    """
    try:
        units = attr_dict[name]['units']
        if not isinstance(units, str):
            units = '{0}'.format(units)
    except KeyError:
        units = None
    if units in [None, 'None', 'none']:
        return None
    
    return units

def get_type(name, attr_dict):
    """
    """
    try:
        v_type = attr_dict[name]['type']
        if v_type in ['string', str, 'str', 'String']:
            v_type = None
    except KeyError:
        v_type = None
    return v_type
        
def recursive_split_xml(element, item, base, name, attr_dict=None):
    """
    """
    key = None
    if isinstance(item, dict):
        for key, value in item.items():
            attr_name = '.'.join([base, key])
            
            sub_element = et.SubElement(element, key)
            recursive_split_xml(sub_element, value, attr_name, key,
                                attr_dict)
                
    elif isinstance(item, (tuple, list)):
        for ii in item:
            sub_element = et.SubElement(element, 'i')
            recursive_split_xml(sub_element, ii, base, name, attr_dict)
            
    elif isinstance(item, str):
        element.text = item
    elif isinstance(item, (float, int, type(None))):
        element.text = str(item)
    else:
        raise ValueError('Value cannot be {0}'.format(type(item)))
    
    if attr_dict:
        
        units = get_units(base, attr_dict)
        if units:
            element.set('units', str(units))
            
        v_type = get_type(base, attr_dict)
        if v_type:
            element.set('type', v_type)
    
    return element, name
    
def dict_to_xml(meta_dict, attr_dict=None):
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
        recursive_split_xml(element, value, key, key, attr_dict)
    
    return root

def element_to_dict(element):
    """
    
    :param element: DESCRIPTION
    :type element: TYPE
    :return: DESCRIPTION
    :rtype: TYPE

    """
    meta_dict = {element.tag: {} if element.attrib else None}
    children = list(element)
    if children:
        child_dict = defaultdict(list)
        for dc in map(element_to_dict, children):
            for k, v in dc.items():
                child_dict[k].append(v)
        meta_dict = {element.tag: {k:v[0] if len(v) == 1 else v 
                                   for k, v in child_dict.items()}}
    
    # going to skip attributes for now, later can check them against 
    # standards
    # if element.attrib:
    #     meta_dict[element.tag].update((k, v) 
    #                                   for k, v in element.attrib.items())
    
    if element.text:
        text = element.text.strip()
        # if children or element.attrib:
        #     if text:
        #       meta_dict[element.tag]['value'] = text
        # else:
        meta_dict[element.tag] = text
        
    return OrderedDict(sorted(meta_dict.items(), key=itemgetter(0)))

def element_to_string(element):
    return minidom.parseString(et.tostring(element).decode()).toprettyxml(
            indent='    ')
    
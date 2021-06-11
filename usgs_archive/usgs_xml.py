# -*- coding: utf-8 -*-
"""
Created on Thu Jun 10 12:33:12 2021

:copyright: 
    Jared Peacock (jpeacock@usgs.gov)

:license: MIT

"""
from pathlib import Path
from configparser import ConfigParser
from usgs_archive import xml_utils

class MTSBXML(xml_utils.XMLRecord):
    """
    Class to make it easier to create and manipulate Sciencebase metadata XML files
    that adhere to the FGDC standards.
    
    Based on pymdwizard https://github.com/usgs/fort-pymdwizard/tree/master
    
    """
    
    def __init__(self, fn=None):
        super().__init__(fn)
    
    def read_template_xml(self, template_fn):
        """
        Read in a template xml that can be updated later
        
        :param template_fn: Full path to template XML file
        :type template_fn: string or Path
        :return: fills 
        :rtype: TYPE

        """
        
        if not Path(template_fn):
            raise IOError(f"Could not find {template_fn}")
            
        self.fn = template_fn
        
    def read_config(self, cfg_fn):
        """
        read from a config file
        """
        cfg_fn = Path(cfg_fn)
        if not cfg_fn.exists():
            raise IOError(f"Could not find {cfg_fn}")
        c = ConfigParser()
        c.read_file(cfg_fn.open())
        
        self._update_cite_info(c["general"])
        self._update_description(c["general"])
        for k in ["general", "thesaurus"]:
            self._update_keywords(c["keywords"][k], k)
        for k in ["geolex", "eras"]:
            self._update_temporal(c["temporal"][k], k)
            
        self._update_constraints(c["supplemental"]["usage_constraints"])
        
        
    def _update_authors(self, authors, orcids=None):
        authors = [name.strip() for name in authors.split(',')] 
        self.metadata.idinfo.citation.citeinfo.clear_children("origin")
        count = 0
        other_cite = ''
        for name in authors:
            xml_utils.XMLNode(
                tag="origin", 
                text=name.strip(),
                parent_node=self.metadata.idinfo.citation.citeinfo, 
                index=count)
            count += 1
        if orcids:
            orcids = [number.strip() for number in orcids.split(',')]
  
            other_cite = "Additional information about Originators: "
            for name, orcid in zip(authors, orcids):
                other_cite += (f"{name}, {orcid}; ")
                
        return other_cite

        
    def _update_cite_info(self, config_object):
        """
        Update Cite information from config file information
        """
        
        mapping = {"authors": "origin",
                   "title": "title",
                   "release_date": "pubdate",
                   "doi": "onlink",
                   "gis_data": "geoform",
                   "suggested_citation": "othercit"}
        other_cite = ''
        for k in ["authors", "release_date", "gis_data", "title", "suggested_citation", "doi"]:
            v = config_object[k]
            xml_key = mapping[k]
            if k == "authors":
                if "orcids" in config_object.keys():
                    other_cite = self._update_authors(v, config_object["orcids"])
                else:
                    other_cite = self._update_authors(v)
                
                    
            elif k == "suggested_citation":
                other_cite += f"\nSuggested citation: {v}"
                self.metadata.idinfo.citation.citeinfo.othercit.text = other_cite
                
            elif k == "release_date":
                self.metadata.idinfo.citation.citeinfo.pubdate.text = v.replace('-', '')
                
            else:
                setattr(getattr(self.metadata.idinfo.citation.citeinfo, xml_key), "text", v)
                
    def _update_description(self, config_object):
        """ 
        update description
        """
        if "purpose" in config_object.keys():
            self.metadata.idinfo.descript.purpose.text = config_object["purpose"]
            
        if "abstract" in config_object.keys():
            self.metadata.idinfo.descript.abstract.text = config_object["abstract"]
        
        if "supplement_info" in config_object.keys():
            self.metadata.idinfo.descript.supplinfo.text = config_object["supplement_info"]
            
            
    def update_bounding_box(self, west, east, north, south):
        """
        update the bounding box
        """
        
        self.metadata.idinfo.spdom.bounding.westbc.text = west
        self.metadata.idinfo.spdom.bounding.eastbc.text = east
        self.metadata.idinfo.spdom.bounding.northbc.text = north
        self.metadata.idinfo.spdom.bounding.southbc.text = south
        
    def _update_keywords(self, kw_string, key):
        """
        update the keywords
        """
        index_dict = {"general": 1,
                      "thesaurus": 2}
        
        kw = [k.strip() for k in  kw_string.split(',')]
        try:
            count = len(self.metadata.idinfo.keywords.theme[index_dict[key]].themekey)
        except TypeError:
            count = 1
        self.metadata.idinfo.keywords.theme[index_dict[key]].clear_children("themekey")
        for k in kw:
            xml_utils.XMLNode(
                tag="themekey", 
                text=k,
                parent_node=self.metadata.idinfo.keywords.theme[index_dict[key]], 
                index=count)
            count += 1
            
    def _update_places(self, place_string, place):
        """
        update places
        """
        index_dict = {"gnis": 0,
                      "common": 1,
                      "terranes": 2}
        
        index = index_dict[place]
        kw = [k.strip() for k in place_string.split(',')]
        try:
            count = len(self.metadata.idinfo.keywords.place[index].placekey)
        except TypeError:
            count = 1
        self.metadata.idinfo.keywords.place[index].clear_children("placekey")
        for k in kw:
            xml_utils.XMLNode(
                tag="placekey", 
                text=k,
                parent_node=self.metadata.idinfo.keywords.place[index], 
                index=count)
            count += 1
            
    def _update_temporal(self, temporal_string, temporal):
        """
        update places
        """
        index_dict = {"geolex": 0,
                      "eras": 1}
        
        index = index_dict[temporal]
        kw = [k.strip() for k in temporal_string.split(',')]
        try:
            count = len(self.metadata.idinfo.keywords.temporal[index].tempkey)
        except TypeError:
            count = 1
        self.metadata.idinfo.keywords.temporal[index].clear_children("tempkey")
        for k in kw:
            xml_utils.XMLNode(
                tag="tempkey", 
                text=k,
                parent_node=self.metadata.idinfo.keywords.temporal[index], 
                index=count)
            count += 1
            
    def _update_constraints(self, constraint_string):
        """
        
        :param constraint_string: DESCRIPTION
        :type constraint_string: TYPE
        :return: DESCRIPTION
        :rtype: TYPE

        """
        
        self.metadata.idinfo.useconst.text = constraint_string
        
        
        
        
        
        
        
                    
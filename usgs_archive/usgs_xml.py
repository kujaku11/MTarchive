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
import datetime

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
            
        self._update_constraints(c["usage"]["constraints"])
        self._update_contact(c["principle_investigator"])
        self._update_processing(c["processing"])
        self._update_attachments(c["attachments"])
        
        
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
        
    def _update_contact(self, config_object):
        """
        Update ptcontact and metc
        
        :param config_object: DESCRIPTION
        :type config_object: TYPE
        :return: DESCRIPTION
        :rtype: TYPE

        """
        
        self.metadata.idinfo.ptcontac.cntinfo.cntperp.cntper.text = config_object["name"]
        self.metadata.metainfo.metc.cntinfo.cntperp.cntper.text = config_object["name"]
        
        self.metadata.idinfo.ptcontac.cntinfo.cntperp.cntorg.text = config_object["orginization"]
        self.metadata.metainfo.metc.cntinfo.cntperp.cntorg.text = config_object["orginization"]
        
        self.metadata.idinfo.ptcontac.cntinfo.cntpos.text = config_object["position"]
        self.metadata.metainfo.metc.cntinfo.cntpos.text = config_object["position"]
        
        self.metadata.idinfo.ptcontac.cntinfo.cntaddr.addrtype.text = "mailing address"
        self.metadata.metainfo.metc.cntinfo.cntaddr.addrtype.text = "mailing address"
        
        self.metadata.idinfo.ptcontac.cntinfo.cntaddr.address.text = config_object["address"]
        self.metadata.metainfo.metc.cntinfo.cntaddr.address.text = config_object["address"]
        
        self.metadata.idinfo.ptcontac.cntinfo.cntaddr.city.text = config_object["city"]
        self.metadata.metainfo.metc.cntinfo.cntaddr.city.text = config_object["city"]
        
        self.metadata.idinfo.ptcontac.cntinfo.cntaddr.state.text = config_object["state"]
        self.metadata.metainfo.metc.cntinfo.cntaddr.state.text = config_object["state"]
        
        self.metadata.idinfo.ptcontac.cntinfo.cntaddr.postal.text = config_object["postal"]
        self.metadata.metainfo.metc.cntinfo.cntaddr.postal.text = config_object["postal"]
        
        self.metadata.idinfo.ptcontac.cntinfo.cntaddr.country.text = config_object["country"]
        self.metadata.metainfo.metc.cntinfo.cntaddr.country.text = config_object["country"]

        self.metadata.idinfo.ptcontac.cntinfo.cntvoice.text = config_object["phone"]
        self.metadata.metainfo.metc.cntinfo.cntvoice.text = config_object["phone"] 
        
        self.metadata.idinfo.ptcontac.cntinfo.cntfax.text = config_object["fax"]
        self.metadata.metainfo.metc.cntinfo.cntfax.text = config_object["fax"]
        
        self.metadata.idinfo.ptcontac.cntinfo.cntemail.text = config_object["email"]
        self.metadata.metainfo.metc.cntinfo.cntemail[0].text = config_object["email"]
        self.metadata.metainfo.metc.cntinfo.cntemail[1].text = config_object["data_managment_email"]
        
        self.metadata.idinfo.datacred.text = config_object["funding_source"]
        
        
    def _update_processing(self, config_object):
        """
        Update processing steps
        :param config_object: DESCRIPTION
        :type config_object: TYPE
        :return: DESCRIPTION
        :rtype: TYPE

        """
        self.metadata.dataqual.lineage.clear_children("procstep")
        for step in [k for k in config_object.keys() if "step" in k]:
            index = int(step[-2:])
            date = config_object[f"date_{index:02}"].replace("-", "")

            xml_utils.XMLNode(
                tag="procstep", 
                parent_node=self.metadata.dataqual.lineage, 
                index=index - 1)

            xml_utils.XMLNode(
                tag="procdesc", 
                text=config_object[step],
                parent_node=self.metadata.dataqual.lineage.procstep[index + 1], 
                index=0)
            
            xml_utils.XMLNode(
                tag="procdate", 
                text=date,
                parent_node=self.metadata.dataqual.lineage.procstep[index + 1], 
                index=1)
            
    def _update_attachments(self, config_object):
        """
        Update processing steps
        :param config_object: DESCRIPTION
        :type config_object: TYPE
        :return: DESCRIPTION
        :rtype: TYPE

        """
        self.metadata.eainfo.clear_children("overview")
        count = len(self.metadata.eainfo.detailed.attr)

        for ii, ext in enumerate(["edi", "png", "guide"]):
            overview = xml_utils.XMLNode(
                tag="overview", 
                parent_node=self.metadata.eainfo, 
                index=ii + count)
    
            xml_utils.XMLNode(
                tag="eaover", 
                text=config_object[f"{ext}.fn"],
                parent_node=overview, 
                index=0)
            
            xml_utils.XMLNode(
                tag="eadetcit", 
                text=config_object[f"{ext}.description"],
                parent_node=overview, 
                index=1)
            
    def update_dates(self, date=None):
        """
        Update release and metadata dates to input date or if not input the current 
        date
        
        :param date: DESCRIPTION, defaults to None
        :type date: TYPE, optional
        :return: DESCRIPTION
        :rtype: TYPE

        """

        if date is None:
            date = datetime.datetime.utcnow()
            date = date.strftime("%Y%m%d")
            
        self.metadata.metainfo.metd.text = date
        self.metadata.idinfo.citation.citeinfo.pubdate.text = date
        
            
        
        
                    
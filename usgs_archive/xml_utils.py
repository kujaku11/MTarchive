#!/usr/bin/env python
# -*- coding: utf8 -*-
"""
The MetadataWizard(pymdwizard) software was developed by the
U.S. Geological Survey Fort Collins Science Center.
See: https://github.com/usgs/fort-pymdwizard for current project source code
See: https://usgs.github.io/fort-pymdwizard/ for current user documentation
See: https://github.com/usgs/fort-pymdwizard/tree/master/examples
    for examples of use in other scripts

License:            Creative Commons Attribution 4.0 International (CC BY 4.0)
                    http://creativecommons.org/licenses/by/4.0/

PURPOSE
------------------------------------------------------------------------------
Provide a variety of xml processing functions.


SCRIPT DEPENDENCIES
------------------------------------------------------------------------------
    This script is part of the pymdwizard package and is not intented to be
    used independently.  All pymdwizard package requirements are needed.

    See imports section for external packages used in this script as well as
    inter-package dependencies


U.S. GEOLOGICAL SURVEY DISCLAIMER
------------------------------------------------------------------------------
This software has been approved for release by the U.S. Geological Survey
(USGS). Although the software has been subjected to rigorous review,
the USGS reserves the right to update the software as needed pursuant to
further analysis and review. No warranty, expressed or implied, is made by
the USGS or the U.S. Government as to the functionality of the software and
related material nor shall the fact of release constitute any such warranty.
Furthermore, the software is released on condition that neither the USGS nor
the U.S. Government shall be held liable for any damages resulting from
its authorized or unauthorized use.

Any use of trade, product or firm names is for descriptive purposes only and
does not imply endorsement by the U.S. Geological Survey.

Although this information product, for the most part, is in the public domain,
it also contains copyrighted material as noted in the text. Permission to
reproduce copyrighted items for other than personal use must be secured from
the copyright owner.
------------------------------------------------------------------------------
"""
# =============================================================================
# Imports
# =============================================================================
import os
import collections
from collections import OrderedDict
import json
from pathlib import Path
import unicodedata
from dateutil import parser

from defusedxml import lxml
from lxml import etree as etree

import pandas as pd

# =============================================================================
# Global Variables
# =============================================================================
fgdc_dir = Path(__file__).parent.parent.joinpath("fgdc_standards")
FGDC_XSD_NAME = fgdc_dir.joinpath("fgdc-std-001-1998-annotated.xsd")
BDP_LOOKUP = fgdc_dir.joinpath("bdp_lookup.json")

# =============================================================================


def xml_document_loader(xml_locator):
    """

    Parameters
    ----------
    xml_locator : str or lxml element or lxml document
                if str can be one of:
                    file path and name to an xml document
                    string representation of an xml document
                    TODO: add option for url that resolves to an xml document
                lxml element or document

    Returns
    -------
        lxml element
    """

    if isinstance(xml_locator, str):
        if os.path.exists(xml_locator):
            return fname_to_node(xml_locator)
        else:
            return string_to_node(xml_locator)

    else:
        return xml_locator


def save_to_file(element, fn):
    """
    Save the provided element as the filename provided
    Parameters
    ----------
    element : lxml element
    fn : str

    Returns
    -------
    None
    """
    import codecs

    file = codecs.open(fn, "w", "utf-8")

    file.write(node_to_string(element))
    file.close()


def node_to_dict(node, add_fgdc=True):
    """

    Parameters
    ----------
    node : lxml element
    add_fgdc : bool
            if true prepend 'fgdc_' to the front of all tags
    Returns
    -------
        dictionary contain a key value pair for each child item in the node
        where the key is the item's tag and the value is the item's text
    """
    node_dict = collections.OrderedDict()

    if len(node.getchildren()) == 0:
        tag = parse_tag(node.tag)
        if add_fgdc:
            tag = "fgdc_" + tag
        node_dict[tag] = node.text
    else:
        for child in node.getchildren():
            try:
                tag = parse_tag(child.tag)
                if add_fgdc:
                    tag = "fgdc_" + tag
                if len(child.getchildren()) > 0:
                    content = node_to_dict(child, add_fgdc=add_fgdc)
                else:
                    content = child.text
                node_dict[tag] = content
            except AttributeError:
                pass  # thid node was a comment or processing instruction
    return node_dict


def parse_tag(tag):
    """
    strips namespace declaration from xml tag string

    Parameters
    ----------
    tag : str

    Returns
    -------
    formatted tag

    """
    return tag[tag.find("}") + 1 :]


def element_to_list(results):
    """
    Returns the results(etree) formatted into a list of dictionaries.
    This is useful for flat data structures, e.g. homogeneous results that
    could be thought of and converted to a dataframe.

    Parameters
    ----------
    results : list of lxml nodes
        This list would could be returned from an xpath query for example

    Returns
    -------
    List of dictionaries. Each dictionary in this list is the result of
    the _node_to_dict function
    """
    return [node_to_dict(item, add_fgdc=False) for item in results]


def search_xpath(node, xpath, only_first=True):
    """

    Parameters
    ----------
    node : lxml node

    xpath : string
        xpath.search

    only_first : boolean
        flag to indicate return type
        True == only return first element found or None if none found
        False == return list of matches found or [] if none found

    Returns
    -------
    list of lxml nodes
    """

    if type(node) in [
        lxml._etree._Element,
        lxml._etree._ElementTree,
        lxml.RestrictedElement,
    ]:
        matches = node.xpath(xpath)
        if len(matches) == 0:
            if only_first:
                return None
            else:
                return []
        elif len(matches) == 1 and only_first:
            return matches[0]
        elif len(matches) >= 1 and not only_first:
            return matches
        else:
            return matches[0]
    else:
        if only_first:
            return None
        else:
            return []


def get_text_content(node, xpath=""):
    """
    return the text from a specific node

    Parameters
    ----------
    node : lxml node

    xpath : xpath.search

    Returns
    -------
    str
    None if that xpath is not found in the node
    """
    if node is None:
        return None

    if xpath:
        nodes = node.xpath(xpath)
    else:
        nodes = [node]

    if nodes:
        result = nodes[0].text
        if result is None:
            return ""
        else:
            return result
    else:
        return ""


def remove_control_characters(s):
    """
    Removes control characters from string

    Parameters
    ----------
    str: string

    Returns
    -------
    string
    """
    s = str(s)
    return "".join(
        ch for ch in s if unicodedata.category(ch)[0] != "C" or ch in ["\n", "\t"]
    )


def element_to_df(results):
    """
    Returns the results (etree) formatted into a pandas dataframe.
    This only intended to be used on flat data structures, e.g. a list of
    homogeneous elements.
    For nested or hierarchical data structures this result will be awkward.

    Parameters
    ----------
    results : list of lxml nodes
        This list would could be returned from an xpath query for example

    Returns
    -------
    pandas dataframe
    """
    results_list = element_to_list(results)
    return pd.DataFrame.from_dict(results_list)


def node_to_string(node, encoding=True):
    """

    Parameters
    ----------
    node : lxml note

    Returns
    -------

    str :
    Pretty string representation of node
    """
    if not type(node) == etree._ElementTree:
        tree = etree.ElementTree(node)
    else:
        tree = node

    return lxml.tostring(
        tree,
        pretty_print=True,
        with_tail=False,
        encoding="UTF-8",
        xml_declaration=encoding,
    ).decode("utf-8")


def fname_to_node(fn):
    """
    parse the contents of local filename into an lxml node object

    Parameters
    ----------
    fn : str
            full file and path to the the file to load
    Returns
    -------
    lxml node
    """
    return lxml.parse(fn)


def string_to_node(str_node):
    """
    covert a string representation of a node into an lxml node object

    Parameters
    ----------
    str_node : str
               string representation of an XML element

    Returns
    -------
    lxml node
    """
    parser = etree.XMLParser(ns_clean=True, recover=True, encoding="utf-8")
    element = lxml.fromstring(str_node, parser=parser)
    return element


def xml_node(tag, text="", parent_node=None, index=-1, comment=False):
    """
    convenience function for creating an xml node

    Parameters
    ----------
    tag : str
          The tag (e.g. fgdc short name) to be assigned to the node
    text : str, optional
          The text contents of the node.
    parent_node : lxml element, optional
          the node created by this function will be
          appended to this nodes children
    index : int, optional
          The positional index to insert the node at. (zero based)
          If none specified will append node to end of existing children.

    Returns
    -------
        the lxml node created by the function.
    """

    if comment:
        node = etree.Comment()
    else:
        node = etree.Element(tag)

    if text:
        node.text = "{}".format(remove_control_characters(text))

    if parent_node is not None:
        if index == -1:
            parent_node.append(node)
        else:
            parent_node.insert(index, node)

    return node


def load_xslt(fn):
    return etree.XSLT(fname_to_node(fn))


def load_schema(fn):
    return etree.XMLSchema(fname_to_node(fn))


def clear_children(element):
    """
    Removes all child elements from the element passed
    Parameters
    ----------
    element : lxml element

    Returns
    -------
    None
    """
    for child in element.getchildren():
        element.remove(child)


class XMLRecord(object):
    def __init__(self, fn=None):
        """
        contents must be one of the following

        1) File path/name on the local filesystem that exists and can be read
        2) String containing an XML Record.

        Parameters
        ----------
        contents : str, lxml node
                url, file path, string xml snippet
        """
        self.tag = None
        self.record = None
        self._root = None
        self._contents = None
        self.fn = fn

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        if self.tag:
            return self.__dict__[self.tag].__str__()
        return "No Metadata"

    def serialize(self):
        return self.__str__()

    @property
    def fn(self):
        return self._fn

    @fn.setter
    def fn(self, value):
        if value is None:
            self._fn = None
        else:
            self._fn = Path(value)
            if self._fn.exists():
                self.read(self._fn)

    def read(self, fn):
        """
        Read xml file
        """
        self.record = lxml.parse(self.fn.as_posix())
        self._root = self.record.getroot()
        self.tag = self._root.tag
        self.__dict__[self._root.tag] = XMLNode(self.record.getroot())
        self._contents = self.__dict__[self._root.tag]

    def save(self, fn=""):
        if not fn:
            fn = self.fn
        save_to_file(self._contents.to_xml(), fn)

    def validate(self, schema="fgdc", as_dataframe=True):
        """
        Returns a list of schema validation errors for a given CSDGM XML file.

        Parameters
        ----------
        xsl_fname : str (optional)
            can be one of:
            'fgdc' - uses the standard fgdc schema
                    ../resources/FGDC/fgdc-std-001-1998-annotated.xsd
            'bdp' = use the Biological Data profile schema,
                    ../resources/FGDC/BDPfgdc-std-001-1998-annotated.xsd
            full file path to another local schema.

            if not specified defaults to 'fgdc'
        as_dataframe : bool
            used to specify return format (list of tuples or dataframe)

        Returns
        -------
            list of tuples
            (xpath, error message, line number)
            or
            pandas dataframe
        """

        df = validate_xml(
            self._contents.to_xml(), xsl_fname=schema, as_dataframe=as_dataframe
        )

        lines = ["Error Messages", "=" * 25]
        for entry in df.itertuples():
            lines += [f"\tLine: {entry.line}"]
            lines += [f"\txpath: {entry.xpath}"]
            lines += [f"\t{entry.message}"]
            lines += ["-" * 25]

        print("\n".join(lines))


class XMLNode(object):
    """
    Class used to dynamically create an object containing the contents of an
    XML node, along with functions for manipulating and introspecting it.
    """

    def __init__(self, element=None, tag="", text="", parent_node=None, index=-1):
        """
        Initialization function.

        Parameters
        ----------
        element : xml element, optional (one of tag or element must be used)

        tag : str, optional (one of tag or element must be used)
              The string to use for the element tag
        text : str
               The text contents of the element
        parent_node : XMLNode, optional
                      if provided add this XMLNode to the parent node
        index : int, optional
                if provided insert this XMLNode into the parent node at this
                position
        """
        self.text = text
        self.tag = tag
        self.children = []

        if isinstance(element, etree._Element):
            self.from_xml(element)
        elif tag:
            element = xml_node(tag=tag, text=text)
            self.from_xml(element)
        elif type(element) == str:
            self.from_str(element)

        if parent_node is not None:
            parent_node.add_child(self, index=index, deepcopy=False)

    def __repr__(self):
        """
        return representation of this object

        Returns
        -------
        str representation of this element, pretty print of entire contents.
        """
        return self.__str__()

    def __str__(self, level=0):
        """

        Parameters
        ----------
        level : int
                Number of double spaces "  " to indent the resulting output to

        Returns
        -------
        str representation of this element, pretty print of entire contents.
        """
        if self.text:
            cur_node = xml_node(self.tag, self.text)
            result = "{}{}".format(
                "  " * level, lxml.tostring(cur_node, pretty_print=True).decode()
            )
            result = result.rstrip()
        else:
            result = "{}<{}>".format("  " * level, self.tag)
            for child in self.children:
                if type(self.__dict__[child.tag]) == XMLNode:
                    child = self.__dict__[child.tag]
                result += "\n" + child.__str__(level=level + 1)
            result += "\n{}</{}>".format("  " * level, self.tag)
        return result

    def __eq__(self, other):
        """
        Check equality of XMLNode objects by comparing
        their string representations

        Parameters
        ----------
        other : Second XMLNode object to compare self to

        Returns
        -------
        bool
        """
        if isinstance(other, self.__class__):
            return self.to_str() == other.to_str()
        return False

    def from_xml(self, element):
        """

        Parameters
        ----------
        element

        Returns
        -------

        """
        self.element = element
        self.tag = element.tag
        self.add_attr(self.tag, self)
        try:
            self.text = element.text.strip()
        except:
            self.text = ""

        self.children = []
        for child_node in self.element.getchildren():
            child_object = XMLNode(child_node)
            self.children.append(child_object)
            self.add_attr(child_node.tag, child_object)

    def add_attr(self, tag, child_object):
        """
        Add a child XMLNode to this object's attributes.
        If there is already a child with this tag, make that
        child a list containing the previous item, and append this chils


        Parameters
        ----------
        tag : str
              the tag of the XMLNode
        child_object : XMLNode
                       The node to add to this object
        Returns
        -------
        None
        """
        if tag in self.__dict__:
            cur_contents = self.__dict__[tag]
            if type(cur_contents) == list:
                cur_contents.append(child_object)
            else:
                self.__dict__[tag] = [cur_contents, child_object]
        else:
            self.__dict__[tag] = child_object

    def to_xml(self):
        """
        Return lxml element version of self

        Returns
        -------
        lxml element
        """
        str_element = self.to_str()
        element = string_to_node(str_element)
        return element

    def from_str(self, str_element):
        """

        Parameters
        ----------
        str_element : str
                      xml element serialized as a string
        Returns
        -------

        """
        parser = etree.XMLParser(ns_clean=True, recover=True, encoding="utf-8")
        element = lxml.fromstring(str_element, parser=parser)
        self.from_xml(element)

    def to_str(self):
        """
        return __str__ representation of self

        Returns
        -------
        str
        """
        return self.__str__()

    def search_xpath(self, xpath=""):
        """
        Parses an xpath and recursively searches this object for matching
        elements

        Parameters
        ----------
        xpath : str
                The xpath that will be searched, can contain tags and indexes
                only

        Returns
        -------
        list of matching elements
        """
        if not xpath:
            return self

        xpath_items = xpath.split("/")
        if len(xpath_items) == 1:
            xpath_remainder = ""
        else:
            xpath_remainder = "/".join(xpath_items[1:])
        first_item = xpath_items[0]
        try:
            tag, index = split_tag(first_item)
            results = self.__dict__[tag]
            if "[" in first_item:
                first_result = results[index]
                return first_result.search_xpath(xpath_remainder)
            else:
                if type(results) == list:
                    aggregator = []
                    for result in results:
                        node = result.search_xpath(xpath_remainder)
                        if node is not None:
                            aggregator.append(node)
                    return aggregator
                else:
                    return results.search_xpath(xpath_remainder)
        except:
            return []

    def xpath(self, xpath="", as_list=True, as_text=False):
        """
        Convenience function for calling self.xpath but specifying the format
        to return results in

        Parameters
        ----------
        xpath : str
                the xpath to search
        as_list : bool
                 Whether to return a list regardless of how many matching
                 elements are found
        as_text : bool
                  Whether to return the text of the first matching element
                  only

        Returns
        -------
        XMLNode, list of XMLNodes, or str
        """
        results = self.search_xpath(xpath)
        if as_list and not type(results) == list:
            results = [results]

        if as_text:
            results = [r.text for r in results if r]

        return results

    def xpath_march(self, xpath, as_list=True):
        """
        for a given xpath, return the most distant matching element
        iteratively searches an xpath until a match is found removing the last
        element each time.  An iterative version of xpath.

        Parameters
        ----------
        xpath : str
                the xpath to search
        as_list : bool
                  Whether to return the text of the first matching element
                  only

        Returns
        -------

        """
        xpath_items = xpath.split("/")

        while xpath_items:
            result = self.xpath("/".join(xpath_items), as_list=as_list)
            if result:
                return result
            xpath_items.pop()

        return []

    def clear_children(self, tag=None):
        """
        Remove the children of this object.  If tag==None all children will be
        removed.  If a specific tag is passed only the children with a matching
        tag will be removed.

        Parameters
        ----------
        tag : str, optional
              The tag to lookfor and remove.  Non-matching tags will be kept

        Returns
        -------
        None
        """
        if tag is not None:
            self.children = [c for c in self.children if c.tag != tag]
        else:
            self.children = []

    def replace_child(self, new_child, tag=None, deepcopy=True):
        """
        Replaces a given child

        Parameters
        ----------
        tag : Str (optional)
            The child node tag that will be replaced.
            If not supplied the tag of the child node will be used.
        new_child : XMLNode
            The child to swap into this object
        deepcopy : bool
            Whether to use the exact child object passed or
            a copy of it.

        Returns
        -------
        None
        """
        if tag is None:
            tag = new_child.tag
        for i, child in enumerate(self.children):
            if child.tag == tag:
                del self.children[i]
                self.add_child(new_child, i, deepcopy=deepcopy)

    def find_string(self, string, ignorecase=False):
        """
        Return a list of all nodes that contain a string match of 'string'

        Parameters
        ----------
        string : str
                 The string to search for in record.
        ignorecase : bool
                     Flag to match case or not

        Returns
        -------

        list of XMLNodes with text elements containing string
        """
        found = []
        if ignorecase and string.lower() in self.text.lower():
            found.append(self)
        elif string in self.text:
            found.append(self)

        for child in self.children:
            found += child.find_string(string, ignorecase)

        return found

    def replace_string(self, old, new, maxreplace=None, deep=True):
        """
        String replacement function for the text of a node.

        Parameters
        ----------
        old : str
              The string to find
        new : str
              The string to replace 'old' with
        maxreplace : int (optional)
                     The first maxreplace occurrences are replace (per node)
                     if not provided then all occurrences are replaced.
        deep : bool
               To apply replace on all child nodes as well (recursive).

        Returns
        -------
        int : The number of occurrences found

        """
        count_found = self.text.count(old)

        if maxreplace is None:
            self.text = self.text.replace(old, new)
        else:
            if count_found > maxreplace:
                count_found = maxreplace
            self.text = self.text.replace(old, new, maxreplace)

        if deep:
            for child in self.children:
                count_found += child.replace_string(old, new, maxreplace, deep)

        return count_found

    def add_child(self, child, index=-1, deepcopy=True):
        """
        Add a child element to this object.

        Parameters
        ----------
        child : XML element
            The child element to be added to this object
        index : int, optional
            What position (zero based) to add the child element at
        deepcopy : bool
            Whether to use the exact child object passed or
            a copy of it.

        Returns
        -------
        None
        """
        if index == -1:
            index = len(self.children)
        if index < -1:
            index += 1

        if type(child) == etree._Element:
            node_str = node_to_string(child, encoding=False)
        else:
            node_str = child.to_str()
        child_copy = XMLNode(node_str)

        if deepcopy:
            self.children.insert(index, child_copy)
        else:
            self.children.insert(index, child)
        self.add_attr(child.tag, child)

    def copy(self):
        """
        Return a duplicate (deepcopy) of this object

        Returns
        -------
        XMLNode
        """
        node_str = self.to_str()
        self_copy = XMLNode(node_str)
        return self_copy


def split_tag(tag):
    """
    parse an xml tag into the tag itself and the tag index

    Parameters
    ----------
    tag : str
        xml tag that might or might not have a [n] item

    Returns
    -------
    tuple: fgdc_tag, index
    """
    if "[" in tag:
        fgdc_tag, tag = tag.split("[")
        index = int(tag.split("]")[0]) - 1
    else:
        fgdc_tag = tag
        index = 0
    return fgdc_tag, index


def validate_xml(xml, xsl_fname="fgdc", as_dataframe=False):
    """

    Parameters
    ----------
    xml : lxml document
                or
          filename
                or
          string containing xml representation

    xsl_fname : str (optional)
                can be one of:
                'fgdc' - uses the standard fgdc schema
                        ../resources/FGDC/fgdc-std-001-1998-annotated.xsd
                full file path to another local schema.

                if not specified defaults to 'fgdc'
    as_dataframe : bool
                used to specify return format (list of tuples or dataframe)

    Returns
    -------
        list of tuples
        (xpath, error message, line number)
        or
        pandas dataframe
    """

    if xsl_fname.lower() == "fgdc":
        xsl_fname = FGDC_XSD_NAME
    else:
        xsl_fname = xsl_fname

    xmlschema = load_schema(xsl_fname.as_posix())
    xml_doc = xml_document_loader(xml)
    xml_str = node_to_string(xml_doc)

    tree_node = string_to_node(xml_str.encode("utf-8"))
    lxml._etree._ElementTree(tree_node)

    errors = []
    srcciteas = []

    src_xpath = "dataqual/lineage/srcinfo/srccitea"
    src_nodes = tree_node.xpath(src_xpath)
    for i, src in enumerate(src_nodes):
        srcciteas.append(src.text)
        if src.text is None:
            if len(src_nodes) == 1:
                errors.append(
                    (
                        "metadata/" + src_xpath,
                        "source citation abbreviation cannot be empty",
                        1,
                    )
                )
            else:
                xpath = "metadata/dataqual/lineage/srcinfo[{}]/srccitea"
                errors.append(
                    (
                        xpath.format(i + 1),
                        "source citation abbreviation cannot be empty",
                        1,
                    )
                )
    procstep_xpath = "dataqual/lineage/procstep"
    procstep_nodes = tree_node.xpath(procstep_xpath)
    for proc_i, proc in enumerate(procstep_nodes):
        srcprod_nodes = proc.xpath("srcprod")
        for srcprod_i, srcprod in enumerate(srcprod_nodes):
            srcciteas.append(srcprod.text)
            if srcprod.text is None:
                error_xpath = procstep_xpath
                if len(procstep_nodes) > 1:
                    error_xpath += "[{}]".format(proc_i + 1)
                error_xpath += "/srcprod"
                if len(srcprod_nodes) > 1:
                    error_xpath += "[{}]".format(proc_i + 1)
                errors.append(
                    (
                        "metadata/" + error_xpath,
                        "source produced abbreviation cannot be empty",
                        1,
                    )
                )

    srcused_xpath = "dataqual/lineage/procstep/srcused"
    srcused_nodes = tree_node.xpath(srcused_xpath)
    for i, src in enumerate(srcused_nodes):
        if src.text not in srcciteas:
            if len(srcused_nodes) == 1:
                errors.append(
                    (
                        "metadata/" + srcused_xpath,
                        "Source Used Citation Abbreviation {} "
                        "not found in Source inputs "
                        "used".format(src.text),
                        1,
                    )
                )
            else:
                xpath = "metadata/dataqual/lineage/procstep[{}]/srcused"
                errors.append(
                    (
                        xpath.format(i + 1),
                        "Source Used Citation Abbreviation {} "
                        "not found in Source inputs "
                        "used".format(src.text),
                        1,
                    )
                )

    if xmlschema.validate(tree_node) and not errors:
        return []

    line_lookup = dict(
        [
            (e.sourceline, tree_node.getroottree().getpath(e))
            for e in tree_node.xpath(".//*")
        ]
    )
    sourceline = tree_node.sourceline
    line_lookup[sourceline] = tree_node.getroottree().getpath(tree_node)

    fgdc_lookup = get_fgdc_lookup()

    for error in xmlschema.error_log:
        error_msg = clean_error_message(error.message, fgdc_lookup)
        try:
            errors.append((line_lookup[error.line][1:], error_msg, error.line))
        except KeyError:
            errors.append(("Unknown", error_msg, error.line))

    errors = list(OrderedDict.fromkeys(errors))

    if as_dataframe:
        cols = ["xpath", "message", "line"]
        return pd.DataFrame.from_records(errors, columns=cols)
    else:
        return errors


def get_fgdc_lookup():
    """
    Loads the local resource, 'bdp_lookup' into a json object

    Returns
    -------
        json fgdc item lookup
    """
    annotation_lookup_fname = BDP_LOOKUP
    try:
        with open(annotation_lookup_fname, encoding="utf-8") as data_file:
            annotation_lookup = json.loads(data_file.read())
    except TypeError:
        with open(annotation_lookup_fname) as data_file:
            annotation_lookup = json.loads(data_file.read())

    return annotation_lookup


def clean_error_message(message, fgdc_lookup=None):
    """
    Returns a cleaned up, more informative translation
    of a raw xml schema error message.
    Empty or missing elements are described in plain English

    Parameters
    ----------
    message : str
              The raw message we will be cleaning up

    Returns
    -------
        str : cleaned up error message
    """
    parts = message.split()
    if "Missing child element" in message:
        clean_message = (
            f"The {parts[1][:-1]} is missing the expected element(s) '{parts[-2]}'"
        )
    elif (
        r"' is not accepted by the pattern '\s*\S(.|\n|\r)*'" in message
        or "'' is not a valid value of the atomic type" in message
    ):
        shortname = parts[1][:-1].replace("'", "")
        try:
            longname = fgdc_lookup[shortname]["long_name"]
        except (KeyError, TypeError):
            longname = None

        if longname is None:
            name = shortname
        else:
            name = "{} ({})".format(longname, shortname)

        clean_message = "The value for {} cannot be empty"
        clean_message = clean_message.format(name)
    else:
        clean_message = message
    return clean_message


def format_date(date_input):
    """
    Convert a Python date object into an FGDC string format YYYYMMDD

    Parameters
    ----------
    date_input : str or datetime
            if str provided must be in format that dateutil's parser can handle
    Returns
    -------
        str : date formated in FGDC YYYYMMDD format
    """

    if type(date_input) == str:
        date_input = parser.parse(date_input)

    return date_input.strftime("%Y%m%d")


def format_time(date_time_str):
    """
        get time string
        """
    dt = parser.parse(date_time_str)

    return dt.strftime("%H%M%S%f")[:10] + "Z"

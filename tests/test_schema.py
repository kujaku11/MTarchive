# -*- coding: utf-8 -*-
"""
Tests for Schema module

Created on Tue Apr 28 18:08:40 2020

@author: jpeacock
"""

# =============================================================================
# Imports
# =============================================================================

import unittest
from mth5.standards import schema
from mth5.utils.exceptions import MTSchemaError

# =============================================================================
# Tests
# =============================================================================
class TestValidators(unittest.TestCase):
    def setUp(self):
        self.name = 'test'
        self.type = str
        self.style = 'name'
        self.header = ['attribute', 'type', 'required', 'units', 'style']
        self.required = True
        self.units = 'mv'
        self.value_dict = {'type': self.type,
                           'required': self.required,
                           'units': self.units,
                           'style': self.style}
        
        self.name_fail = '0test'
        self.type_fail = 'value'
        self.style_fail = 'fancy'
        self.header_fail = ['type', 'required', 'units']
        self.required_fail = 'Negative'
        self.units_fail = 10
        self.value_dict_fail = {'type': self.type_fail,
                           'required': self.required_fail,
                           'units': self.units_fail,
                           'style': self.style_fail}
        
    def test_header_with_attribute(self):
        self.assertListEqual(sorted(self.header), 
                             sorted(schema.validate_header(self.header, 
                                                           attribute=True)))
    def test_header_without_attribute(self):
        self.assertListEqual(sorted(self.header[1:]), 
                             sorted(schema.validate_header(self.header[1:],
                                                           attribute=False)))
    def test_header_fail(self):
        self.assertRaises(MTSchemaError, 
                          schema.validate_header, 
                          self.header_fail)
        
    def test_validate(self):
        self.assertEqual(self.required,
                         schema.validate_required(self.required))
        self.assertEqual(self.required,
                         schema.validate_required(str(self.required)))
        
    def test_validate_fail(self):
        self.assertRaises(MTSchemaError,
                          schema.validate_required, 
                          self.required_fail)
        
    def test_validate_type(self):
        self.assertEqual('string', schema.validate_type(str))
        self.assertEqual('float', schema.validate_type(float))
        self.assertEqual('integer', schema.validate_type(int))
        self.assertEqual('boolean', schema.validate_type(bool))
        
    def test_validate_type_fail(self):
        self.assertRaises(MTSchemaError, 
                          schema.validate_type,
                          self.type_fail)
        
                
        
# =============================================================================
# Run
# =============================================================================
if __name__ == '__main__':
    unittest.main()
    
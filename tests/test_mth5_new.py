# -*- coding: utf-8 -*-
"""
Created on Fri May 29 15:49:44 2020

@author: jpeacock
"""

import unittest
from mth5 import mth5
from pathlib import Path

class TestMTH5(unittest.TestCase):
    
    def setUp(self):
        fn = Path('c:\Users\jpeacock\Documents\GitHub\MTarchive\tests\test.mth5')
        self.mth5_obj = mth5.MTH5()
        self.mth5_obj.open_mth5(fn, mode='w')
        
    def test_initialized_groups(self):
        initial_groups = list(sorted(self.mth5_obj.keys()))
        self.assertListEqual(initial_groups, 
                             list(sorted(self.mth5_obj.default_groups)))
        
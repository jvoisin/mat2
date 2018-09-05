#!/usr/bin/python3

import unittest
import shutil
import os

from libmat2 import office

class TestPolicy(unittest.TestCase):
    def test_policy_omit(self):
        shutil.copy('./tests/data/embedded.docx', './tests/data/clean.docx')
        p = office.MSOfficeParser('./tests/data/clean.docx')
        p.unknown_member_policy = 'omit'
        self.assertTrue(p.remove_all())
        os.remove('./tests/data/clean.docx')

    def test_policy_keep(self):
        shutil.copy('./tests/data/embedded.docx', './tests/data/clean.docx')
        p = office.MSOfficeParser('./tests/data/clean.docx')
        p.unknown_member_policy = 'keep'
        self.assertTrue(p.remove_all())
        os.remove('./tests/data/clean.docx')

    def test_policy_unknown(self):
        shutil.copy('./tests/data/embedded.docx', './tests/data/clean.docx')
        p = office.MSOfficeParser('./tests/data/clean.docx')
        p.unknown_member_policy = 'unknown_policy_name_totally_invalid'
        with self.assertRaises(ValueError):
            p.remove_all()
        os.remove('./tests/data/clean.docx')


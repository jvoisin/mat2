#!/usr/bin/env python3

import unittest
import shutil
import os

from libmat2 import office, UnknownMemberPolicy

class TestPolicy(unittest.TestCase):
    def test_policy_omit(self):
        shutil.copy('./tests/data/embedded.docx', './tests/data/clean.docx')
        p = office.MSOfficeParser('./tests/data/clean.docx')
        p.unknown_member_policy = UnknownMemberPolicy.OMIT
        self.assertTrue(p.remove_all())
        os.remove('./tests/data/clean.docx')
        os.remove('./tests/data/clean.cleaned.docx')

    def test_policy_keep(self):
        shutil.copy('./tests/data/embedded.docx', './tests/data/clean.docx')
        p = office.MSOfficeParser('./tests/data/clean.docx')
        p.unknown_member_policy = UnknownMemberPolicy.KEEP
        self.assertTrue(p.remove_all())
        os.remove('./tests/data/clean.docx')
        os.remove('./tests/data/clean.cleaned.docx')

    def test_policy_unknown(self):
        shutil.copy('./tests/data/embedded.docx', './tests/data/clean.docx')
        p = office.MSOfficeParser('./tests/data/clean.docx')
        with self.assertRaises(ValueError):
            p.unknown_member_policy = UnknownMemberPolicy('unknown_policy_name_totally_invalid')
        os.remove('./tests/data/clean.docx')

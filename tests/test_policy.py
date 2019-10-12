#!/usr/bin/env python3

import unittest
import shutil
import os

from libmat2 import office, UnknownMemberPolicy

class TestPolicy(unittest.TestCase):
    target = './tests/data/clean.docx'

    def test_policy_omit(self):
        shutil.copy('./tests/data/embedded.docx', self.target)
        p = office.MSOfficeParser(self.target)
        p.unknown_member_policy = UnknownMemberPolicy.OMIT
        self.assertTrue(p.remove_all())
        os.remove(p.filename)

    def test_policy_keep(self):
        shutil.copy('./tests/data/embedded.docx', self.target)
        p = office.MSOfficeParser(self.target)
        p.unknown_member_policy = UnknownMemberPolicy.KEEP
        self.assertTrue(p.remove_all())
        os.remove(p.filename)
        os.remove(p.output_filename)

    def test_policy_unknown(self):
        shutil.copy('./tests/data/embedded.docx', self.target)
        p = office.MSOfficeParser(self.target)
        with self.assertRaises(ValueError):
            p.unknown_member_policy = UnknownMemberPolicy('unknown_policy_name_totally_invalid')
        os.remove(p.filename)

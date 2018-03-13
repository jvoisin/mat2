#!/usr/bin/python3

import unittest
import shutil
import os

from src import parsers
from src.parsers import pdf

class TestGetMeta(unittest.TestCase):
    def test_pdf(self):
        p = pdf.PDFParser('./tests/data/dirty.pdf')
        meta = p.get_meta().items()


class TestCleaning(unittest.TestCase):
    def setUp(self):
        shutil.copy('./tests/data/dirty.pdf', './tests/data/clean.pdf')

    def tearDown(self):
        #os.remove('./tests/data/clean.pdf')
        pass

    def test_pdf(self):
        p = pdf.PDFParser('./tests/data/clean.pdf')
        p.remove_all()
        #self.assertEqual(p.get_meta(), {})

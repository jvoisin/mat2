#!/usr/bin/python3

import unittest
import shutil
import os

from src import parsers
from src.parsers import pdf

class TestGetMeta(unittest.TestCase):
    def test_pdf(self):
        p = pdf.PDFParser('./tests/data/dirty.pdf')
        meta = p.get_meta()
        self.assertEqual(meta['producer'], 'pdfTeX-1.40.14')
        self.assertEqual(meta['creator'], "'Certified by IEEE PDFeXpress at 03/19/2016 2:56:07 AM'")

class TestCleaning(unittest.TestCase):
    def setUp(self):
        shutil.copy('./tests/data/dirty.pdf', './tests/data/clean.pdf')

    def tearDown(self):
        os.remove('./tests/data/clean.pdf')

    def test_pdf(self):
        p = pdf.PDFParser('./tests/data/clean.pdf')

        meta = p.get_meta()
        self.assertEqual(meta['producer'], 'pdfTeX-1.40.14')

        ret = p.remove_all()
        self.assertTrue(ret)

        p = pdf.PDFParser('./tests/data/clean.pdf.cleaned')
        expected_meta = {'creation-date': -1, 'format': 'PDF-1.5', 'mod-date': -1}
        self.assertEqual(p.get_meta(), expected_meta)

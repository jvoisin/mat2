#!/usr/bin/python3

import unittest
import shutil
import os

from src import parsers
from src.parsers import pdf, png, jpg

class TestGetMeta(unittest.TestCase):
    def test_pdf(self):
        p = pdf.PDFParser('./tests/data/dirty.pdf')
        meta = p.get_meta()
        self.assertEqual(meta['producer'], 'pdfTeX-1.40.14')
        self.assertEqual(meta['creator'], "'Certified by IEEE PDFeXpress at 03/19/2016 2:56:07 AM'")

    def test_png(self):
        p = png.PNGParser('./tests/data/dirty.png')
        meta = p.get_meta()
        self.assertEqual(meta['Comment'], 'This is a comment, be careful!')
        self.assertEqual(meta['ModifyDate'], "2018:03:20 21:59:25")

    def test_jpg(self):
        p = jpg.JPGParser('./tests/data/dirty.jpg')
        meta = p.get_meta()
        self.assertEqual(meta['Comment'], 'Created with GIMP')

class TestCleaning(unittest.TestCase):
    def test_pdf(self):
        shutil.copy('./tests/data/dirty.pdf', './tests/data/clean.pdf')
        p = pdf.PDFParser('./tests/data/clean.pdf')

        meta = p.get_meta()
        self.assertEqual(meta['producer'], 'pdfTeX-1.40.14')

        ret = p.remove_all()
        self.assertTrue(ret)

        p = pdf.PDFParser('./tests/data/clean.pdf.cleaned')
        expected_meta = {'creation-date': -1, 'format': 'PDF-1.5', 'mod-date': -1}
        self.assertEqual(p.get_meta(), expected_meta)

        os.remove('./tests/data/clean.pdf')

    def test_png(self):
        shutil.copy('./tests/data/dirty.png', './tests/data/clean.png')
        p = png.PNGParser('./tests/data/clean.png')

        meta = p.get_meta()
        self.assertEqual(meta['Comment'], 'This is a comment, be careful!')

        ret = p.remove_all()
        self.assertTrue(ret)

        p = png.PNGParser('./tests/data/clean.png.cleaned')
        self.assertEqual(p.get_meta(), {})

        os.remove('./tests/data/clean.png')


    def test_jpg(self):
        shutil.copy('./tests/data/dirty.jpg', './tests/data/clean.jpg')
        p = jpg.JPGParser('./tests/data/clean.jpg')

        meta = p.get_meta()
        self.assertEqual(meta['Comment'], 'Created with GIMP')

        ret = p.remove_all()
        self.assertTrue(ret)

        p = jpg.JPGParser('./tests/data/clean.jpg.cleaned')
        self.assertEqual(p.get_meta(), {})

        os.remove('./tests/data/clean.jpg')

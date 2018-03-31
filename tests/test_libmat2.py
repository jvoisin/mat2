#!/usr/bin/python3

import unittest
import shutil
import os

from src import pdf, png, jpg, audio, office

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

    def test_mp3(self):
        p = audio.MP3Parser('./tests/data/dirty.mp3')
        meta = p.get_meta()
        self.assertEqual(meta['TXXX:I am a '], ['various comment'])

    def test_ogg(self):
        p = audio.OGGParser('./tests/data/dirty.ogg')
        meta = p.get_meta()
        self.assertEqual(meta['TITLE'], ['I am so'])

    def test_flac(self):
        p = audio.FLACParser('./tests/data/dirty.flac')
        meta = p.get_meta()
        self.assertEqual(meta['TITLE'], ['I am so'])

    def test_docx(self):
        p = office.OfficeParser('./tests/data/dirty.docx')
        meta = p.get_meta()
        self.assertEqual(meta['cp:lastModifiedBy'], 'Julien Voisin')
        self.assertEqual(meta['dc:creator'], 'julien voisin')
        self.assertEqual(meta['Application'], 'LibreOffice/5.4.5.1$Linux_X86_64 LibreOffice_project/40m0$Build-1')


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

    def test_mp3(self):
        shutil.copy('./tests/data/dirty.mp3', './tests/data/clean.mp3')
        p = audio.MP3Parser('./tests/data/clean.mp3')

        meta = p.get_meta()
        self.assertEqual(meta['TXXX:I am a '], ['various comment'])

        ret = p.remove_all()
        self.assertTrue(ret)

        p = audio.MP3Parser('./tests/data/clean.mp3.cleaned')
        self.assertEqual(p.get_meta(), {})

        os.remove('./tests/data/clean.mp3')

    def test_ogg(self):
        shutil.copy('./tests/data/dirty.ogg', './tests/data/clean.ogg')
        p = audio.OGGParser('./tests/data/clean.ogg')

        meta = p.get_meta()
        self.assertEqual(meta['TITLE'], ['I am so'])

        ret = p.remove_all()
        self.assertTrue(ret)

        p = audio.OGGParser('./tests/data/clean.ogg.cleaned')
        self.assertEqual(p.get_meta(), {})

        os.remove('./tests/data/clean.ogg')

    def test_flac(self):
        shutil.copy('./tests/data/dirty.flac', './tests/data/clean.flac')
        p = audio.FLACParser('./tests/data/clean.flac')

        meta = p.get_meta()
        self.assertEqual(meta['TITLE'], ['I am so'])

        ret = p.remove_all()
        self.assertTrue(ret)

        p = audio.FLACParser('./tests/data/clean.flac.cleaned')
        self.assertEqual(p.get_meta(), {})

        os.remove('./tests/data/clean.flac')

    def test_office(self):
        shutil.copy('./tests/data/dirty.docx', './tests/data/clean.docx')
        p = office.OfficeParser('./tests/data/clean.docx')

        meta = p.get_meta()
        self.assertIsNotNone(meta)

        ret = p.remove_all()
        self.assertTrue(ret)

        p = office.OfficeParser('./tests/data/clean.docx.cleaned')
        self.assertEqual(p.get_meta(), {})

        os.remove('./tests/data/clean.docx')

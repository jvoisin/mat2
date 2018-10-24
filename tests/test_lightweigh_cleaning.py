#!/usr/bin/env python3

import unittest
import shutil
import os

from libmat2 import pdf, images, torrent

class TestLightWeightCleaning(unittest.TestCase):
    def test_pdf(self):
        shutil.copy('./tests/data/dirty.pdf', './tests/data/clean.pdf')
        p = pdf.PDFParser('./tests/data/clean.pdf')

        meta = p.get_meta()
        self.assertEqual(meta['producer'], 'pdfTeX-1.40.14')

        p.lightweight_cleaning = True
        ret = p.remove_all()
        self.assertTrue(ret)

        p = pdf.PDFParser('./tests/data/clean.cleaned.pdf')
        expected_meta = {'creation-date': -1, 'format': 'PDF-1.5', 'mod-date': -1}
        self.assertEqual(p.get_meta(), expected_meta)

        os.remove('./tests/data/clean.pdf')
        os.remove('./tests/data/clean.cleaned.pdf')

    def test_png(self):
        shutil.copy('./tests/data/dirty.png', './tests/data/clean.png')
        p = images.PNGParser('./tests/data/clean.png')

        meta = p.get_meta()
        self.assertEqual(meta['Comment'], 'This is a comment, be careful!')

        p.lightweight_cleaning = True
        ret = p.remove_all()
        self.assertTrue(ret)

        p = images.PNGParser('./tests/data/clean.cleaned.png')
        self.assertEqual(p.get_meta(), {})

        p = images.PNGParser('./tests/data/clean.png')
        p.lightweight_cleaning = True
        ret = p.remove_all()
        self.assertTrue(ret)

        os.remove('./tests/data/clean.png')
        os.remove('./tests/data/clean.cleaned.png')

    def test_jpg(self):
        shutil.copy('./tests/data/dirty.jpg', './tests/data/clean.jpg')
        p = images.JPGParser('./tests/data/clean.jpg')

        meta = p.get_meta()
        self.assertEqual(meta['Comment'], 'Created with GIMP')

        p.lightweight_cleaning = True
        ret = p.remove_all()
        self.assertTrue(ret)

        p = images.JPGParser('./tests/data/clean.cleaned.jpg')
        self.assertEqual(p.get_meta(), {})

        os.remove('./tests/data/clean.jpg')
        os.remove('./tests/data/clean.cleaned.jpg')

    def test_torrent(self):
        shutil.copy('./tests/data/dirty.torrent', './tests/data/clean.torrent')
        p = torrent.TorrentParser('./tests/data/clean.torrent')

        meta = p.get_meta()
        self.assertEqual(meta['created by'], b'mktorrent 1.0')

        p.lightweight_cleaning = True
        ret = p.remove_all()
        self.assertTrue(ret)

        p = torrent.TorrentParser('./tests/data/clean.cleaned.torrent')
        self.assertEqual(p.get_meta(), {})

        os.remove('./tests/data/clean.torrent')
        os.remove('./tests/data/clean.cleaned.torrent')

    def test_tiff(self):
        shutil.copy('./tests/data/dirty.tiff', './tests/data/clean.tiff')
        p = images.TiffParser('./tests/data/clean.tiff')

        meta = p.get_meta()
        self.assertEqual(meta['ImageDescription'], 'OLYMPUS DIGITAL CAMERA         ')

        p.lightweight_cleaning = True
        ret = p.remove_all()
        self.assertTrue(ret)

        p = images.TiffParser('./tests/data/clean.cleaned.tiff')
        self.assertEqual(p.get_meta(),
                {
                    'Orientation': 'Horizontal (normal)',
                    'ResolutionUnit': 'inches',
                    'XResolution': 72,
                    'YResolution': 72
                    }
                )

        os.remove('./tests/data/clean.tiff')
        os.remove('./tests/data/clean.cleaned.tiff')

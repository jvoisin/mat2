#!/usr/bin/env python3

import unittest
import shutil
import os

from libmat2 import pdf, images, torrent


class TestLightWeightCleaning(unittest.TestCase):
    data = [{
            'name': 'pdf',
            'parser': pdf.PDFParser,
            'meta': {'producer': 'pdfTeX-1.40.14'},
            'expected_meta': {'creation-date': -1, 'format': 'PDF-1.5', 'mod-date': -1},
            }, {
                'name': 'png',
                'parser': images.PNGParser,
                'meta': {'Comment': 'This is a comment, be careful!'},
                'expected_meta': {},
            }, {
                'name': 'jpg',
                'parser': images.JPGParser,
                'meta': {'Comment': 'Created with GIMP'},
                'expected_meta': {},
            }, {
                'name': 'torrent',
                'parser': torrent.TorrentParser,
                'meta': {'created by': b'mktorrent 1.0'},
                'expected_meta': {},
            },{
                'name': 'tiff',
                'parser': images.TiffParser,
                'meta': {'ImageDescription': 'OLYMPUS DIGITAL CAMERA         '},
                'expected_meta': {
                    'Orientation': 'Horizontal (normal)',
                    'ResolutionUnit': 'inches',
                    'XResolution': 72,
                    'YResolution': 72
                    }
            },
        ]

    def test_all(self):
        for case in self.data:
            target = './tests/data/clean.' + case['name']
            shutil.copy('./tests/data/dirty.' + case['name'], target)
            p1 = case['parser'](target)

            meta = p1.get_meta()
            for k, v in case['meta'].items():
                self.assertEqual(meta[k], v)

            p1.lightweight_cleaning = True
            self.assertTrue(p1.remove_all())

            p2 = case['parser'](p1.output_filename)
            self.assertEqual(p2.get_meta(), case['expected_meta'])

            os.remove(target)
            os.remove(p1.output_filename)

    def test_exiftool_overwrite(self):
        target = './tests/data/clean.png'
        shutil.copy('./tests/data/dirty.png', target)

        p1 = images.PNGParser(target)
        p1.lightweight_cleaning = True
        shutil.copy('./tests/data/dirty.png', p1.output_filename)
        self.assertTrue(p1.remove_all())

        p2 = images.PNGParser(p1.output_filename)
        self.assertEqual(p2.get_meta(), {})

        os.remove(target)
        os.remove(p1.output_filename)

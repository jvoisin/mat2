#!/usr/bin/python3

import unittest
import shutil
import os

from libmat2 import pdf, images, audio, office, parser_factory, torrent, harmless


class TestUnsupportedFiles(unittest.TestCase):
    def test_pdf(self):
        shutil.copy('./tests/test_libmat2.py', './tests/clean.py')
        parser, mimetype = parser_factory.get_parser('./tests/data/clean.py')
        self.assertEqual(mimetype, 'text/x-python')
        self.assertEqual(parser, None)
        os.remove('./tests/clean.py')


class TestExplicitelyUnsupportedFiles(unittest.TestCase):
    def test_pdf(self):
        shutil.copy('./tests/test_libmat2.py', './tests/data/clean.py')
        parser, mimetype = parser_factory.get_parser('./tests/data/clean.py')
        self.assertEqual(mimetype, 'text/x-python')
        self.assertEqual(parser, None)
        os.remove('./tests/data/clean.py')


class TestCorruptedFiles(unittest.TestCase):
    def test_pdf(self):
        shutil.copy('./tests/data/dirty.png', './tests/data/clean.png')
        with self.assertRaises(ValueError):
            pdf.PDFParser('./tests/data/clean.png')
        os.remove('./tests/data/clean.png')

    def test_png(self):
        shutil.copy('./tests/data/dirty.pdf', './tests/data/clean.pdf')
        with self.assertRaises(ValueError):
            images.PNGParser('./tests/data/clean.pdf')
        os.remove('./tests/data/clean.pdf')

    def test_png2(self):
        shutil.copy('./tests/test_libmat2.py', './tests/clean.png')
        parser, mimetype = parser_factory.get_parser('./tests/clean.png')
        self.assertIsNone(parser)
        os.remove('./tests/clean.png')

    def test_torrent(self):
        shutil.copy('./tests/data/dirty.png', './tests/data/clean.torrent')
        with self.assertRaises(ValueError):
            torrent.TorrentParser('./tests/data/clean.torrent')

        with open("./tests/data/clean.torrent", "a") as f:
            f.write("trailing garbage")
        with self.assertRaises(ValueError):
            torrent.TorrentParser('./tests/data/clean.torrent')

        os.remove('./tests/data/clean.torrent')

    def test_odg(self):
        shutil.copy('./tests/data/dirty.png', './tests/data/clean.odg')
        with self.assertRaises(ValueError):
            office.LibreOfficeParser('./tests/data/clean.odg')
        os.remove('./tests/data/clean.odg')

    def test_bmp(self):
        shutil.copy('./tests/data/dirty.png', './tests/data/clean.bmp')
        harmless.HarmlessParser('./tests/data/clean.bmp')
        os.remove('./tests/data/clean.bmp')

    def test_docx(self):
        shutil.copy('./tests/data/dirty.png', './tests/data/clean.docx')
        with self.assertRaises(ValueError):
             office.MSOfficeParser('./tests/data/clean.docx')
        os.remove('./tests/data/clean.docx')

    def test_flac(self):
        shutil.copy('./tests/data/dirty.png', './tests/data/clean.flac')
        with self.assertRaises(ValueError):
             audio.FLACParser('./tests/data/clean.flac')
        os.remove('./tests/data/clean.flac')

    def test_mp3(self):
        shutil.copy('./tests/data/dirty.png', './tests/data/clean.mp3')
        with self.assertRaises(ValueError):
             audio.MP3Parser('./tests/data/clean.mp3')
        os.remove('./tests/data/clean.mp3')

    def test_jpg(self):
        shutil.copy('./tests/data/dirty.mp3', './tests/data/clean.jpg')
        with self.assertRaises(ValueError):
             images.JPGParser('./tests/data/clean.jpg')
        os.remove('./tests/data/clean.jpg')

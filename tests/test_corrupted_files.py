#!/usr/bin/env python3

import unittest
import shutil
import os
import logging

from libmat2 import pdf, images, audio, office, parser_factory, torrent
from libmat2 import harmless, video

# No need to logging messages, should something go wrong,
# the testsuite _will_ fail.
logger = logging.getLogger()
logger.setLevel(logging.FATAL)


class TestInexistentFiles(unittest.TestCase):
    def test_ro(self):
        parser, mimetype = parser_factory.get_parser('/etc/passwd')
        self.assertEqual(mimetype, None)
        self.assertEqual(parser, None)

    def test_notaccessible(self):
        parser, mimetype = parser_factory.get_parser('/etc/shadow')
        self.assertEqual(mimetype, None)
        self.assertEqual(parser, None)

    def test_folder(self):
        parser, mimetype = parser_factory.get_parser('./tests/')
        self.assertEqual(mimetype, None)
        self.assertEqual(parser, None)

    def test_inexistingfile(self):
        parser, mimetype = parser_factory.get_parser('./tests/NONEXISTING_FILE')
        self.assertEqual(mimetype, None)
        self.assertEqual(parser, None)

    def test_chardevice(self):
        parser, mimetype = parser_factory.get_parser('/dev/zero')
        self.assertEqual(mimetype, None)
        self.assertEqual(parser, None)

    def test_brokensymlink(self):
        shutil.copy('./tests/test_libmat2.py', './tests/clean.py')
        os.symlink('./tests/clean.py', './tests/SYMLINK')
        os.remove('./tests/clean.py')
        parser, mimetype = parser_factory.get_parser('./tests/SYMLINK')
        self.assertEqual(mimetype, None)
        self.assertEqual(parser, None)
        os.unlink('./tests/SYMLINK')

class TestUnsupportedFiles(unittest.TestCase):
    def test_pdf(self):
        shutil.copy('./tests/test_libmat2.py', './tests/clean.py')
        parser, mimetype = parser_factory.get_parser('./tests/data/clean.py')
        self.assertEqual(mimetype, 'text/x-python')
        self.assertEqual(parser, None)
        os.remove('./tests/clean.py')

class TestCorruptedEmbedded(unittest.TestCase):
    def test_docx(self):
        shutil.copy('./tests/data/embedded_corrupted.docx', './tests/data/clean.docx')
        parser, _ = parser_factory.get_parser('./tests/data/clean.docx')
        self.assertFalse(parser.remove_all())
        self.assertIsNotNone(parser.get_meta())
        os.remove('./tests/data/clean.docx')

    def test_odt(self):
        expected = {
                'create_system': 'Weird',
                'date_time': '2018-06-10 17:18:18',
                'meta.xml': 'harmful content'
                }
        shutil.copy('./tests/data/embedded_corrupted.odt', './tests/data/clean.odt')
        parser, _ = parser_factory.get_parser('./tests/data/clean.odt')
        self.assertFalse(parser.remove_all())
        self.assertEqual(parser.get_meta(), expected)
        os.remove('./tests/data/clean.odt')


class TestExplicitelyUnsupportedFiles(unittest.TestCase):
    def test_pdf(self):
        shutil.copy('./tests/test_libmat2.py', './tests/data/clean.py')
        parser, mimetype = parser_factory.get_parser('./tests/data/clean.py')
        self.assertEqual(mimetype, 'text/x-python')
        self.assertEqual(parser, None)
        os.remove('./tests/data/clean.py')


class TestWrongContentTypesFileOffice(unittest.TestCase):
    def test_office_incomplete(self):
        shutil.copy('./tests/data/malformed_content_types.docx', './tests/data/clean.docx')
        p = office.MSOfficeParser('./tests/data/clean.docx')
        self.assertIsNotNone(p)
        self.assertFalse(p.remove_all())
        os.remove('./tests/data/clean.docx')

    def test_office_broken(self):
        shutil.copy('./tests/data/broken_xml_content_types.docx', './tests/data/clean.docx')
        with self.assertRaises(ValueError):
            office.MSOfficeParser('./tests/data/clean.docx')
        os.remove('./tests/data/clean.docx')

    def test_office_absent(self):
        shutil.copy('./tests/data/no_content_types.docx', './tests/data/clean.docx')
        with self.assertRaises(ValueError):
            office.MSOfficeParser('./tests/data/clean.docx')
        os.remove('./tests/data/clean.docx')

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
        parser, _ = parser_factory.get_parser('./tests/clean.png')
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

        with open("./tests/data/clean.torrent", "w") as f:
            f.write("i-0e")
        with self.assertRaises(ValueError):
            torrent.TorrentParser('./tests/data/clean.torrent')

        with open("./tests/data/clean.torrent", "w") as f:
            f.write("i00e")
        with self.assertRaises(ValueError):
            torrent.TorrentParser('./tests/data/clean.torrent')

        with open("./tests/data/clean.torrent", "w") as f:
            f.write("01:AAAAAAAAA")
        with self.assertRaises(ValueError):
            torrent.TorrentParser('./tests/data/clean.torrent')

        with open("./tests/data/clean.torrent", "w") as f:
            f.write("1:aaa")
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
        ret = harmless.HarmlessParser('./tests/data/clean.bmp')
        self.assertIsNotNone(ret)
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

    def test_avi(self):
        try:
            video._get_ffmpeg_path()
        except RuntimeError:
            raise unittest.SkipTest

        shutil.copy('./tests/data/dirty.torrent', './tests/data/clean.avi')
        p = video.AVIParser('./tests/data/clean.avi')
        self.assertFalse(p.remove_all())
        os.remove('./tests/data/clean.avi')

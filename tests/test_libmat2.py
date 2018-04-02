#!/usr/bin/python3

import unittest
import shutil
import os
import zipfile
import tempfile

from src import pdf, images, audio, office, parser_factory

class TestGetMeta(unittest.TestCase):
    def test_pdf(self):
        p = pdf.PDFParser('./tests/data/dirty.pdf')
        meta = p.get_meta()
        self.assertEqual(meta['producer'], 'pdfTeX-1.40.14')
        self.assertEqual(meta['creator'], "'Certified by IEEE PDFeXpress at 03/19/2016 2:56:07 AM'")

    def test_png(self):
        p = images.PNGParser('./tests/data/dirty.png')
        meta = p.get_meta()
        self.assertEqual(meta['Comment'], 'This is a comment, be careful!')
        self.assertEqual(meta['ModifyDate'], "2018:03:20 21:59:25")

    def test_jpg(self):
        p = images.JPGParser('./tests/data/dirty.jpg')
        meta = p.get_meta()
        self.assertEqual(meta['Comment'], 'Created with GIMP')

    def test_tiff(self):
        p = images.JPGParser('./tests/data/dirty.tiff')
        meta = p.get_meta()
        self.assertEqual(meta['Make'], 'OLYMPUS IMAGING CORP.')
        self.assertEqual(meta['Model'], 'C7070WZ')
        self.assertEqual(meta['ModifyDate'], '2005:12:26 17:09:35')

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
        p = office.MSOfficeParser('./tests/data/dirty.docx')
        meta = p.get_meta()
        self.assertEqual(meta['cp:lastModifiedBy'], 'Julien Voisin')
        self.assertEqual(meta['dc:creator'], 'julien voisin')
        self.assertEqual(meta['Application'], 'LibreOffice/5.4.5.1$Linux_X86_64 LibreOffice_project/40m0$Build-1')

    def test_libreoffice(self):
        p = office.LibreOfficeParser('./tests/data/dirty.odt')
        meta = p.get_meta()
        self.assertEqual(meta['meta:initial-creator'], 'jvoisin ')
        self.assertEqual(meta['meta:creation-date'], '2011-07-26T03:27:48')
        self.assertEqual(meta['meta:generator'], 'LibreOffice/3.3$Unix LibreOffice_project/330m19$Build-202')


class TestDeepCleaning(unittest.TestCase):
    def __check_deep_meta(self, p):
        tempdir = tempfile.mkdtemp()
        zipin = zipfile.ZipFile(p.filename)
        zipin.extractall(tempdir)

        for subdir, dirs, files in os.walk(tempdir):
            for f in files:
                complete_path = os.path.join(subdir, f)
                inside_p, _ = parser_factory.get_parser(complete_path)
                if inside_p is None:
                    continue
                print('[+] %s is clean inside %s' %(complete_path, p.filename))
                self.assertEqual(inside_p.get_meta(), {})
        shutil.rmtree(tempdir)


    def __check_zip_meta(self, p):
        zipin = zipfile.ZipFile(p.filename)
        for item in zipin.infolist():
            self.assertEqual(item.comment, b'')
            self.assertEqual(item.date_time, (1980, 1, 1, 0, 0, 0))
            self.assertEqual(item.create_system, 3)  # 3 is UNIX


    def test_office(self):
        shutil.copy('./tests/data/dirty.docx', './tests/data/clean.docx')
        p = office.MSOfficeParser('./tests/data/clean.docx')

        meta = p.get_meta()
        self.assertIsNotNone(meta)

        ret = p.remove_all()
        self.assertTrue(ret)

        p = office.MSOfficeParser('./tests/data/clean.docx.cleaned')
        self.assertEqual(p.get_meta(), {})

        self.__check_zip_meta(p)
        self.__check_deep_meta(p)

        os.remove('./tests/data/clean.docx')


    def test_libreoffice(self):
        shutil.copy('./tests/data/dirty.odt', './tests/data/clean.odt')
        p = office.LibreOfficeParser('./tests/data/clean.odt')

        meta = p.get_meta()
        self.assertIsNotNone(meta)

        ret = p.remove_all()
        self.assertTrue(ret)

        p = office.LibreOfficeParser('./tests/data/clean.odt.cleaned')
        self.assertEqual(p.get_meta(), {})

        self.__check_zip_meta(p)
        self.__check_deep_meta(p)

        os.remove('./tests/data/clean.odt')

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
        p = images.PNGParser('./tests/data/clean.png')

        meta = p.get_meta()
        self.assertEqual(meta['Comment'], 'This is a comment, be careful!')

        ret = p.remove_all()
        self.assertTrue(ret)

        p = images.PNGParser('./tests/data/clean.png.cleaned')
        self.assertEqual(p.get_meta(), {})

        os.remove('./tests/data/clean.png')

    def test_jpg(self):
        shutil.copy('./tests/data/dirty.jpg', './tests/data/clean.jpg')
        p = images.JPGParser('./tests/data/clean.jpg')

        meta = p.get_meta()
        self.assertEqual(meta['Comment'], 'Created with GIMP')

        ret = p.remove_all()
        self.assertTrue(ret)

        p = images.JPGParser('./tests/data/clean.jpg.cleaned')
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
        p = office.MSOfficeParser('./tests/data/clean.docx')

        meta = p.get_meta()
        self.assertIsNotNone(meta)

        ret = p.remove_all()
        self.assertTrue(ret)

        p = office.MSOfficeParser('./tests/data/clean.docx.cleaned')
        self.assertEqual(p.get_meta(), {})

        os.remove('./tests/data/clean.docx')


    def test_libreoffice(self):
        shutil.copy('./tests/data/dirty.odt', './tests/data/clean.odt')
        p = office.LibreOfficeParser('./tests/data/clean.odt')

        meta = p.get_meta()
        self.assertIsNotNone(meta)

        ret = p.remove_all()
        self.assertTrue(ret)

        p = office.LibreOfficeParser('./tests/data/clean.odt.cleaned')
        self.assertEqual(p.get_meta(), {})

        os.remove('./tests/data/clean.odt')

    def test_tiff(self):
        shutil.copy('./tests/data/dirty.tiff', './tests/data/clean.tiff')
        p = images.TiffParser('./tests/data/clean.tiff')

        meta = p.get_meta()
        self.assertEqual(meta['Model'], 'C7070WZ')

        ret = p.remove_all()
        self.assertTrue(ret)

        p = images.TiffParser('./tests/data/clean.tiff.cleaned')
        self.assertEqual(p.get_meta(), {})

        os.remove('./tests/data/clean.tiff')

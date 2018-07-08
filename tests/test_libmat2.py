#!/usr/bin/python3

import unittest
import shutil
import os
import zipfile
import tempfile

from libmat2 import pdf, images, audio, office, parser_factory, torrent, harmless


class TestParserFactory(unittest.TestCase):
    def test_subsubcalss(self):
        """ Test that our module auto-detection is handling sub-sub-classes """
        parser, mimetype = parser_factory.get_parser('./tests/data/dirty.mp3')
        self.assertEqual(mimetype, 'audio/mpeg')
        self.assertEqual(parser.__class__, audio.MP3Parser)


class TestParameterInjection(unittest.TestCase):
    def test_ver_injection(self):
        shutil.copy('./tests/data/dirty.png', './-ver')
        p = images.PNGParser('-ver')
        meta = p.get_meta()
        self.assertEqual(meta['Comment'], 'This is a comment, be careful!')
        self.assertEqual(meta['ModifyDate'], "2018:03:20 21:59:25")
        os.remove('-ver')


class TestUnsupportedEmbeddedFiles(unittest.TestCase):
    def test_odt_with_svg(self):
        shutil.copy('./tests/data/embedded.odt', './tests/data/clean.odt')
        p = office.LibreOfficeParser('./tests/data/clean.odt')
        self.assertFalse(p.remove_all())
        os.remove('./tests/data/clean.odt')

    def test_docx_with_svg(self):
        shutil.copy('./tests/data/embedded.docx', './tests/data/clean.docx')
        p = office.MSOfficeParser('./tests/data/clean.docx')
        self.assertFalse(p.remove_all())
        os.remove('./tests/data/clean.docx')


class TestGetMeta(unittest.TestCase):
    def test_pdf(self):
        p = pdf.PDFParser('./tests/data/dirty.pdf')
        meta = p.get_meta()
        self.assertEqual(meta['producer'], 'pdfTeX-1.40.14')
        self.assertEqual(meta['creator'], "'Certified by IEEE PDFeXpress at 03/19/2016 2:56:07 AM'")
        self.assertEqual(meta['DocumentID'], "uuid:4a1a79c8-404e-4d38-9580-5bc081036e61")
        self.assertEqual(meta['PTEX.Fullbanner'], "This is pdfTeX, Version " \
                "3.1415926-2.5-1.40.14 (TeX Live 2013/Debian) kpathsea " \
                "version 6.1.1")

    def test_torrent(self):
        p = torrent.TorrentParser('./tests/data/dirty.torrent')
        meta = p.get_meta()
        self.assertEqual(meta['created by'], b'mktorrent 1.0')

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
        p = images.TiffParser('./tests/data/dirty.tiff')
        meta = p.get_meta()
        self.assertEqual(meta['Make'], 'OLYMPUS IMAGING CORP.')
        self.assertEqual(meta['Model'], 'C7070WZ')
        self.assertEqual(meta['ModifyDate'], '2005:12:26 17:09:35')

    def test_mp3(self):
        p = audio.MP3Parser('./tests/data/dirty.mp3')
        meta = p.get_meta()
        self.assertEqual(meta['TXXX:I am a'], 'various comment')

    def test_ogg(self):
        p = audio.OGGParser('./tests/data/dirty.ogg')
        meta = p.get_meta()
        self.assertEqual(meta['title'], 'I am so')

    def test_flac(self):
        p = audio.FLACParser('./tests/data/dirty.flac')
        meta = p.get_meta()
        self.assertEqual(meta['title'], 'I am so')

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

        p = office.LibreOfficeParser('./tests/data/weird_producer.odt')
        meta = p.get_meta()
        self.assertEqual(meta['create_system'], 'Windows')
        self.assertEqual(meta['comment'], b'YAY FOR COMMENTS')

    def test_txt(self):
        p, mimetype = parser_factory.get_parser('./tests/data/dirty.txt')
        self.assertEqual(mimetype, 'text/plain')
        meta = p.get_meta()
        self.assertEqual(meta, {})


class TestRemovingThumbnails(unittest.TestCase):
    def test_odt(self):
        shutil.copy('./tests/data/revision.odt', './tests/data/clean.odt')

        zipin = zipfile.ZipFile(os.path.abspath('./tests/data/clean.odt'))
        self.assertIn('Thumbnails/thumbnail.png', zipin.namelist())
        zipin.close()

        p = office.LibreOfficeParser('./tests/data/clean.odt')
        self.assertTrue(p.remove_all())

        zipin = zipfile.ZipFile(os.path.abspath('./tests/data/clean.cleaned.odt'))
        self.assertNotIn('Thumbnails/thumbnail.png', zipin.namelist())
        zipin.close()

        os.remove('./tests/data/clean.cleaned.odt')
        os.remove('./tests/data/clean.odt')


class TestRevisionsCleaning(unittest.TestCase):
    def test_libreoffice(self):
        with zipfile.ZipFile('./tests/data/revision.odt') as zipin:
            c = zipin.open('content.xml')
            r = c.read()
            self.assertIn(b'tracked-changes', r)

        shutil.copy('./tests/data/revision.odt', './tests/data/clean.odt')
        p = office.LibreOfficeParser('./tests/data/clean.odt')
        self.assertTrue(p.remove_all())

        with zipfile.ZipFile('./tests/data/clean.cleaned.odt') as zipin:
            c = zipin.open('content.xml')
            r = c.read()
            self.assertNotIn(b'tracked-changes', r)

        os.remove('./tests/data/clean.odt')
        os.remove('./tests/data/clean.cleaned.odt')

    def test_msoffice(self):
        with zipfile.ZipFile('./tests/data/revision.docx') as zipin:
            c = zipin.open('word/document.xml')
            content = c.read()
            r = b'<w:ins w:id="1" w:author="Unknown Author" w:date="2018-06-28T23:48:00Z">'
            self.assertIn(r, content)

        shutil.copy('./tests/data/revision.docx', './tests/data/revision_clean.docx')
        p = office.MSOfficeParser('./tests/data/revision_clean.docx')
        self.assertTrue(p.remove_all())

        with zipfile.ZipFile('./tests/data/revision_clean.cleaned.docx') as zipin:
            c = zipin.open('word/document.xml')
            content = c.read()
            r = b'<w:ins w:id="1" w:author="Unknown Author" w:date="2018-06-28T23:48:00Z">'
            self.assertNotIn(r, content)

        os.remove('./tests/data/revision_clean.docx')
        os.remove('./tests/data/revision_clean.cleaned.docx')


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

        p = office.MSOfficeParser('./tests/data/clean.cleaned.docx')
        self.assertEqual(p.get_meta(), {})

        self.__check_zip_meta(p)
        self.__check_deep_meta(p)

        os.remove('./tests/data/clean.docx')
        os.remove('./tests/data/clean.cleaned.docx')


    def test_libreoffice(self):
        shutil.copy('./tests/data/dirty.odt', './tests/data/clean.odt')
        p = office.LibreOfficeParser('./tests/data/clean.odt')

        meta = p.get_meta()
        self.assertIsNotNone(meta)

        ret = p.remove_all()
        self.assertTrue(ret)

        p = office.LibreOfficeParser('./tests/data/clean.cleaned.odt')
        self.assertEqual(p.get_meta(), {})

        self.__check_zip_meta(p)
        self.__check_deep_meta(p)

        os.remove('./tests/data/clean.odt')
        os.remove('./tests/data/clean.cleaned.odt')

class TestLightWeightCleaning(unittest.TestCase):
    def test_pdf(self):
        shutil.copy('./tests/data/dirty.pdf', './tests/data/clean.pdf')
        p = pdf.PDFParser('./tests/data/clean.pdf')

        meta = p.get_meta()
        self.assertEqual(meta['producer'], 'pdfTeX-1.40.14')

        ret = p.remove_all_lightweight()
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

        ret = p.remove_all_lightweight()
        self.assertTrue(ret)

        p = images.PNGParser('./tests/data/clean.cleaned.png')
        self.assertEqual(p.get_meta(), {})

        os.remove('./tests/data/clean.png')
        os.remove('./tests/data/clean.cleaned.png')

class TestCleaning(unittest.TestCase):
    def test_pdf(self):
        shutil.copy('./tests/data/dirty.pdf', './tests/data/clean.pdf')
        p = pdf.PDFParser('./tests/data/clean.pdf')

        meta = p.get_meta()
        self.assertEqual(meta['producer'], 'pdfTeX-1.40.14')

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

        ret = p.remove_all()
        self.assertTrue(ret)

        p = images.PNGParser('./tests/data/clean.cleaned.png')
        self.assertEqual(p.get_meta(), {})

        os.remove('./tests/data/clean.png')
        os.remove('./tests/data/clean.cleaned.png')

    def test_jpg(self):
        shutil.copy('./tests/data/dirty.jpg', './tests/data/clean.jpg')
        p = images.JPGParser('./tests/data/clean.jpg')

        meta = p.get_meta()
        self.assertEqual(meta['Comment'], 'Created with GIMP')

        ret = p.remove_all()
        self.assertTrue(ret)

        p = images.JPGParser('./tests/data/clean.cleaned.jpg')
        self.assertEqual(p.get_meta(), {})

        os.remove('./tests/data/clean.jpg')
        os.remove('./tests/data/clean.cleaned.jpg')

    def test_mp3(self):
        shutil.copy('./tests/data/dirty.mp3', './tests/data/clean.mp3')
        p = audio.MP3Parser('./tests/data/clean.mp3')

        meta = p.get_meta()
        self.assertEqual(meta['TXXX:I am a'], 'various comment')

        ret = p.remove_all()
        self.assertTrue(ret)

        p = audio.MP3Parser('./tests/data/clean.cleaned.mp3')
        self.assertEqual(p.get_meta(), {})

        os.remove('./tests/data/clean.mp3')
        os.remove('./tests/data/clean.cleaned.mp3')

    def test_ogg(self):
        shutil.copy('./tests/data/dirty.ogg', './tests/data/clean.ogg')
        p = audio.OGGParser('./tests/data/clean.ogg')

        meta = p.get_meta()
        self.assertEqual(meta['title'], 'I am so')

        ret = p.remove_all()
        self.assertTrue(ret)

        p = audio.OGGParser('./tests/data/clean.cleaned.ogg')
        self.assertEqual(p.get_meta(), {})

        os.remove('./tests/data/clean.ogg')
        os.remove('./tests/data/clean.cleaned.ogg')

    def test_flac(self):
        shutil.copy('./tests/data/dirty.flac', './tests/data/clean.flac')
        p = audio.FLACParser('./tests/data/clean.flac')

        meta = p.get_meta()
        self.assertEqual(meta['title'], 'I am so')

        ret = p.remove_all()
        self.assertTrue(ret)

        p = audio.FLACParser('./tests/data/clean.cleaned.flac')
        self.assertEqual(p.get_meta(), {})

        os.remove('./tests/data/clean.flac')
        os.remove('./tests/data/clean.cleaned.flac')

    def test_office(self):
        shutil.copy('./tests/data/dirty.docx', './tests/data/clean.docx')
        p = office.MSOfficeParser('./tests/data/clean.docx')

        meta = p.get_meta()
        self.assertIsNotNone(meta)

        ret = p.remove_all()
        self.assertTrue(ret)

        p = office.MSOfficeParser('./tests/data/clean.cleaned.docx')
        self.assertEqual(p.get_meta(), {})

        os.remove('./tests/data/clean.docx')
        os.remove('./tests/data/clean.cleaned.docx')


    def test_libreoffice(self):
        shutil.copy('./tests/data/dirty.odt', './tests/data/clean.odt')
        p = office.LibreOfficeParser('./tests/data/clean.odt')

        meta = p.get_meta()
        self.assertIsNotNone(meta)

        ret = p.remove_all()
        self.assertTrue(ret)

        p = office.LibreOfficeParser('./tests/data/clean.cleaned.odt')
        self.assertEqual(p.get_meta(), {})

        os.remove('./tests/data/clean.odt')
        os.remove('./tests/data/clean.cleaned.odt')

    def test_tiff(self):
        shutil.copy('./tests/data/dirty.tiff', './tests/data/clean.tiff')
        p = images.TiffParser('./tests/data/clean.tiff')

        meta = p.get_meta()
        self.assertEqual(meta['Model'], 'C7070WZ')

        ret = p.remove_all()
        self.assertTrue(ret)

        p = images.TiffParser('./tests/data/clean.cleaned.tiff')
        self.assertEqual(p.get_meta(), {})

        os.remove('./tests/data/clean.tiff')
        os.remove('./tests/data/clean.cleaned.tiff')

    def test_bmp(self):
        shutil.copy('./tests/data/dirty.bmp', './tests/data/clean.bmp')
        p = harmless.HarmlessParser('./tests/data/clean.bmp')

        meta = p.get_meta()
        self.assertEqual(meta, {})  # bmp has no meta :)

        ret = p.remove_all()
        self.assertTrue(ret)

        p = harmless.HarmlessParser('./tests/data/clean.cleaned.bmp')
        self.assertEqual(p.get_meta(), {})

        os.remove('./tests/data/clean.bmp')
        os.remove('./tests/data/clean.cleaned.bmp')

    def test_torrent(self):
        shutil.copy('./tests/data/dirty.torrent', './tests/data/clean.torrent')
        p = torrent.TorrentParser('./tests/data/clean.torrent')

        meta = p.get_meta()
        self.assertEqual(meta, {'created by': b'mktorrent 1.0', 'creation date': 1522397702})

        ret = p.remove_all()
        self.assertTrue(ret)

        p = torrent.TorrentParser('./tests/data/clean.cleaned.torrent')
        self.assertEqual(p.get_meta(), {})

        os.remove('./tests/data/clean.torrent')
        os.remove('./tests/data/clean.cleaned.torrent')

    def test_odf(self):
        shutil.copy('./tests/data/dirty.odf', './tests/data/clean.odf')
        p = office.LibreOfficeParser('./tests/data/clean.odf')

        meta = p.get_meta()
        self.assertEqual(meta['meta:creation-date'], '2018-04-23T00:18:59.438231281')

        ret = p.remove_all()
        self.assertTrue(ret)

        p = office.LibreOfficeParser('./tests/data/clean.cleaned.odf')
        self.assertEqual(p.get_meta(), {})

        os.remove('./tests/data/clean.odf')
        os.remove('./tests/data/clean.cleaned.odf')


    def test_odg(self):
        shutil.copy('./tests/data/dirty.odg', './tests/data/clean.odg')
        p = office.LibreOfficeParser('./tests/data/clean.odg')

        meta = p.get_meta()
        self.assertEqual(meta['dc:date'], '2018-04-23T00:26:59.385838550')

        ret = p.remove_all()
        self.assertTrue(ret)

        p = office.LibreOfficeParser('./tests/data/clean.cleaned.odg')
        self.assertEqual(p.get_meta(), {})

        os.remove('./tests/data/clean.odg')
        os.remove('./tests/data/clean.cleaned.odg')

    def test_txt(self):
        shutil.copy('./tests/data/dirty.txt', './tests/data/clean.txt')
        p = harmless.HarmlessParser('./tests/data/clean.txt')

        meta = p.get_meta()
        self.assertEqual(meta, {})

        ret = p.remove_all()
        self.assertTrue(ret)

        p = harmless.HarmlessParser('./tests/data/clean.cleaned.txt')
        self.assertEqual(p.get_meta(), {})

        os.remove('./tests/data/clean.txt')
        os.remove('./tests/data/clean.cleaned.txt')

#!/usr/bin/env python3

import unittest
import shutil
import os
import re
import tarfile
import tempfile
import zipfile

from libmat2 import pdf, images, audio, office, parser_factory, torrent, harmless
from libmat2 import check_dependencies, video, archive, web, epub


class TestCheckDependencies(unittest.TestCase):
    def test_deps(self):
        ret = check_dependencies()
        for key, value in ret.items():
            if value['required']:
                self.assertTrue(value['found'], "The value for %s is False" % key)


class TestParserFactory(unittest.TestCase):
    def test_subsubcalss(self):
        """ Test that our module auto-detection is handling sub-sub-classes """
        parser, mimetype = parser_factory.get_parser('./tests/data/dirty.mp3')
        self.assertEqual(mimetype, 'audio/mpeg')
        self.assertEqual(parser.__class__, audio.MP3Parser)

    def test_tarfile_double_extension_handling(self):
        """ Test that our module auto-detection is handling sub-sub-classes """
        with tarfile.TarFile.open('./tests/data/dirty.tar.bz2', 'w:bz2') as zout:
            zout.add('./tests/data/dirty.jpg')
        parser, mimetype = parser_factory.get_parser('./tests/data/dirty.tar.bz2')
        self.assertEqual(mimetype, 'application/x-tar+bz2')
        os.remove('./tests/data/dirty.tar.bz2')


class TestParameterInjection(unittest.TestCase):
    def test_ver_injection(self):
        shutil.copy('./tests/data/dirty.png', './-ver')
        p = images.PNGParser('-ver')
        meta = p.get_meta()
        self.assertEqual(meta['Comment'], 'This is a comment, be careful!')
        self.assertEqual(meta['ModifyDate'], "2018:03:20 21:59:25")
        os.remove('-ver')

    def test_ffmpeg_injection(self):
        try:
            video._get_ffmpeg_path()
        except RuntimeError:
            raise unittest.SkipTest

        shutil.copy('./tests/data/dirty.avi', './--output')
        p = video.AVIParser('--output')
        meta = p.get_meta()
        self.assertEqual(meta['Software'], 'MEncoder SVN-r33148-4.0.1')
        os.remove('--output')

    def test_ffmpeg_injection_complete_path(self):
        try:
            video._get_ffmpeg_path()
        except RuntimeError:
            raise unittest.SkipTest

        shutil.copy('./tests/data/dirty.avi', './tests/data/ --output.avi')
        p = video.AVIParser('./tests/data/ --output.avi')
        meta = p.get_meta()
        self.assertEqual(meta['Software'], 'MEncoder SVN-r33148-4.0.1')
        self.assertTrue(p.remove_all())
        os.remove('./tests/data/ --output.avi')
        os.remove('./tests/data/ --output.cleaned.avi')


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
        self.assertEqual(meta['PTEX.Fullbanner'], "This is pdfTeX, Version "
                "3.1415926-2.5-1.40.14 (TeX Live 2013/Debian) kpathsea "
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
        self.assertEqual(meta['Cover 0'], {'Comment': 'Created with GIMP'})

    def test_docx(self):
        p = office.MSOfficeParser('./tests/data/dirty.docx')
        meta = p.get_meta()
        self.assertEqual(meta['docProps/core.xml']['cp:lastModifiedBy'], 'Julien Voisin')
        self.assertEqual(meta['docProps/core.xml']['dc:creator'], 'julien voisin')
        self.assertEqual(meta['docProps/app.xml']['Application'], 'LibreOffice/5.4.5.1$Linux_X86_64 LibreOffice_project/40m0$Build-1')

    def test_libreoffice(self):
        p = office.LibreOfficeParser('./tests/data/dirty.odt')
        meta = p.get_meta()
        self.assertEqual(meta['meta.xml']['meta:initial-creator'], 'jvoisin ')
        self.assertEqual(meta['meta.xml']['meta:creation-date'], '2011-07-26T03:27:48')
        self.assertEqual(meta['meta.xml']['meta:generator'], 'LibreOffice/3.3$Unix LibreOffice_project/330m19$Build-202')

        p = office.LibreOfficeParser('./tests/data/weird_producer.odt')
        meta = p.get_meta()
        self.assertEqual(meta['mimetype']['create_system'], 'Windows')
        self.assertEqual(meta['mimetype']['comment'], b'YAY FOR COMMENTS')

    def test_txt(self):
        p, mimetype = parser_factory.get_parser('./tests/data/dirty.txt')
        self.assertEqual(mimetype, 'text/plain')
        meta = p.get_meta()
        self.assertEqual(meta, {})

    def test_zip(self):
        with zipfile.ZipFile('./tests/data/dirty.zip', 'w') as zout:
            zout.write('./tests/data/dirty.flac')
            zout.write('./tests/data/dirty.docx')
            zout.write('./tests/data/dirty.jpg')
        p, mimetype = parser_factory.get_parser('./tests/data/dirty.zip')
        self.assertEqual(mimetype, 'application/zip')
        meta = p.get_meta()
        self.assertEqual(meta['tests/data/dirty.flac']['comments'], 'Thank you for using MAT !')
        self.assertEqual(meta['tests/data/dirty.docx']['word/media/image1.png']['Comment'], 'This is a comment, be careful!')
        os.remove('./tests/data/dirty.zip')

    def test_wmv(self):
        p, mimetype = parser_factory.get_parser('./tests/data/dirty.wmv')
        self.assertEqual(mimetype, 'video/x-ms-wmv')
        meta = p.get_meta()
        self.assertEqual(meta['EncodingSettings'], 'Lavf52.103.0')

    def test_gif(self):
        p, mimetype = parser_factory.get_parser('./tests/data/dirty.gif')
        self.assertEqual(mimetype, 'image/gif')
        meta = p.get_meta()
        self.assertEqual(meta['Comment'], 'this is a test comment')

    def test_epub(self):
        p, mimetype = parser_factory.get_parser('./tests/data/dirty.epub')
        self.assertEqual(mimetype, 'application/epub+zip')
        meta = p.get_meta()
        self.assertEqual(meta['OEBPS/content.opf']['dc:creator'], 'Dorothy L. Sayers')
        self.assertEqual(meta['OEBPS/toc.ncx']['dtb:generator'], 'Ebookmaker 0.4.0a5 by Marcello Perathoner <webmaster@gutenberg.org>')
        self.assertEqual(meta['OEBPS/@public@vhost@g@gutenberg@html@files@58820@58820-h@images@shield25.jpg']['CreatorTool'], 'Adobe Photoshop CS5 Macintosh')
        self.assertEqual(meta['OEBPS/@public@vhost@g@gutenberg@html@files@58820@58820-h@58820-h-2.htm.html']['generator'], 'Ebookmaker 0.4.0a5 by Marcello Perathoner <webmaster@gutenberg.org>')

    def test_css(self):
        p, mimetype = parser_factory.get_parser('./tests/data/dirty.css')
        self.assertEqual(mimetype, 'text/css')
        meta = p.get_meta()
        self.assertEqual(meta['author'], 'jvoisin')
        self.assertEqual(meta['version'], '1.0')
        self.assertEqual(meta['harmful data'], 'underline is cool')

    def test_tar(self):
        with tarfile.TarFile('./tests/data/dirty.tar', 'w') as tout:
            tout.add('./tests/data/dirty.flac')
            tout.add('./tests/data/dirty.docx')
            tout.add('./tests/data/dirty.jpg')
        p, mimetype = parser_factory.get_parser('./tests/data/dirty.tar')
        self.assertEqual(mimetype, 'application/x-tar')
        meta = p.get_meta()
        self.assertEqual(meta['./tests/data/dirty.flac']['comments'], 'Thank you for using MAT !')
        self.assertEqual(meta['./tests/data/dirty.docx']['word/media/image1.png']['Comment'], 'This is a comment, be careful!')
        os.remove('./tests/data/dirty.tar')


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
        self.assertTrue(p.remove_all())

        os.remove('./tests/data/clean.pdf')
        os.remove('./tests/data/clean.cleaned.pdf')
        os.remove('./tests/data/clean.cleaned.cleaned.pdf')

    def test_png(self):
        shutil.copy('./tests/data/dirty.png', './tests/data/clean.png')
        p = images.PNGParser('./tests/data/clean.png')

        meta = p.get_meta()
        self.assertEqual(meta['Comment'], 'This is a comment, be careful!')

        ret = p.remove_all()
        self.assertTrue(ret)

        p = images.PNGParser('./tests/data/clean.cleaned.png')
        self.assertEqual(p.get_meta(), {})
        self.assertTrue(p.remove_all())

        os.remove('./tests/data/clean.png')
        os.remove('./tests/data/clean.cleaned.png')
        os.remove('./tests/data/clean.cleaned.cleaned.png')

    def test_jpg(self):
        shutil.copy('./tests/data/dirty.jpg', './tests/data/clean.jpg')
        p = images.JPGParser('./tests/data/clean.jpg')

        meta = p.get_meta()
        self.assertEqual(meta['Comment'], 'Created with GIMP')

        ret = p.remove_all()
        self.assertTrue(ret)

        p = images.JPGParser('./tests/data/clean.cleaned.jpg')
        self.assertEqual(p.get_meta(), {})
        self.assertTrue(p.remove_all())

        os.remove('./tests/data/clean.jpg')
        os.remove('./tests/data/clean.cleaned.jpg')
        os.remove('./tests/data/clean.cleaned.cleaned.jpg')

    def test_mp3(self):
        shutil.copy('./tests/data/dirty.mp3', './tests/data/clean.mp3')
        p = audio.MP3Parser('./tests/data/clean.mp3')

        meta = p.get_meta()
        self.assertEqual(meta['TXXX:I am a'], 'various comment')

        ret = p.remove_all()
        self.assertTrue(ret)

        p = audio.MP3Parser('./tests/data/clean.cleaned.mp3')
        self.assertEqual(p.get_meta(), {})
        self.assertTrue(p.remove_all())

        os.remove('./tests/data/clean.mp3')
        os.remove('./tests/data/clean.cleaned.mp3')
        os.remove('./tests/data/clean.cleaned.cleaned.mp3')

    def test_ogg(self):
        shutil.copy('./tests/data/dirty.ogg', './tests/data/clean.ogg')
        p = audio.OGGParser('./tests/data/clean.ogg')

        meta = p.get_meta()
        self.assertEqual(meta['title'], 'I am so')

        ret = p.remove_all()
        self.assertTrue(ret)

        p = audio.OGGParser('./tests/data/clean.cleaned.ogg')
        self.assertEqual(p.get_meta(), {})
        self.assertTrue(p.remove_all())

        os.remove('./tests/data/clean.ogg')
        os.remove('./tests/data/clean.cleaned.ogg')
        os.remove('./tests/data/clean.cleaned.cleaned.ogg')

    def test_flac(self):
        shutil.copy('./tests/data/dirty.flac', './tests/data/clean.flac')
        p = audio.FLACParser('./tests/data/clean.flac')

        meta = p.get_meta()
        self.assertEqual(meta['title'], 'I am so')

        ret = p.remove_all()
        self.assertTrue(ret)

        p = audio.FLACParser('./tests/data/clean.cleaned.flac')
        self.assertEqual(p.get_meta(), {})
        self.assertTrue(p.remove_all())

        os.remove('./tests/data/clean.flac')
        os.remove('./tests/data/clean.cleaned.flac')
        os.remove('./tests/data/clean.cleaned.cleaned.flac')

    def test_office(self):
        shutil.copy('./tests/data/dirty.docx', './tests/data/clean.docx')
        p = office.MSOfficeParser('./tests/data/clean.docx')

        meta = p.get_meta()
        self.assertIsNotNone(meta)

        ret = p.remove_all()
        self.assertTrue(ret)

        p = office.MSOfficeParser('./tests/data/clean.cleaned.docx')
        self.assertEqual(p.get_meta(), {})
        self.assertTrue(p.remove_all())

        os.remove('./tests/data/clean.docx')
        os.remove('./tests/data/clean.cleaned.docx')
        os.remove('./tests/data/clean.cleaned.cleaned.docx')

    def test_libreoffice(self):
        shutil.copy('./tests/data/dirty.odt', './tests/data/clean.odt')
        p = office.LibreOfficeParser('./tests/data/clean.odt')

        meta = p.get_meta()
        self.assertIsNotNone(meta)

        ret = p.remove_all()
        self.assertTrue(ret)

        p = office.LibreOfficeParser('./tests/data/clean.cleaned.odt')
        self.assertEqual(p.get_meta(), {})
        self.assertTrue(p.remove_all())

        os.remove('./tests/data/clean.odt')
        os.remove('./tests/data/clean.cleaned.odt')
        os.remove('./tests/data/clean.cleaned.cleaned.odt')

    def test_tiff(self):
        shutil.copy('./tests/data/dirty.tiff', './tests/data/clean.tiff')
        p = images.TiffParser('./tests/data/clean.tiff')

        meta = p.get_meta()
        self.assertEqual(meta['Model'], 'C7070WZ')

        ret = p.remove_all()
        self.assertTrue(ret)

        p = images.TiffParser('./tests/data/clean.cleaned.tiff')
        self.assertEqual(p.get_meta(), {})
        self.assertTrue(p.remove_all())

        os.remove('./tests/data/clean.tiff')
        os.remove('./tests/data/clean.cleaned.tiff')
        os.remove('./tests/data/clean.cleaned.cleaned.tiff')

    def test_bmp(self):
        shutil.copy('./tests/data/dirty.bmp', './tests/data/clean.bmp')
        p = harmless.HarmlessParser('./tests/data/clean.bmp')

        meta = p.get_meta()
        self.assertEqual(meta, {})  # bmp has no meta :)

        ret = p.remove_all()
        self.assertTrue(ret)

        p = harmless.HarmlessParser('./tests/data/clean.cleaned.bmp')
        self.assertEqual(p.get_meta(), {})
        self.assertTrue(p.remove_all())

        os.remove('./tests/data/clean.bmp')
        os.remove('./tests/data/clean.cleaned.bmp')
        os.remove('./tests/data/clean.cleaned.cleaned.bmp')

    def test_torrent(self):
        shutil.copy('./tests/data/dirty.torrent', './tests/data/clean.torrent')
        p = torrent.TorrentParser('./tests/data/clean.torrent')

        meta = p.get_meta()
        self.assertEqual(meta, {'created by': b'mktorrent 1.0', 'creation date': 1522397702})

        ret = p.remove_all()
        self.assertTrue(ret)

        p = torrent.TorrentParser('./tests/data/clean.cleaned.torrent')
        self.assertEqual(p.get_meta(), {})
        self.assertTrue(p.remove_all())

        os.remove('./tests/data/clean.torrent')
        os.remove('./tests/data/clean.cleaned.torrent')
        os.remove('./tests/data/clean.cleaned.cleaned.torrent')

    def test_odf(self):
        shutil.copy('./tests/data/dirty.odf', './tests/data/clean.odf')
        p = office.LibreOfficeParser('./tests/data/clean.odf')

        meta = p.get_meta()
        self.assertEqual(meta['meta.xml']['meta:creation-date'], '2018-04-23T00:18:59.438231281')

        ret = p.remove_all()
        self.assertTrue(ret)

        p = office.LibreOfficeParser('./tests/data/clean.cleaned.odf')
        self.assertEqual(p.get_meta(), {})
        self.assertTrue(p.remove_all())

        os.remove('./tests/data/clean.odf')
        os.remove('./tests/data/clean.cleaned.odf')
        os.remove('./tests/data/clean.cleaned.cleaned.odf')

    def test_odg(self):
        shutil.copy('./tests/data/dirty.odg', './tests/data/clean.odg')
        p = office.LibreOfficeParser('./tests/data/clean.odg')

        meta = p.get_meta()
        self.assertEqual(meta['meta.xml']['dc:date'], '2018-04-23T00:26:59.385838550')

        ret = p.remove_all()
        self.assertTrue(ret)

        p = office.LibreOfficeParser('./tests/data/clean.cleaned.odg')
        self.assertEqual(p.get_meta(), {})
        self.assertTrue(p.remove_all())

        os.remove('./tests/data/clean.odg')
        os.remove('./tests/data/clean.cleaned.odg')
        os.remove('./tests/data/clean.cleaned.cleaned.odg')

    def test_txt(self):
        shutil.copy('./tests/data/dirty.txt', './tests/data/clean.txt')
        p = harmless.HarmlessParser('./tests/data/clean.txt')

        meta = p.get_meta()
        self.assertEqual(meta, {})

        ret = p.remove_all()
        self.assertTrue(ret)

        p = harmless.HarmlessParser('./tests/data/clean.cleaned.txt')
        self.assertEqual(p.get_meta(), {})
        self.assertTrue(p.remove_all())

        os.remove('./tests/data/clean.txt')
        os.remove('./tests/data/clean.cleaned.txt')
        os.remove('./tests/data/clean.cleaned.cleaned.txt')

    def test_avi(self):
        try:
            video._get_ffmpeg_path()
        except RuntimeError:
            raise unittest.SkipTest

        shutil.copy('./tests/data/dirty.avi', './tests/data/clean.avi')
        p = video.AVIParser('./tests/data/clean.avi')

        meta = p.get_meta()
        self.assertEqual(meta['Software'], 'MEncoder SVN-r33148-4.0.1')

        ret = p.remove_all()
        self.assertTrue(ret)

        p = video.AVIParser('./tests/data/clean.cleaned.avi')
        self.assertEqual(p.get_meta(), {})
        self.assertTrue(p.remove_all())

        os.remove('./tests/data/clean.avi')
        os.remove('./tests/data/clean.cleaned.avi')
        os.remove('./tests/data/clean.cleaned.cleaned.avi')

    def test_zip(self):
        with zipfile.ZipFile('./tests/data/dirty.zip', 'w') as zout:
            zout.write('./tests/data/dirty.flac')
            zout.write('./tests/data/dirty.docx')
            zout.write('./tests/data/dirty.jpg')
        p = archive.ZipParser('./tests/data/dirty.zip')
        meta = p.get_meta()
        self.assertEqual(meta['tests/data/dirty.docx']['word/media/image1.png']['Comment'], 'This is a comment, be careful!')

        ret = p.remove_all()
        self.assertTrue(ret)

        p = archive.ZipParser('./tests/data/dirty.cleaned.zip')
        self.assertEqual(p.get_meta(), {})
        self.assertTrue(p.remove_all())

        os.remove('./tests/data/dirty.zip')
        os.remove('./tests/data/dirty.cleaned.zip')
        os.remove('./tests/data/dirty.cleaned.cleaned.zip')


    def test_mp4(self):
        try:
            video._get_ffmpeg_path()
        except RuntimeError:
            raise unittest.SkipTest

        shutil.copy('./tests/data/dirty.mp4', './tests/data/clean.mp4')
        p = video.MP4Parser('./tests/data/clean.mp4')

        meta = p.get_meta()
        self.assertEqual(meta['Encoder'], 'HandBrake 0.9.4 2009112300')

        ret = p.remove_all()
        self.assertTrue(ret)

        p = video.MP4Parser('./tests/data/clean.cleaned.mp4')
        self.assertNotIn('Encoder', p.get_meta())
        self.assertTrue(p.remove_all())

        os.remove('./tests/data/clean.mp4')
        os.remove('./tests/data/clean.cleaned.mp4')
        os.remove('./tests/data/clean.cleaned.cleaned.mp4')

    def test_wmv(self):
        try:
            video._get_ffmpeg_path()
        except RuntimeError:
            raise unittest.SkipTest

        shutil.copy('./tests/data/dirty.wmv', './tests/data/clean.wmv')
        p = video.WMVParser('./tests/data/clean.wmv')

        meta = p.get_meta()
        self.assertEqual(meta['EncodingSettings'], 'Lavf52.103.0')

        ret = p.remove_all()
        self.assertTrue(ret)

        p = video.WMVParser('./tests/data/clean.cleaned.wmv')
        self.assertNotIn('EncodingSettings', p.get_meta())
        self.assertTrue(p.remove_all())

        os.remove('./tests/data/clean.wmv')
        os.remove('./tests/data/clean.cleaned.wmv')
        os.remove('./tests/data/clean.cleaned.cleaned.wmv')

    def test_gif(self):
        shutil.copy('./tests/data/dirty.gif', './tests/data/clean.gif')
        p = images.GIFParser('./tests/data/clean.gif')

        meta = p.get_meta()
        self.assertEqual(meta['Comment'], 'this is a test comment')

        ret = p.remove_all()
        self.assertTrue(ret)

        p = images.GIFParser('./tests/data/clean.cleaned.gif')
        self.assertNotIn('EncodingSettings', p.get_meta())
        self.assertTrue(p.remove_all())

        os.remove('./tests/data/clean.gif')
        os.remove('./tests/data/clean.cleaned.gif')
        os.remove('./tests/data/clean.cleaned.cleaned.gif')

    def test_html(self):
        shutil.copy('./tests/data/dirty.html', './tests/data/clean.html')
        p = web.HTMLParser('./tests/data/clean.html')

        meta = p.get_meta()
        self.assertEqual(meta['author'], 'jvoisin')

        ret = p.remove_all()
        self.assertTrue(ret)

        p = web.HTMLParser('./tests/data/clean.cleaned.html')
        self.assertEqual(p.get_meta(), {})
        self.assertTrue(p.remove_all())

        os.remove('./tests/data/clean.html')
        os.remove('./tests/data/clean.cleaned.html')
        os.remove('./tests/data/clean.cleaned.cleaned.html')

        with open('./tests/data/clean.html', 'w') as f:
            f.write('<title><title><pouet/><meta/></title></title><test/>')
        p = web.HTMLParser('./tests/data/clean.html')
        self.assertTrue(p.remove_all())
        with open('./tests/data/clean.cleaned.html', 'r') as f:
            self.assertEqual(f.read(), '<title></title><test/>')
        os.remove('./tests/data/clean.html')
        os.remove('./tests/data/clean.cleaned.html')

        with open('./tests/data/clean.html', 'w') as f:
            f.write('<test><title>Some<b>metadata</b><br/></title></test>')
        p = web.HTMLParser('./tests/data/clean.html')
        self.assertTrue(p.remove_all())
        with open('./tests/data/clean.cleaned.html', 'r') as f:
            self.assertEqual(f.read(), '<test><title></title></test>')
        os.remove('./tests/data/clean.html')
        os.remove('./tests/data/clean.cleaned.html')

        with open('./tests/data/clean.html', 'w') as f:
            f.write('<meta><meta/><!----><!-- test--></meta>')
        p = web.HTMLParser('./tests/data/clean.html')
        self.assertTrue(p.remove_all())
        with open('./tests/data/clean.cleaned.html', 'r') as f:
            self.assertEqual(f.read(), '')
        os.remove('./tests/data/clean.html')
        os.remove('./tests/data/clean.cleaned.html')


    def test_epub(self):
        shutil.copy('./tests/data/dirty.epub', './tests/data/clean.epub')
        p = epub.EPUBParser('./tests/data/clean.epub')

        meta = p.get_meta()
        self.assertEqual(meta['OEBPS/content.opf']['dc:source'], 'http://www.gutenberg.org/files/58820/58820-h/58820-h.htm')

        ret = p.remove_all()
        self.assertTrue(ret)

        p = epub.EPUBParser('./tests/data/clean.cleaned.epub')
        meta = p.get_meta()
        res = re.match(meta['OEBPS/content.opf']['metadata'], '^<dc:identifier>[0-9a-f-]+</dc:identifier><dc:title /><dc:language />$')
        self.assertNotEqual(res, False)

        self.assertTrue(p.remove_all())

        os.remove('./tests/data/clean.epub')
        os.remove('./tests/data/clean.cleaned.epub')
        os.remove('./tests/data/clean.cleaned.cleaned.epub')


    def test_css(self):
        shutil.copy('./tests/data/dirty.css', './tests/data/clean.css')
        p = web.CSSParser('./tests/data/clean.css')

        self.assertEqual(p.get_meta(), {
            'harmful data': 'underline is cool',
            'version': '1.0',
            'author': 'jvoisin'})

        ret = p.remove_all()
        self.assertTrue(ret)

        p = web.CSSParser('./tests/data/clean.cleaned.css')
        self.assertEqual(p.get_meta(), {})
        self.assertTrue(p.remove_all())

        os.remove('./tests/data/clean.css')
        os.remove('./tests/data/clean.cleaned.css')
        os.remove('./tests/data/clean.cleaned.cleaned.css')

    def test_tar(self):
        with tarfile.TarFile.open('./tests/data/dirty.tar', 'w') as zout:
            zout.add('./tests/data/dirty.flac')
            zout.add('./tests/data/dirty.docx')
            zout.add('./tests/data/dirty.jpg')
        p = archive.TarParser('./tests/data/dirty.tar')
        meta = p.get_meta()
        self.assertEqual(meta['./tests/data/dirty.docx']['word/media/image1.png']['Comment'], 'This is a comment, be careful!')

        ret = p.remove_all()
        self.assertTrue(ret)

        p = archive.TarParser('./tests/data/dirty.cleaned.tar')
        self.assertEqual(p.get_meta(), {})
        self.assertTrue(p.remove_all())

        tmp_dir = tempfile.mkdtemp()
        with tarfile.open('./tests/data/dirty.cleaned.tar') as zout:
            zout.extractall(path=tmp_dir)
            zout.close()

        number_of_files = 0
        for root, _, fnames in os.walk(tmp_dir):
            for f in fnames:
                complete_path = os.path.join(root, f)
                p, _ = parser_factory.get_parser(complete_path)
                self.assertIsNotNone(p)
                self.assertEqual(p.get_meta(), {})
                number_of_files += 1
        self.assertEqual(number_of_files, 3)

        os.remove('./tests/data/dirty.tar')
        os.remove('./tests/data/dirty.cleaned.tar')
        os.remove('./tests/data/dirty.cleaned.cleaned.tar')

    def test_targz(self):
        with tarfile.TarFile.open('./tests/data/dirty.tar.gz', 'w:gz') as zout:
            zout.add('./tests/data/dirty.flac')
            zout.add('./tests/data/dirty.docx')
            zout.add('./tests/data/dirty.jpg')
        p = archive.TarParser('./tests/data/dirty.tar.gz')
        meta = p.get_meta()
        self.assertEqual(meta['./tests/data/dirty.docx']['word/media/image1.png']['Comment'], 'This is a comment, be careful!')

        ret = p.remove_all()
        self.assertTrue(ret)

        p = archive.TarParser('./tests/data/dirty.cleaned.tar.gz')
        self.assertEqual(p.get_meta(), {})
        self.assertTrue(p.remove_all())

        tmp_dir = tempfile.mkdtemp()
        with tarfile.open('./tests/data/dirty.cleaned.tar.gz') as zout:
            zout.extractall(path=tmp_dir)
            zout.close()

        number_of_files = 0
        for root, _, fnames in os.walk(tmp_dir):
            for f in fnames:
                complete_path = os.path.join(root, f)
                p, _ = parser_factory.get_parser(complete_path)
                self.assertIsNotNone(p)
                self.assertEqual(p.get_meta(), {})
                number_of_files += 1
        self.assertEqual(number_of_files, 3)

        os.remove('./tests/data/dirty.tar.gz')
        os.remove('./tests/data/dirty.cleaned.tar.gz')
        os.remove('./tests/data/dirty.cleaned.cleaned.tar.gz')

    def test_tarbz2(self):
        with tarfile.TarFile.open('./tests/data/dirty.tar.bz2', 'w:bz2') as zout:
            zout.add('./tests/data/dirty.flac')
            zout.add('./tests/data/dirty.docx')
            zout.add('./tests/data/dirty.jpg')
        p = archive.TarParser('./tests/data/dirty.tar.bz2')
        meta = p.get_meta()
        self.assertEqual(meta['./tests/data/dirty.docx']['word/media/image1.png']['Comment'], 'This is a comment, be careful!')

        ret = p.remove_all()
        self.assertTrue(ret)

        p = archive.TarParser('./tests/data/dirty.cleaned.tar.bz2')
        self.assertEqual(p.get_meta(), {})
        self.assertTrue(p.remove_all())

        tmp_dir = tempfile.mkdtemp()
        with tarfile.open('./tests/data/dirty.cleaned.tar.bz2') as zout:
            zout.extractall(path=tmp_dir)
            zout.close()

        number_of_files = 0
        for root, _, fnames in os.walk(tmp_dir):
            for f in fnames:
                complete_path = os.path.join(root, f)
                p, _ = parser_factory.get_parser(complete_path)
                self.assertIsNotNone(p)
                self.assertEqual(p.get_meta(), {})
                number_of_files += 1
        self.assertEqual(number_of_files, 3)

        os.remove('./tests/data/dirty.tar.bz2')
        os.remove('./tests/data/dirty.cleaned.tar.bz2')
        os.remove('./tests/data/dirty.cleaned.cleaned.tar.bz2')

    def test_tarxz(self):
        with tarfile.TarFile.open('./tests/data/dirty.tar.xz', 'w:xz') as zout:
            zout.add('./tests/data/dirty.flac')
            zout.add('./tests/data/dirty.docx')
            zout.add('./tests/data/dirty.jpg')
        p = archive.TarParser('./tests/data/dirty.tar.xz')
        meta = p.get_meta()
        self.assertEqual(meta['./tests/data/dirty.docx']['word/media/image1.png']['Comment'], 'This is a comment, be careful!')

        ret = p.remove_all()
        self.assertTrue(ret)

        p = archive.TarParser('./tests/data/dirty.cleaned.tar.xz')
        self.assertEqual(p.get_meta(), {})
        self.assertTrue(p.remove_all())

        tmp_dir = tempfile.mkdtemp()
        with tarfile.open('./tests/data/dirty.cleaned.tar.xz') as zout:
            zout.extractall(path=tmp_dir)
            zout.close()

        number_of_files = 0
        for root, _, fnames in os.walk(tmp_dir):
            for f in fnames:
                complete_path = os.path.join(root, f)
                p, _ = parser_factory.get_parser(complete_path)
                self.assertIsNotNone(p)
                self.assertEqual(p.get_meta(), {})
                number_of_files += 1
        self.assertEqual(number_of_files, 3)

        os.remove('./tests/data/dirty.tar.xz')
        os.remove('./tests/data/dirty.cleaned.tar.xz')
        os.remove('./tests/data/dirty.cleaned.cleaned.tar.xz')

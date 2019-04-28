#!/usr/bin/env python3

import unittest
import stat
import time
import shutil
import os
import logging
import zipfile
import tarfile

from libmat2 import pdf, images, audio, office, parser_factory, torrent
from libmat2 import harmless, video, web, archive

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
        shutil.copy('./tests/data/embedded_corrupted.odt', './tests/data/clean.odt')
        parser, _ = parser_factory.get_parser('./tests/data/clean.odt')
        self.assertFalse(parser.remove_all())
        self.assertTrue(parser.get_meta())
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

    def test_png_lightweight(self):
        return
        shutil.copy('./tests/data/dirty.torrent', './tests/data/clean.png')
        p = images.PNGParser('./tests/data/clean.png')
        self.assertTrue(p.remove_all())
        os.remove('./tests/data/clean.png')

    def test_avi(self):
        try:
            video._get_ffmpeg_path()
        except RuntimeError:
            raise unittest.SkipTest

        shutil.copy('./tests/data/dirty.torrent', './tests/data/clean.avi')
        p = video.AVIParser('./tests/data/clean.avi')
        self.assertFalse(p.remove_all())
        os.remove('./tests/data/clean.avi')

    def test_avi_injection(self):
        try:
            video._get_ffmpeg_path()
        except RuntimeError:
            raise unittest.SkipTest

        shutil.copy('./tests/data/dirty.torrent', './tests/data/--output.avi')
        p = video.AVIParser('./tests/data/--output.avi')
        self.assertFalse(p.remove_all())
        os.remove('./tests/data/--output.avi')

    def test_zip(self):
        with zipfile.ZipFile('./tests/data/clean.zip', 'w') as zout:
            zout.write('./tests/data/dirty.flac')
            zout.write('./tests/data/dirty.docx')
            zout.write('./tests/data/dirty.jpg')
            zout.write('./tests/data/embedded_corrupted.docx')
        p, mimetype = parser_factory.get_parser('./tests/data/clean.zip')
        self.assertEqual(mimetype, 'application/zip')
        meta = p.get_meta()
        self.assertEqual(meta['tests/data/dirty.flac']['comments'], 'Thank you for using MAT !')
        self.assertEqual(meta['tests/data/dirty.docx']['word/media/image1.png']['Comment'], 'This is a comment, be careful!')
        self.assertFalse(p.remove_all())
        os.remove('./tests/data/clean.zip')

    def test_html(self):
        shutil.copy('./tests/data/dirty.html', './tests/data/clean.html')
        with open('./tests/data/clean.html', 'a') as f:
            f.write('<open>but not</closed>')
        with self.assertRaises(ValueError):
            web.HTMLParser('./tests/data/clean.html')
        os.remove('./tests/data/clean.html')

        # Yes, we're able to deal with malformed html :/
        shutil.copy('./tests/data/dirty.html', './tests/data/clean.html')
        with open('./tests/data/clean.html', 'a') as f:
            f.write('<meta name=\'this" is="weird"/>')
        p = web.HTMLParser('./tests/data/clean.html')
        self.assertTrue(p.remove_all())
        p = web.HTMLParser('./tests/data/clean.cleaned.html')
        self.assertEqual(p.get_meta(), {})
        os.remove('./tests/data/clean.html')
        os.remove('./tests/data/clean.cleaned.html')

        with open('./tests/data/clean.html', 'w') as f:
            f.write('</meta>')
        with self.assertRaises(ValueError):
            web.HTMLParser('./tests/data/clean.html')
        os.remove('./tests/data/clean.html')

        with open('./tests/data/clean.html', 'w') as f:
            f.write('<meta><a>test</a><set/></meta><title></title><meta>')
        p = web.HTMLParser('./tests/data/clean.html')
        with self.assertRaises(ValueError):
            p.get_meta()
        p = web.HTMLParser('./tests/data/clean.html')
        with self.assertRaises(ValueError):
            p.remove_all()
        os.remove('./tests/data/clean.html')

        with open('./tests/data/clean.html', 'w') as f:
            f.write('<doctitle><br/></doctitle><br/><notclosed>')
        p = web.HTMLParser('./tests/data/clean.html')
        with self.assertRaises(ValueError):
            p.get_meta()
        p = web.HTMLParser('./tests/data/clean.html')
        with self.assertRaises(ValueError):
            p.remove_all()
        os.remove('./tests/data/clean.html')

    def test_epub(self):
        with zipfile.ZipFile('./tests/data/clean.epub', 'w') as zout:
            zout.write('./tests/data/dirty.jpg', 'OEBPS/content.opf')
        p, mimetype = parser_factory.get_parser('./tests/data/clean.epub')
        self.assertEqual(mimetype, 'application/epub+zip')
        meta = p.get_meta()
        self.assertEqual(meta['OEBPS/content.opf']['OEBPS/content.opf'],
                'harmful content')

        self.assertFalse(p.remove_all())
        os.remove('./tests/data/clean.epub')

    def test_tar(self):
        with tarfile.TarFile.open('./tests/data/clean.tar', 'w') as zout:
            zout.add('./tests/data/dirty.flac')
            zout.add('./tests/data/dirty.docx')
            zout.add('./tests/data/dirty.jpg')
            zout.add('./tests/data/embedded_corrupted.docx')
            tarinfo = tarfile.TarInfo(name='./tests/data/dirty.png')
            tarinfo.mtime = time.time()
            tarinfo.uid = 1337
            tarinfo.gid = 1338
            tarinfo.size = os.stat('./tests/data/dirty.png').st_size
            with open('./tests/data/dirty.png', 'rb') as f:
                zout.addfile(tarinfo, f)
        p, mimetype = parser_factory.get_parser('./tests/data/clean.tar')
        self.assertEqual(mimetype, 'application/x-tar')
        meta = p.get_meta()
        self.assertEqual(meta['./tests/data/dirty.flac']['comments'], 'Thank you for using MAT !')
        self.assertEqual(meta['./tests/data/dirty.docx']['word/media/image1.png']['Comment'], 'This is a comment, be careful!')
        self.assertFalse(p.remove_all())
        os.remove('./tests/data/clean.tar')

        shutil.copy('./tests/data/dirty.png', './tests/data/clean.tar')
        with self.assertRaises(ValueError):
            archive.TarParser('./tests/data/clean.tar')
        os.remove('./tests/data/clean.tar')

class TestReadOnlyArchiveMembers(unittest.TestCase):
    def test_onlymember_tar(self):
        with tarfile.open('./tests/data/clean.tar', 'w') as zout:
            zout.add('./tests/data/dirty.png')
            tarinfo = tarfile.TarInfo('./tests/data/dirty.jpg')
            tarinfo.mtime = time.time()
            tarinfo.uid = 1337
            tarinfo.gid = 0
            tarinfo.mode = 0o000
            tarinfo.size = os.stat('./tests/data/dirty.jpg').st_size
            with open('./tests/data/dirty.jpg', 'rb') as f:
                zout.addfile(tarinfo=tarinfo, fileobj=f)
        p, mimetype = parser_factory.get_parser('./tests/data/clean.tar')
        self.assertEqual(mimetype, 'application/x-tar')
        meta = p.get_meta()
        self.assertEqual(meta['./tests/data/dirty.jpg']['uid'], '1337')
        self.assertTrue(p.remove_all())

        p = archive.TarParser('./tests/data/clean.cleaned.tar')
        self.assertEqual(p.get_meta(), {})
        os.remove('./tests/data/clean.tar')
        os.remove('./tests/data/clean.cleaned.tar')


class TestPathTraversalArchiveMembers(unittest.TestCase):
    def test_tar_traversal(self):
        with tarfile.open('./tests/data/clean.tar', 'w') as zout:
            zout.add('./tests/data/dirty.png')
            tarinfo = tarfile.TarInfo('./tests/data/dirty.jpg')
            tarinfo.name = '../../../../../../../../../../tmp/mat2_test.png'
            with open('./tests/data/dirty.jpg', 'rb') as f:
                zout.addfile(tarinfo=tarinfo, fileobj=f)
        with self.assertRaises(ValueError):
            archive.TarParser('./tests/data/clean.tar')
        os.remove('./tests/data/clean.tar')

    def test_tar_absolute_path(self):
        with tarfile.open('./tests/data/clean.tar', 'w') as zout:
            zout.add('./tests/data/dirty.png')
            tarinfo = tarfile.TarInfo('./tests/data/dirty.jpg')
            tarinfo.name = '/etc/passwd'
            with open('./tests/data/dirty.jpg', 'rb') as f:
                zout.addfile(tarinfo=tarinfo, fileobj=f)
        with self.assertRaises(ValueError):
            archive.TarParser('./tests/data/clean.tar')
        os.remove('./tests/data/clean.tar')

    def test_tar_duplicate_file(self):
        with tarfile.open('./tests/data/clean.tar', 'w') as zout:
            for _ in range(3):
                zout.add('./tests/data/dirty.png')
                tarinfo = tarfile.TarInfo('./tests/data/dirty.jpg')
                with open('./tests/data/dirty.jpg', 'rb') as f:
                    zout.addfile(tarinfo=tarinfo, fileobj=f)
        with self.assertRaises(ValueError):
            archive.TarParser('./tests/data/clean.tar')
        os.remove('./tests/data/clean.tar')

    def test_tar_setuid(self):
        with tarfile.open('./tests/data/clean.tar', 'w') as zout:
            zout.add('./tests/data/dirty.png')
            tarinfo = tarfile.TarInfo('./tests/data/dirty.jpg')
            tarinfo.mode |= stat.S_ISUID
            with open('./tests/data/dirty.jpg', 'rb') as f:
                zout.addfile(tarinfo=tarinfo, fileobj=f)
        with self.assertRaises(ValueError):
            archive.TarParser('./tests/data/clean.tar')
        os.remove('./tests/data/clean.tar')

    def test_tar_setgid(self):
        with tarfile.open('./tests/data/clean.tar', 'w') as zout:
            zout.add('./tests/data/dirty.png')
            tarinfo = tarfile.TarInfo('./tests/data/dirty.jpg')
            tarinfo.mode |= stat.S_ISGID
            with open('./tests/data/dirty.jpg', 'rb') as f:
                zout.addfile(tarinfo=tarinfo, fileobj=f)
        with self.assertRaises(ValueError):
            archive.TarParser('./tests/data/clean.tar')
        os.remove('./tests/data/clean.tar')

    def test_tar_symlink_absolute(self):
        os.symlink('/etc/passwd', './tests/data/symlink')
        with tarfile.open('./tests/data/clean.tar', 'w') as zout:
            zout.add('./tests/data/symlink')
            tarinfo = tarfile.TarInfo('./tests/data/symlink')
            tarinfo.linkname = '/etc/passwd'
            tarinfo.type = tarfile.SYMTYPE
            with open('./tests/data/dirty.jpg', 'rb') as f:
                zout.addfile(tarinfo=tarinfo, fileobj=f)
        with self.assertRaises(ValueError):
            archive.TarParser('./tests/data/clean.tar')
        os.remove('./tests/data/clean.tar')
        os.remove('./tests/data/symlink')

    def test_tar_symlink_ok(self):
        shutil.copy('./tests/data/dirty.png', './tests/data/clean.png')
        with tarfile.open('./tests/data/clean.tar', 'w') as zout:
            zout.add('./tests/data/dirty.png')
            t = tarfile.TarInfo('mydir')
            t.type = tarfile.DIRTYPE
            zout.addfile(t)
            zout.add('./tests/data/clean.png')
            t = tarfile.TarInfo('mylink')
            t.type = tarfile.SYMTYPE
            t.linkname = './tests/data/clean.png'
            zout.addfile(t)
            zout.add('./tests/data/dirty.jpg')
        archive.TarParser('./tests/data/clean.tar')
        os.remove('./tests/data/clean.tar')
        os.remove('./tests/data/clean.png')

    def test_tar_symlink_relative(self):
        os.symlink('../../../etc/passwd', './tests/data/symlink')
        with tarfile.open('./tests/data/clean.tar', 'w') as zout:
            zout.add('./tests/data/symlink')
            tarinfo = tarfile.TarInfo('./tests/data/symlink')
            with open('./tests/data/dirty.jpg', 'rb') as f:
                zout.addfile(tarinfo=tarinfo, fileobj=f)
        with self.assertRaises(ValueError):
            archive.TarParser('./tests/data/clean.tar')
        os.remove('./tests/data/clean.tar')
        os.remove('./tests/data/symlink')

    def test_tar_device_file(self):
        with tarfile.open('./tests/data/clean.tar', 'w') as zout:
            zout.add('/dev/null')
        with self.assertRaises(ValueError):
            archive.TarParser('./tests/data/clean.tar')
        os.remove('./tests/data/clean.tar')

    def test_tar_hardlink(self):
        shutil.copy('./tests/data/dirty.png', './tests/data/clean.png')
        os.link('./tests/data/clean.png', './tests/data/hardlink.png')
        with tarfile.open('./tests/data/cleaner.tar', 'w') as zout:
            zout.add('tests/data/clean.png')
            zout.add('tests/data/hardlink.png')
        with self.assertRaises(ValueError):
            archive.TarParser('./tests/data/cleaner.tar')
        os.remove('./tests/data/cleaner.tar')
        os.remove('./tests/data/clean.png')
        os.remove('./tests/data/hardlink.png')

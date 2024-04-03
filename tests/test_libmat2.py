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
    def test_odt_with_py(self):
        shutil.copy('./tests/data/embedded.odt', './tests/data/clean.odt')
        p = office.LibreOfficeParser('./tests/data/clean.odt')
        self.assertFalse(p.remove_all())
        os.remove('./tests/data/clean.odt')

    def test_docx_with_py(self):
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

    def test_ppm(self):
        p = images.PPMParser('./tests/data/dirty.ppm')
        meta = p.get_meta()
        self.assertEqual(meta['1'], '# A metadata')
        self.assertEqual(meta['4'], '# And an other one')
        self.assertEqual(meta['6'], '# and a final one here')

    def test_tiff(self):
        p = images.TiffParser('./tests/data/dirty.tiff')
        meta = p.get_meta()
        self.assertEqual(meta['Make'], 'OLYMPUS IMAGING CORP.')
        self.assertEqual(meta['Model'], 'C7070WZ')
        self.assertEqual(meta['ModifyDate'], '2005:12:26 17:09:35')

    def test_wav(self):
        p = audio.WAVParser('./tests/data/dirty.wav')
        meta = p.get_meta()
        self.assertEqual(meta['Artist'], 'jvoisin')

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
            zout.write('./tests/data/dirty.flac',
                       compress_type = zipfile.ZIP_STORED)
            zout.write('./tests/data/dirty.docx',
                       compress_type = zipfile.ZIP_DEFLATED)
            zout.write('./tests/data/dirty.jpg',
                       compress_type = zipfile.ZIP_BZIP2)
            zout.write('./tests/data/dirty.txt',
                       compress_type = zipfile.ZIP_LZMA)
        p, mimetype = parser_factory.get_parser('./tests/data/dirty.zip')
        self.assertEqual(mimetype, 'application/zip')
        meta = p.get_meta()
        self.assertEqual(meta['tests/data/dirty.flac']['comments'], 'Thank you for using MAT !')
        self.assertEqual(meta['tests/data/dirty.docx']['word/media/image1.png']['Comment'], 'This is a comment, be careful!')

        with zipfile.ZipFile('./tests/data/dirty.zip') as zipin:
            members = {
                'tests/data/dirty.flac' : zipfile.ZIP_STORED,
                'tests/data/dirty.docx': zipfile.ZIP_DEFLATED,
                'tests/data/dirty.jpg' : zipfile.ZIP_BZIP2,
                'tests/data/dirty.txt' : zipfile.ZIP_LZMA,
            }
            for k, v in members.items():
                self.assertEqual(zipin.getinfo(k).compress_type, v)

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

    def test_svg(self):
        p = images.SVGParser('./tests/data/weird.svg')
        self.assertEqual(p.get_meta()['Xmlns'], 'http://www.w3.org/1337/svg')

    def test_aiff(self):
        p = audio.AIFFParser('./tests/data/dirty.aiff')
        meta = p.get_meta()
        self.assertEqual(meta['Name'], 'I am so')

    def test_heic(self):
        p = images.HEICParser('./tests/data/dirty.heic')
        meta = p.get_meta()
        self.assertEqual(meta['ProfileCopyright'], 'Public Domain')
        self.assertEqual(meta['ProfileDescription'], 'GIMP built-in sRGB')


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
            'name': 'wav',
            'parser': audio.WAVParser,
            'meta': {'Comment': 'Zomg, a comment!'},
            'expected_meta': {},
        }, {
            'name': 'aiff',
            'parser': audio.AIFFParser,
            'meta': {'Annotation': 'Thank you for using MAT !'},
            'expected_meta': {},
        },
        {
            'name': 'mp3',
            'parser': audio.MP3Parser,
            'meta': {'TXXX:I am a': 'various comment'},
            'expected_meta': {},
        }, {
            'name': 'ogg',
            'parser': audio.OGGParser,
            'meta': {'title': 'I am so'},
            'expected_meta': {},
        }, {
            'name': 'flac',
            'parser': audio.FLACParser,
            'meta': {'title': 'I am so'},
            'expected_meta': {},
        }, {
            'name': 'docx',
            'parser': office.MSOfficeParser,
            'meta': {'word/media/image1.png' :
               {'Comment': 'This is a comment, be careful!',
                'ModifyDate': '2018:03:20 21:59:25',
                'PixelUnits': 'meters',
                'PixelsPerUnitX': 2835,
                'PixelsPerUnitY': 2835,
                'create_system': 'Weird',
                'date_time': '2018-03-31 13:15:38'} ,
               },
            'expected_meta': {},
        }, {
            'name': 'odt',
            'parser': office.LibreOfficeParser,
            'meta': {
                'Pictures/1000000000000032000000311EC5314D.png': {
                    'create_system': 'Weird',
                    'date_time': '2011-07-26 02:40:16',
                    'PixelsPerUnitX': 4847,
                    'PixelsPerUnitY': 4760,
                    'PixelUnits': 'meters',
                    },
                },
            'expected_meta': {},
        },{
            'name': 'tiff',
            'parser': images.TiffParser,
            'meta': {'Model': 'C7070WZ'},
            'expected_meta':
             {'Orientation': 'Horizontal (normal)',
                  'ResolutionUnit': 'inches',
                  'XResolution': 72,
                  'YResolution': 72}
        },{
            'name': 'bmp',
            'parser': harmless.HarmlessParser,
            'meta': {},
            'expected_meta': {},
        },{
            'name': 'torrent',
            'parser': torrent.TorrentParser,
            'meta': {'created by': b'mktorrent 1.0', 'creation date': 1522397702},
            'expected_meta': {},
        }, {
            'name': 'odf',
            'parser': office.LibreOfficeParser,
            'meta': {'meta.xml': {'create_system': 'Weird', 'date_time':
                '2018-04-22 22:20:24', 'meta:initial-creator': 'Julien Voisin',
                'meta:creation-date': '2018-04-23T00:18:59.438231281',
                'dc:date': '2018-04-23T00:20:23.978564933', 'dc:creator':
                'Julien Voisin', 'meta:editing-duration': 'PT1M24S',
                'meta:editing-cycles': '1', 'meta:generator':
                'LibreOffice/5.4.6.2$Linux_X86_64 LibreOffice_project/40m0$Build-2'}},
            'expected_meta': {},
        }, {
            'name': 'odg',
            'parser': office.LibreOfficeParser,
            'meta': {'meta.xml': {'create_system': 'Weird', 'date_time':
                '2018-04-22 22:26:58', 'meta:initial-creator': 'Julien Voisin',
                'meta:creation-date': '2018-04-23T00:25:59.953271949',
                'dc:date': '2018-04-23T00:26:59.385838550', 'dc:creator':
                'Julien Voisin', 'meta:editing-duration': 'PT59S',
                'meta:editing-cycles': '1', 'meta:generator':
                'LibreOffice/5.4.6.2$Linux_X86_64 LibreOffice_project/40m0$Build-2'}},
            'expected_meta': {},
        }, {
            'name': 'txt',
            'parser': harmless.HarmlessParser,
            'meta': {},
            'expected_meta': {},
        },{
            'name': 'gif',
            'parser': images.GIFParser,
            'meta': {'Comment': 'this is a test comment'},
            'expected_meta': {'TransparentColor': '5'},
        },{
            'name': 'css',
            'parser': web.CSSParser,
            'meta': {
                'harmful data': 'underline is cool',
                'version': '1.0',
                'author': 'jvoisin'
            },
            'expected_meta': {},
        },{
            'name': 'svg',
            'parser': images.SVGParser,
            'meta': {
                'WorkDescription': "This is a test svg image for mat2's testsuite",
            },
            'expected_meta': {
                'ImageSize': '128x128',
                'Megapixels': '0.016',
            },
        } ,{
            'name': 'ppm',
            'parser': images.PPMParser,
            'meta': {
                '1': '# A metadata',
            },
            'expected_meta': {},
        } ,{
            'name': 'avi',
            'ffmpeg': 1,
            'parser': video.AVIParser,
            'meta': {
                'Software': 'MEncoder SVN-r33148-4.0.1',
            },
            'expected_meta': {},
        } ,{
            'name': 'mp4',
            'ffmpeg': 1,
            'parser': video.MP4Parser,
            'meta': {
                'Encoder':  'HandBrake 0.9.4 2009112300',
            },
            'expected_meta': {
                'AverageBitrate': 465641,
                'BufferSize': 0,
                'ColorPrimaries': 'BT.709',
                'ColorProfiles': 'nclx',
                'ColorRepresentation': 'nclx 1 1 1',
                'CompatibleBrands': ['isom', 'iso2', 'avc1', 'mp41'],
                'CompressorID': 'avc1',
                'CompressorName': 'JVT/AVC Coding',
                'GraphicsMode': 'srcCopy',
                'HandlerDescription': 'SoundHandler',
                'HandlerType': 'Metadata',
                'HandlerVendorID': 'Apple',
                'MajorBrand': 'Base Media v1 [IS0 14496-12:2003]',
                'MatrixCoefficients': 'BT.709',
                'MaxBitrate': 465641,
                'MediaDataOffset': 48,
                'MediaDataSize': 379872,
                'MediaHeaderVersion': 0,
                'MediaLanguageCode': 'eng',
                'MinorVersion': '0.2.0',
                'MovieDataOffset': 48,
                'MovieHeaderVersion': 0,
                'NextTrackID': 3,
                'PreferredRate': 1,
                'Rotation': 0,
                'TimeScale': 1000,
                'TrackHeaderVersion': 0,
                'TrackID': 1,
                'TrackLayer': 0,
                'TransferCharacteristics': 'BT.709',
                'VideoFullRangeFlag': 0,
            },
        },{
            'name': 'wmv',
            'ffmpeg': 1,
            'parser': video.WMVParser,
            'meta': {
                'EncodingSettings': 'Lavf52.103.0',
            },
            'expected_meta': {},
        },{
            'name': 'heic',
            'parser': images.HEICParser,
            'meta': {},
            'expected_meta': {},
        }
        ]

    def test_all_parametred(self):
        for case in self.data:
            with self.subTest(case=case):
                if 'ffmpeg' in case:
                    try:
                        video._get_ffmpeg_path()
                    except RuntimeError:
                        raise unittest.SkipTest

                print('[+] Testing %s' % case['name'])
                target = './tests/data/clean.' + case['name']
                shutil.copy('./tests/data/dirty.' + case['name'], target)
                p1 = case['parser'](target)

                for k, v in p1.get_meta().items():
                    if k not in case['meta']:
                        continue
                    if isinstance(v, dict):
                        for _k, _v in v.items():
                            if _k in case['meta'][k]:
                                self.assertEqual(_v, case['meta'][k][_k])
                    else:
                        self.assertEqual(v, case['meta'][k])

                p1.lightweight_cleaning = True
                self.assertTrue(p1.remove_all())

                p2 = case['parser'](p1.output_filename)
                meta = p2.get_meta()
                if meta:
                    for k, v in p2.get_meta().items():
                        self.assertIn(k, case['expected_meta'], '"%s" is not in "%s" (%s)' % (k, case['expected_meta'], case['name']))
                        self.assertIn(str(case['expected_meta'][k]), str(v))
                self.assertTrue(p2.remove_all())

                os.remove(target)
                os.remove(p1.output_filename)
                os.remove(p2.output_filename)


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


class TestCleaningArchives(unittest.TestCase):
    def test_zip(self):
        with zipfile.ZipFile('./tests/data/dirty.zip', 'w') as zout:
            zout.write('./tests/data/dirty.flac',
                       compress_type = zipfile.ZIP_STORED)
            zout.write('./tests/data/dirty.docx',
                       compress_type = zipfile.ZIP_DEFLATED)
            zout.write('./tests/data/dirty.jpg',
                       compress_type = zipfile.ZIP_BZIP2)
            zout.write('./tests/data/dirty.txt',
                       compress_type = zipfile.ZIP_LZMA)
        p = archive.ZipParser('./tests/data/dirty.zip')
        meta = p.get_meta()
        self.assertEqual(meta['tests/data/dirty.docx']['word/media/image1.png']['Comment'], 'This is a comment, be careful!')

        ret = p.remove_all()
        self.assertTrue(ret)

        p = archive.ZipParser('./tests/data/dirty.cleaned.zip')
        self.assertEqual(p.get_meta(), {})
        self.assertTrue(p.remove_all())

        with zipfile.ZipFile('./tests/data/dirty.zip') as zipin:
            members = {
                'tests/data/dirty.flac' : zipfile.ZIP_STORED,
                'tests/data/dirty.docx': zipfile.ZIP_DEFLATED,
                'tests/data/dirty.jpg' : zipfile.ZIP_BZIP2,
                'tests/data/dirty.txt' : zipfile.ZIP_LZMA,
            }
            for k, v in members.items():
                self.assertEqual(zipin.getinfo(k).compress_type, v)

        os.remove('./tests/data/dirty.zip')
        os.remove('./tests/data/dirty.cleaned.zip')
        os.remove('./tests/data/dirty.cleaned.cleaned.zip')

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

class TestNoSandbox(unittest.TestCase):
    def test_avi_nosandbox(self):
        shutil.copy('./tests/data/dirty.avi', './tests/data/clean.avi')
        p = video.AVIParser('./tests/data/clean.avi')
        p.sandbox = False

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

    def test_png_nosandbox(self):
        shutil.copy('./tests/data/dirty.png', './tests/data/clean.png')
        p = images.PNGParser('./tests/data/clean.png')
        p.sandbox = False
        p.lightweight_cleaning = True

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

class TestComplexOfficeFiles(unittest.TestCase):
    def test_complex_pptx(self):
        target = './tests/data/clean.pptx'
        shutil.copy('./tests/data/narrated_powerpoint_presentation.pptx', target)
        p = office.MSOfficeParser(target)
        self.assertTrue(p.remove_all())

        os.remove(target)
        os.remove(p.output_filename)

class TextDocx(unittest.TestCase):
    def test_comment_xml_is_removed(self):
        with zipfile.ZipFile('./tests/data/comment.docx') as zipin:
            # Check if 'word/comments.xml' exists in the zip
            self.assertIn('word/comments.xml', zipin.namelist())

        shutil.copy('./tests/data/comment.docx', './tests/data/comment_clean.docx')
        p = office.MSOfficeParser('./tests/data/comment_clean.docx')
        self.assertTrue(p.remove_all())

        with zipfile.ZipFile('./tests/data/comment_clean.cleaned.docx') as zipin:
            # Check if 'word/comments.xml' exists in the zip
            self.assertNotIn('word/comments.xml', zipin.namelist())

        os.remove('./tests/data/comment_clean.docx')
        os.remove('./tests/data/comment_clean.cleaned.docx')

    def test_comment_references_are_removed(self):
        with zipfile.ZipFile('./tests/data/comment.docx') as zipin:
            c = zipin.open('word/document.xml')
            content = c.read()

            r = b'w:commentRangeStart'
            self.assertIn(r, content)
            r = b'w:commentRangeEnd'
            self.assertIn(r, content)
            r = b'w:commentReference'
            self.assertIn(r, content)

        shutil.copy('./tests/data/comment.docx', './tests/data/comment_clean.docx')
        p = office.MSOfficeParser('./tests/data/comment_clean.docx')
        self.assertTrue(p.remove_all())

        with zipfile.ZipFile('./tests/data/comment_clean.cleaned.docx') as zipin:
            c = zipin.open('word/document.xml')
            content = c.read()

            r = b'w:commentRangeStart'
            self.assertNotIn(r, content)
            r = b'w:commentRangeEnd'
            self.assertNotIn(r, content)
            r = b'w:commentReference'
            self.assertNotIn(r, content)

        os.remove('./tests/data/comment_clean.docx')
        os.remove('./tests/data/comment_clean.cleaned.docx')
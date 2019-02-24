#!/usr/bin/env python3

import unittest
import shutil
import os
import zipfile
import tempfile

from libmat2 import office, parser_factory

class TestZipMetadata(unittest.TestCase):
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
        self.assertEqual(meta['word/media/image1.png']['Comment'], 'This is a comment, be careful!')

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


class TestZipOrder(unittest.TestCase):
    def test_libreoffice(self):
        shutil.copy('./tests/data/dirty.odt', './tests/data/clean.odt')
        p = office.LibreOfficeParser('./tests/data/clean.odt')

        meta = p.get_meta()
        self.assertIsNotNone(meta)

        is_unordered = False
        with zipfile.ZipFile('./tests/data/clean.odt') as zin:
            previous_name = ''
            for item in zin.infolist():
                if previous_name == '':
                    if item.filename == 'mimetype':
                        continue
                    previous_name = item.filename
                    continue
                elif item.filename < previous_name:
                    is_unordered = True
                    break
        self.assertTrue(is_unordered)

        ret = p.remove_all()
        self.assertTrue(ret)

        with zipfile.ZipFile('./tests/data/clean.cleaned.odt') as zin:
            previous_name = ''
            for item in zin.infolist():
                if previous_name == '':
                    if item.filename == 'mimetype':
                        continue
                    previous_name = item.filename
                    continue
                self.assertGreaterEqual(item.filename, previous_name)

        os.remove('./tests/data/clean.odt')
        os.remove('./tests/data/clean.cleaned.odt')

class TestRsidRemoval(unittest.TestCase):
    def test_office(self):
        shutil.copy('./tests/data/office_revision_session_ids.docx', './tests/data/clean.docx')
        p = office.MSOfficeParser('./tests/data/clean.docx')

        meta = p.get_meta()
        self.assertIsNotNone(meta)

        how_many_rsid = False
        with zipfile.ZipFile('./tests/data/clean.docx') as zin:
            for item in zin.infolist():
                if not item.filename.endswith('.xml'):
                    continue
                num = zin.read(item).decode('utf-8').lower().count('w:rsid')
                how_many_rsid += num
        self.assertEqual(how_many_rsid, 11)

        ret = p.remove_all()
        self.assertTrue(ret)

        with zipfile.ZipFile('./tests/data/clean.cleaned.docx') as zin:
            for item in zin.infolist():
                if not item.filename.endswith('.xml'):
                    continue
                num = zin.read(item).decode('utf-8').lower().count('w:rsid')
                self.assertEqual(num, 0)

        os.remove('./tests/data/clean.docx')
        os.remove('./tests/data/clean.cleaned.docx')

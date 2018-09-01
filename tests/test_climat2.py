import os
import shutil
import subprocess
import unittest


class TestHelp(unittest.TestCase):
    def test_help(self):
        proc = subprocess.Popen(['./mat2', '--help'], stdout=subprocess.PIPE)
        stdout, _ = proc.communicate()
        self.assertIn(b'usage: mat2 [-h] [-v] [-l] [-c] [-V] [-s | -L] [files [files ...]]', stdout)

    def test_no_arg(self):
        proc = subprocess.Popen(['./mat2'], stdout=subprocess.PIPE)
        stdout, _ = proc.communicate()
        self.assertIn(b'usage: mat2 [-h] [-v] [-l] [-c] [-V] [-s | -L] [files [files ...]]', stdout)


class TestVersion(unittest.TestCase):
    def test_version(self):
        proc = subprocess.Popen(['./mat2', '--version'], stdout=subprocess.PIPE)
        stdout, _ = proc.communicate()
        self.assertTrue(stdout.startswith(b'MAT2 '))

class TestDependencies(unittest.TestCase):
    def test_dependencies(self):
        proc = subprocess.Popen(['./mat2', '--check-dependencies'], stdout=subprocess.PIPE)
        stdout, _ = proc.communicate()
        self.assertTrue(b'MAT2' in stdout)

class TestReturnValue(unittest.TestCase):
    def test_nonzero(self):
        ret = subprocess.call(['./mat2', './mat2'], stdout=subprocess.DEVNULL)
        self.assertEqual(255, ret)

        ret = subprocess.call(['./mat2', '--whololo'], stderr=subprocess.DEVNULL)
        self.assertEqual(2, ret)

    def test_zero(self):
        ret = subprocess.call(['./mat2'], stdout=subprocess.DEVNULL)
        self.assertEqual(0, ret)

        ret = subprocess.call(['./mat2', '--show', './mat2'], stdout=subprocess.DEVNULL)
        self.assertEqual(0, ret)


class TestCleanFolder(unittest.TestCase):
    def test_jpg(self):
        os.mkdir('./tests/data/folder/')
        shutil.copy('./tests/data/dirty.jpg', './tests/data/folder/clean1.jpg')
        shutil.copy('./tests/data/dirty.jpg', './tests/data/folder/clean2.jpg')

        proc = subprocess.Popen(['./mat2', '--show', './tests/data/folder/'],
                stdout=subprocess.PIPE)
        stdout, _ = proc.communicate()
        self.assertIn(b'Comment: Created with GIMP', stdout)

        proc = subprocess.Popen(['./mat2', './tests/data/folder/'],
                stdout=subprocess.PIPE)
        stdout, _ = proc.communicate()

        os.remove('./tests/data/folder/clean1.jpg')
        os.remove('./tests/data/folder/clean2.jpg')

        proc = subprocess.Popen(['./mat2', '--show', './tests/data/folder/'],
                stdout=subprocess.PIPE)
        stdout, _ = proc.communicate()
        self.assertNotIn(b'Comment: Created with GIMP', stdout)

        shutil.rmtree('./tests/data/folder/')



class TestCleanMeta(unittest.TestCase):
    def test_jpg(self):
        shutil.copy('./tests/data/dirty.jpg', './tests/data/clean.jpg')

        proc = subprocess.Popen(['./mat2', '--show', './tests/data/clean.jpg'],
                stdout=subprocess.PIPE)
        stdout, _ = proc.communicate()
        self.assertIn(b'Comment: Created with GIMP', stdout)

        proc = subprocess.Popen(['./mat2', './tests/data/clean.jpg'],
                stdout=subprocess.PIPE)
        stdout, _ = proc.communicate()

        proc = subprocess.Popen(['./mat2', '--show', './tests/data/clean.cleaned.jpg'],
                stdout=subprocess.PIPE)
        stdout, _ = proc.communicate()
        self.assertNotIn(b'Comment: Created with GIMP', stdout)

        os.remove('./tests/data/clean.jpg')


class TestIsSupported(unittest.TestCase):
    def test_pdf(self):
        proc = subprocess.Popen(['./mat2', '--show', './tests/data/dirty.pdf'],
                stdout=subprocess.PIPE)
        stdout, _ = proc.communicate()
        self.assertNotIn(b"isn't supported", stdout)

class TestGetMeta(unittest.TestCase):
    def test_pdf(self):
        proc = subprocess.Popen(['./mat2', '--show', './tests/data/dirty.pdf'],
                stdout=subprocess.PIPE)
        stdout, _ = proc.communicate()
        self.assertIn(b'producer: pdfTeX-1.40.14', stdout)

    def test_png(self):
        proc = subprocess.Popen(['./mat2', '--show', './tests/data/dirty.png'],
                stdout=subprocess.PIPE)
        stdout, _ = proc.communicate()
        self.assertIn(b'Comment: This is a comment, be careful!', stdout)

    def test_jpg(self):
        proc = subprocess.Popen(['./mat2', '--show', './tests/data/dirty.jpg'],
                stdout=subprocess.PIPE)
        stdout, _ = proc.communicate()
        self.assertIn(b'Comment: Created with GIMP', stdout)

    def test_docx(self):
        proc = subprocess.Popen(['./mat2', '--show', './tests/data/dirty.docx'],
                stdout=subprocess.PIPE)
        stdout, _ = proc.communicate()
        self.assertIn(b'Application: LibreOffice/5.4.5.1$Linux_X86_64', stdout)
        self.assertIn(b'creator: julien voisin', stdout)
        self.assertIn(b'revision: 1', stdout)

    def test_odt(self):
        proc = subprocess.Popen(['./mat2', '--show', './tests/data/dirty.odt'],
                stdout=subprocess.PIPE)
        stdout, _ = proc.communicate()
        self.assertIn(b'generator: LibreOffice/3.3$Unix', stdout)
        self.assertIn(b'creator: jvoisin', stdout)
        self.assertIn(b'date_time: 2011-07-26 02:40:16', stdout)

    def test_mp3(self):
        proc = subprocess.Popen(['./mat2', '--show', './tests/data/dirty.mp3'],
                stdout=subprocess.PIPE)
        stdout, _ = proc.communicate()
        self.assertIn(b'TALB: harmfull', stdout)
        self.assertIn(b'COMM::: Thank you for using MAT !', stdout)

    def test_flac(self):
        proc = subprocess.Popen(['./mat2', '--show', './tests/data/dirty.flac'],
                stdout=subprocess.PIPE)
        stdout, _ = proc.communicate()
        self.assertIn(b'comments: Thank you for using MAT !', stdout)
        self.assertIn(b'genre: Python', stdout)
        self.assertIn(b'title: I am so', stdout)

    def test_ogg(self):
        proc = subprocess.Popen(['./mat2', '--show', './tests/data/dirty.ogg'],
                stdout=subprocess.PIPE)
        stdout, _ = proc.communicate()
        self.assertIn(b'comments: Thank you for using MAT !', stdout)
        self.assertIn(b'genre: Python', stdout)
        self.assertIn(b'i am a : various comment', stdout)
        self.assertIn(b'artist: jvoisin', stdout)

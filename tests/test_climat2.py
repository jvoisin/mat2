import random
import os
import shutil
import subprocess
import unittest
import glob

from libmat2 import images, parser_factory


mat2_binary = ['./mat2']

if 'MAT2_GLOBAL_PATH_TESTSUITE' in os.environ:
    # Debian runs tests after installing the package
    # https://0xacab.org/jvoisin/mat2/issues/16#note_153878
    mat2_binary = ['/usr/bin/env', 'mat2']


class TestHelp(unittest.TestCase):
    def test_help(self):
        proc = subprocess.Popen(mat2_binary + ['--help'], stdout=subprocess.PIPE)
        stdout, _ = proc.communicate()
        self.assertIn(b'usage: mat2 [-h] [-v] [-l] [--check-dependencies] [-V]',
                      stdout)
        self.assertIn(b'[--unknown-members policy] [-s | -L]', stdout)

    def test_no_arg(self):
        proc = subprocess.Popen(mat2_binary, stdout=subprocess.PIPE)
        stdout, _ = proc.communicate()
        self.assertIn(b'usage: mat2 [-h] [-v] [-l] [--check-dependencies] [-V]',
                      stdout)
        self.assertIn(b'[--unknown-members policy] [-s | -L]', stdout)


class TestVersion(unittest.TestCase):
    def test_version(self):
        proc = subprocess.Popen(mat2_binary + ['--version'], stdout=subprocess.PIPE)
        stdout, _ = proc.communicate()
        self.assertTrue(stdout.startswith(b'MAT2 '))

class TestDependencies(unittest.TestCase):
    def test_dependencies(self):
        proc = subprocess.Popen(mat2_binary + ['--check-dependencies'], stdout=subprocess.PIPE)
        stdout, _ = proc.communicate()
        self.assertTrue(b'MAT2' in stdout)

class TestReturnValue(unittest.TestCase):
    def test_nonzero(self):
        ret = subprocess.call(mat2_binary + ['mat2'], stdout=subprocess.DEVNULL)
        self.assertEqual(255, ret)

        ret = subprocess.call(mat2_binary + ['--whololo'], stderr=subprocess.DEVNULL)
        self.assertEqual(2, ret)

    def test_zero(self):
        ret = subprocess.call(mat2_binary, stdout=subprocess.DEVNULL)
        self.assertEqual(0, ret)

        ret = subprocess.call(mat2_binary + ['--show', 'mat2'], stdout=subprocess.DEVNULL)
        self.assertEqual(0, ret)


class TestCleanFolder(unittest.TestCase):
    def test_jpg(self):
        try:
            os.mkdir('./tests/data/folder/')
        except FileExistsError:
            pass
        shutil.copy('./tests/data/dirty.jpg', './tests/data/folder/clean1.jpg')
        shutil.copy('./tests/data/dirty.jpg', './tests/data/folder/clean2.jpg')

        proc = subprocess.Popen(mat2_binary + ['--show', './tests/data/folder/'],
                stdout=subprocess.PIPE)
        stdout, _ = proc.communicate()
        self.assertIn(b'Comment: Created with GIMP', stdout)

        proc = subprocess.Popen(mat2_binary + ['./tests/data/folder/'],
                stdout=subprocess.PIPE)
        stdout, _ = proc.communicate()

        os.remove('./tests/data/folder/clean1.jpg')
        os.remove('./tests/data/folder/clean2.jpg')

        proc = subprocess.Popen(mat2_binary + ['--show', './tests/data/folder/'],
                stdout=subprocess.PIPE)
        stdout, _ = proc.communicate()
        self.assertNotIn(b'Comment: Created with GIMP', stdout)
        self.assertIn(b'No metadata found', stdout)

        shutil.rmtree('./tests/data/folder/')


class TestCleanMeta(unittest.TestCase):
    def test_jpg(self):
        shutil.copy('./tests/data/dirty.jpg', './tests/data/clean.jpg')

        proc = subprocess.Popen(mat2_binary + ['--show', './tests/data/clean.jpg'],
                stdout=subprocess.PIPE)
        stdout, _ = proc.communicate()
        self.assertIn(b'Comment: Created with GIMP', stdout)

        proc = subprocess.Popen(mat2_binary + ['./tests/data/clean.jpg'],
                stdout=subprocess.PIPE)
        stdout, _ = proc.communicate()

        proc = subprocess.Popen(mat2_binary + ['--show', './tests/data/clean.cleaned.jpg'],
                stdout=subprocess.PIPE)
        stdout, _ = proc.communicate()
        self.assertNotIn(b'Comment: Created with GIMP', stdout)

        os.remove('./tests/data/clean.jpg')


class TestIsSupported(unittest.TestCase):
    def test_pdf(self):
        proc = subprocess.Popen(mat2_binary + ['--show', './tests/data/dirty.pdf'],
                stdout=subprocess.PIPE)
        stdout, _ = proc.communicate()
        self.assertNotIn(b"isn't supported", stdout)

class TestGetMeta(unittest.TestCase):
    maxDiff = None

    def test_pdf(self):
        proc = subprocess.Popen(mat2_binary + ['--show', './tests/data/dirty.pdf'],
                stdout=subprocess.PIPE)
        stdout, _ = proc.communicate()
        self.assertIn(b'Producer: pdfTeX-1.40.14', stdout)

    def test_png(self):
        proc = subprocess.Popen(mat2_binary + ['--show', './tests/data/dirty.png'],
                stdout=subprocess.PIPE)
        stdout, _ = proc.communicate()
        self.assertIn(b'Comment: This is a comment, be careful!', stdout)

    def test_jpg(self):
        proc = subprocess.Popen(mat2_binary + ['--show', './tests/data/dirty.jpg'],
                stdout=subprocess.PIPE)
        stdout, _ = proc.communicate()
        self.assertIn(b'Comment: Created with GIMP', stdout)

    def test_docx(self):
        proc = subprocess.Popen(mat2_binary + ['--show', './tests/data/dirty.docx'],
                stdout=subprocess.PIPE)
        stdout, _ = proc.communicate()
        self.assertIn(b'Application: LibreOffice/5.4.5.1$Linux_X86_64', stdout)
        self.assertIn(b'creator: julien voisin', stdout)
        self.assertIn(b'revision: 1', stdout)

    def test_odt(self):
        proc = subprocess.Popen(mat2_binary + ['--show', './tests/data/dirty.odt'],
                stdout=subprocess.PIPE)
        stdout, _ = proc.communicate()
        self.assertIn(b'generator: LibreOffice/3.3$Unix', stdout)
        self.assertIn(b'creator: jvoisin', stdout)
        self.assertIn(b'date_time: 2011-07-26 02:40:16', stdout)

    def test_mp3(self):
        proc = subprocess.Popen(mat2_binary + ['--show', './tests/data/dirty.mp3'],
                stdout=subprocess.PIPE)
        stdout, _ = proc.communicate()
        self.assertIn(b'TALB: harmfull', stdout)
        self.assertIn(b'COMM::: Thank you for using MAT !', stdout)

    def test_flac(self):
        proc = subprocess.Popen(mat2_binary + ['--show', './tests/data/dirty.flac'],
                stdout=subprocess.PIPE, bufsize=0)
        stdout, _ = proc.communicate()
        self.assertIn(b'comments: Thank you for using MAT !', stdout)
        self.assertIn(b'genre: Python', stdout)
        self.assertIn(b'title: I am so', stdout)

    def test_ogg(self):
        proc = subprocess.Popen(mat2_binary + ['--show', './tests/data/dirty.ogg'],
                stdout=subprocess.PIPE)
        stdout, _ = proc.communicate()
        self.assertIn(b'comments: Thank you for using MAT !', stdout)
        self.assertIn(b'genre: Python', stdout)
        self.assertIn(b'i am a : various comment', stdout)
        self.assertIn(b'artist: jvoisin', stdout)

class TestControlCharInjection(unittest.TestCase):
    def test_jpg(self):
        proc = subprocess.Popen(mat2_binary + ['--show', './tests/data/control_chars.jpg'],
                stdout=subprocess.PIPE)
        stdout, _ = proc.communicate()
        self.assertIn(b'Comment: GQ\n', stdout)


class TestCommandLineParallel(unittest.TestCase):
    iterations = 24

    def test_same(self):
        for i in range(self.iterations):
            shutil.copy('./tests/data/dirty.jpg', './tests/data/dirty_%d.jpg' % i)

        proc = subprocess.Popen(mat2_binary + ['./tests/data/dirty_%d.jpg' % i for i in range(self.iterations)],
                stdout=subprocess.PIPE)
        stdout, _ = proc.communicate()

        for i in range(self.iterations):
            path = './tests/data/dirty_%d.jpg' % i
            p = images.JPGParser('./tests/data/dirty_%d.cleaned.jpg' % i)
            self.assertEqual(p.get_meta(), {})
            os.remove('./tests/data/dirty_%d.cleaned.jpg' % i)
            os.remove(path)

    def test_different(self):
        shutil.copytree('./tests/data/', './tests/data/parallel')

        proc = subprocess.Popen(mat2_binary + glob.glob('./tests/data/parallel/dirty.*'),
                stdout=subprocess.PIPE)
        stdout, _ = proc.communicate()

        for i in glob.glob('./test/data/parallel/dirty.cleaned.*'):
            p, mime = parser_factory.get_parser(i)
            self.assertIsNotNone(mime)
            self.assertIsNotNone(p)
            p = parser_factory.get_parser(p.output_filename)
            self.assertEqual(p.get_meta(), {})
        shutil.rmtree('./tests/data/parallel')

    def test_faulty(self):
        for i in range(self.iterations):
            shutil.copy('./tests/data/dirty.jpg', './tests/data/dirty_%d.jpg' % i)
            shutil.copy('./tests/data/dirty.torrent', './tests/data/dirty_%d.docx' % i)

        to_process = ['./tests/data/dirty_%d.jpg' % i for i in range(self.iterations)]
        to_process.extend(['./tests/data/dirty_%d.docx' % i for i in range(self.iterations)])
        random.shuffle(to_process)
        proc = subprocess.Popen(mat2_binary + to_process,
                stdout=subprocess.PIPE)
        stdout, _ = proc.communicate()

        for i in range(self.iterations):
            path = './tests/data/dirty_%d.jpg' % i
            p = images.JPGParser('./tests/data/dirty_%d.cleaned.jpg' % i)
            self.assertEqual(p.get_meta(), {})
            os.remove('./tests/data/dirty_%d.cleaned.jpg' % i)
            os.remove(path)
            os.remove('./tests/data/dirty_%d.docx' % i)

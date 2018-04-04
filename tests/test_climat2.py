import unittest
import subprocess


class TestHelp(unittest.TestCase):
    def test_help(self):
        proc = subprocess.Popen(['./main.py', '--help'], stdout=subprocess.PIPE)
        stdout, _ = proc.communicate()
        self.assertIn(b'usage: main.py [-h] [-c] [-l] [-s] [files [files ...]]', stdout)

    def test_no_arg(self):
        proc = subprocess.Popen(['./main.py'], stdout=subprocess.PIPE)
        stdout, _ = proc.communicate()
        self.assertIn(b'usage: main.py [-h] [-c] [-l] [-s] [files [files ...]]', stdout)


class TestGetMeta(unittest.TestCase):
    def test_pdf(self):
        proc = subprocess.Popen(['./main.py', '--show', './tests/data/dirty.pdf'],
                stdout=subprocess.PIPE)
        stdout, _ = proc.communicate()
        self.assertIn(b'producer: pdfTeX-1.40.14', stdout)

    def test_png(self):
        proc = subprocess.Popen(['./main.py', '--show', './tests/data/dirty.png'],
                stdout=subprocess.PIPE)
        stdout, _ = proc.communicate()
        self.assertIn(b'Comment: This is a comment, be careful!', stdout)

    def test_jpg(self):
        proc = subprocess.Popen(['./main.py', '--show', './tests/data/dirty.jpg'],
                stdout=subprocess.PIPE)
        stdout, _ = proc.communicate()
        self.assertIn(b'Comment: Created with GIMP', stdout)

    def test_docx(self):
        proc = subprocess.Popen(['./main.py', '--show', './tests/data/dirty.docx'],
                stdout=subprocess.PIPE)
        stdout, _ = proc.communicate()
        self.assertIn(b'Application: LibreOffice/5.4.5.1$Linux_X86_64', stdout)
        self.assertIn(b'creator: julien voisin', stdout)
        self.assertIn(b'revision: 1', stdout)

    def test_odt(self):
        proc = subprocess.Popen(['./main.py', '--show', './tests/data/dirty.odt'],
                stdout=subprocess.PIPE)
        stdout, _ = proc.communicate()
        self.assertIn(b'generator: LibreOffice/3.3$Unix', stdout)
        self.assertIn(b'creator: jvoisin', stdout)
        self.assertIn(b'date_time: 2011-07-26 02:40:16', stdout)

    def test_mp3(self):
        proc = subprocess.Popen(['./main.py', '--show', './tests/data/dirty.mp3'],
                stdout=subprocess.PIPE)
        stdout, _ = proc.communicate()
        self.assertIn(b'TALB: harmfull', stdout)
        self.assertIn(b'COMM::: Thank you for using MAT !', stdout)

    def test_flac(self):
        proc = subprocess.Popen(['./main.py', '--show', './tests/data/dirty.flac'],
                stdout=subprocess.PIPE)
        stdout, _ = proc.communicate()
        self.assertIn(b'comments: Thank you for using MAT !', stdout)
        self.assertIn(b'genre: Python', stdout)
        self.assertIn(b'title: I am so', stdout)

    def test_ogg(self):
        proc = subprocess.Popen(['./main.py', '--show', './tests/data/dirty.ogg'],
                stdout=subprocess.PIPE)
        stdout, _ = proc.communicate()
        self.assertIn(b'comments: Thank you for using MAT !', stdout)
        self.assertIn(b'genre: Python', stdout)
        self.assertIn(b'i am a : various comment', stdout)
        self.assertIn(b'artist: jvoisin', stdout)

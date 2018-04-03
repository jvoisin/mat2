import unittest
import subprocess
import os


class TestHelp(unittest.TestCase):
    def test_help(self):
        proc = subprocess.Popen(['./main.py', '--help'], stdout=subprocess.PIPE)
        stdout, _ = proc.communicate()
        self.assertIn(b'usage: main.py [-h] [-c] [-l] [-s] [files [files ...]]', stdout)

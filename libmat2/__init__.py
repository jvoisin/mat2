#!/bin/env python3

import os
import collections
import importlib
from typing import Dict

# make pyflakes happy
assert Dict

# A set of extension that aren't supported, despite matching a supported mimetype
UNSUPPORTED_EXTENSIONS = {
    '.asc',
    '.bat',
    '.brf',
    '.c',
    '.h',
    '.ksh',
    '.pl',
    '.pot',
    '.rdf',
    '.srt',
    '.wsdl',
    '.xpdl',
    '.xsd',
    '.xsl',
    }

DEPENDENCIES = {
    'cairo': 'Cairo',
    'gi': 'PyGobject',
    'gi.repository.GdkPixbuf': 'GdkPixbuf from PyGobject',
    'gi.repository.Poppler': 'Poppler from PyGobject',
    'gi.repository.GLib': 'GLib from PyGobject',
    'mutagen': 'Mutagen',
    }

def check_dependencies() -> dict:
    ret = collections.defaultdict(bool)  # type: Dict[str, bool]

    exiftool = '/usr/bin/exiftool'
    ret['Exiftool'] = False
    if os.path.isfile(exiftool) and os.access(exiftool, os.X_OK):  # pragma: no cover
        ret['Exiftool'] = True

    for key, value in DEPENDENCIES.items():
        ret[value] = True
        try:
            importlib.import_module(key)
        except ImportError:  # pragma: no cover
            ret[value] = False  # pragma: no cover

    return ret

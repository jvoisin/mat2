#!/usr/bin/env python3

import collections
import enum
import importlib
from typing import Dict, Optional

from . import exiftool, video

# make pyflakes happy
assert Dict
assert Optional

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

    ret['Exiftool'] = True if exiftool._get_exiftool_path() else False
    ret['Ffmpeg'] = True if video._get_ffmpeg_path() else False

    for key, value in DEPENDENCIES.items():
        ret[value] = True
        try:
            importlib.import_module(key)
        except ImportError:  # pragma: no cover
            ret[value] = False  # pragma: no cover

    return ret

@enum.unique
class UnknownMemberPolicy(enum.Enum):
    ABORT = 'abort'
    OMIT = 'omit'
    KEEP = 'keep'

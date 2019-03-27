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
    'Cairo': 'cairo',
    'PyGobject': 'gi',
    'GdkPixbuf from PyGobject': 'gi.repository.GdkPixbuf',
    'Poppler from PyGobject': 'gi.repository.Poppler',
    'GLib from PyGobject': 'gi.repository.GLib',
    'Mutagen': 'mutagen',
    }


def check_dependencies() -> Dict[str, bool]:
    ret = collections.defaultdict(bool)  # type: Dict[str, bool]

    ret['Exiftool'] = bool(exiftool._get_exiftool_path())
    ret['Ffmpeg'] = bool(video._get_ffmpeg_path())

    for key, value in DEPENDENCIES.items():
        ret[key] = True
        try:
            importlib.import_module(value)
        except ImportError:  # pragma: no cover
            ret[key] = False  # pragma: no cover

    return ret


@enum.unique
class UnknownMemberPolicy(enum.Enum):
    ABORT = 'abort'
    OMIT = 'omit'
    KEEP = 'keep'

import glob
import os
import mimetypes
import importlib
from typing import TypeVar, Optional, List

from . import abstract, UNSUPPORTED_EXTENSIONS

T = TypeVar('T', bound='abstract.AbstractParser')

mimetypes.add_type('application/epub+zip', '.epub')
mimetypes.add_type('application/x-dtbncx+xml', '.ncx')  # EPUB Navigation Control XML File

# This should be removed after we move to python3.10
# https://github.com/python/cpython/commit/20a5b7e986377bdfd929d7e8c4e3db5847dfdb2d
mimetypes.add_type('image/heic', '.heic')


def __load_all_parsers():
    """ Loads every parser in a dynamic way """
    current_dir = os.path.dirname(__file__)
    for fname in glob.glob(os.path.join(current_dir, '*.py')):
        if fname.endswith('abstract.py'):
            continue
        elif fname.endswith('__init__.py'):
            continue
        elif fname.endswith('exiftool.py'):
            continue
        basename = os.path.basename(fname)
        name, _ = os.path.splitext(basename)
        importlib.import_module('.' + name, package='libmat2')


__load_all_parsers()


def _get_parsers() -> List[T]:
    """ Get all our parsers!"""
    def __get_parsers(cls):
        return cls.__subclasses__() + \
            [g for s in cls.__subclasses__() for g in __get_parsers(s)]
    return __get_parsers(abstract.AbstractParser)


def get_parser(filename: str) -> tuple[Optional[T], Optional[str]]:
    """ Return the appropriate parser for a given filename.

        :raises ValueError: Raised if the instantiation of the parser went wrong.
    """
    mtype, _ = mimetypes.guess_type(filename)

    _, extension = os.path.splitext(filename)
    if extension.lower() in UNSUPPORTED_EXTENSIONS:
        return None, mtype

    if mtype == 'application/x-tar':
        if extension[1:] in ('bz2', 'gz', 'xz'):
            mtype = mtype + '+' + extension[1:]

    for parser_class in _get_parsers():  # type: ignore
        if mtype in parser_class.mimetypes:
            # This instantiation might raise a ValueError on malformed files
            return parser_class(filename), mtype
    return None, mtype

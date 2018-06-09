import glob
import os
import mimetypes
import importlib
from typing import TypeVar, List, Tuple, Optional

from . import abstract, unsupported_extensions

assert Tuple  # make pyflakes happy

T = TypeVar('T', bound='abstract.AbstractParser')

def __load_all_parsers():
    """ Loads every parser in a dynamic way """
    current_dir = os.path.dirname(__file__)
    for name in glob.glob(os.path.join(current_dir, '*.py')):
        if name.endswith('abstract.py') or name.endswith('__init__.py'):
            continue
        basename = os.path.basename(name)
        name, _ = os.path.splitext(basename)
        importlib.import_module('.' + name, package='libmat2')

__load_all_parsers()

def _get_parsers() -> List[T]:
    """ Get all our parsers!"""
    def __get_parsers(cls):
        return cls.__subclasses__() + \
            [g for s in cls.__subclasses__() for g in __get_parsers(s)]
    return __get_parsers(abstract.AbstractParser)


def get_parser(filename: str) -> Tuple[Optional[T], Optional[str]]:
    mtype, _ = mimetypes.guess_type(filename)

    _, extension = os.path.splitext(filename)
    if extension in unsupported_extensions:
        return None, mtype

    for c in _get_parsers():  # type: ignore
        if mtype in c.mimetypes:
            try:
                return c(filename), mtype
            except ValueError:
                return None, mtype
    return None, mtype

import os
import mimetypes
import importlib
import pkgutil
from typing import TypeVar, List

from . import abstract, unsupported_extensions


T = TypeVar('T', bound='abstract.AbstractParser')

# This loads every parser in a dynamic way
for module_loader, name, ispkg in pkgutil.walk_packages('.libmat2'):
    if not name.startswith('libmat2.'):
        continue
    elif name == 'libmat2.abstract':
        continue
    importlib.import_module(name)


def _get_parsers() -> List[T]:
    """ Get all our parsers!"""
    def __get_parsers(cls):
        return cls.__subclasses__() + \
            [g for s in cls.__subclasses__() for g in __get_parsers(s)]
    return __get_parsers(abstract.AbstractParser)


def get_parser(filename: str) -> (T, str):
    mtype, _ = mimetypes.guess_type(filename)

    _, extension = os.path.splitext(filename)
    if extension in unsupported_extensions:
        return None, mtype

    for c in _get_parsers():
        if mtype in c.mimetypes:
            try:
                return c(filename), mtype
            except ValueError:
                return None, mtype
    return None, mtype

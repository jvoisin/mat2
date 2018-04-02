import mimetypes
import importlib
import pkgutil

from . import abstract

from typing import Type, TypeVar

T = TypeVar('T', bound='abstract.AbstractParser')

# This loads every parser in a dynamic way
for module_loader, name, ispkg in pkgutil.walk_packages('.src'):
    if not name.startswith('src.'):
        continue
    elif name == 'src.abstract':
        continue
    importlib.import_module(name)

def get_parser(filename: str) -> (T, str):
    mtype, _ = mimetypes.guess_type(filename)
    def get_subclasses(cls):
        return cls.__subclasses__() + \
               [g for s in cls.__subclasses__() for g in get_subclasses(s)]
    for c in get_subclasses(abstract.AbstractParser):
        if mtype in c.mimetypes:
            return c(filename), mtype
    return None, mtype

import mimetypes
import importlib
import pkgutil

from . import abstract

from typing import Type, TypeVar

T = TypeVar('T', bound='abstract.AbstractParser')

for module_loader, name, ispkg in pkgutil.walk_packages('.src'):
    if not name.startswith('src.'):
        continue
    elif name == 'src.abstract':
        continue
    importlib.import_module(name)

def get_parser(filename: str) -> (T, str):
    mtype, _ = mimetypes.guess_type(filename)
    for c in abstract.AbstractParser.__subclasses__():
        if mtype in c.mimetypes:
            return c(filename), mtype
    return None, mtype

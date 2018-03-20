import mimetypes
import importlib
import pkgutil

from .parsers import abstract

for module_loader, name, ispkg in pkgutil.walk_packages('.src.parsers'):
    if not name.startswith('src.parsers.'):
        continue
    elif name == 'src.parsers.abstract':
        continue
    importlib.import_module(name)

def get_parser(filename: str):
    mtype, _ = mimetypes.guess_type(filename)
    for c in abstract.AbstractParser.__subclasses__():
        if mtype in c.mimetypes:
            return c(filename)
    print('Nope')

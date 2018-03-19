import mimetypes

from .parsers import abstract
from .parsers import *

def get_parser(filename: str):
    mtype, _ = mimetypes.guess_type(filename)
    for c in abstract.AbstractParser.__subclasses__():
        if mtype in c.mimetypes:
            return c(filename)

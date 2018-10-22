import json
import os
import subprocess
from typing import Dict, Union, Set

from . import abstract

# Make pyflakes happy
assert Set


class ExiftoolParser(abstract.AbstractParser):
    """ Exiftool is often the easiest way to get all the metadata
    from a import file, hence why several parsers are re-using its `get_meta`
    method.
    """
    meta_whitelist = set()  # type: Set[str]

    def get_meta(self) -> Dict[str, Union[str, dict]]:
        out = subprocess.check_output([_get_exiftool_path(), '-json', self.filename])
        meta = json.loads(out.decode('utf-8'))[0]
        for key in self.meta_whitelist:
            meta.pop(key, None)
        return meta

def _get_exiftool_path() -> str:  # pragma: no cover
    exiftool_path = '/usr/bin/exiftool'
    if os.path.isfile(exiftool_path):
        if os.access(exiftool_path, os.X_OK):
            return exiftool_path

    # ArchLinux
    exiftool_path = '/usr/bin/vendor_perl/exiftool'
    if os.path.isfile(exiftool_path):
        if os.access(exiftool_path, os.X_OK):
            return exiftool_path

    raise RuntimeError("Unable to find exiftool")

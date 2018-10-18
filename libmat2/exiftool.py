import json
import os
import re
import shutil
import subprocess
import tempfile

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

    @staticmethod
    def __handle_problematic_filename(filename: str, callback) -> bytes:
        """ This method takes a filename with a problematic name,
        and safely applies it a `callback`."""
        tmpdirname = tempfile.mkdtemp()
        fname = os.path.join(tmpdirname, "temp_file")
        shutil.copy(filename, fname)
        out = callback(fname)
        shutil.rmtree(tmpdirname)
        return out

    def get_meta(self) -> Dict[str, Union[str, dict]]:
        """ There is no way to escape the leading(s) dash(es) of the current
        self.filename to prevent parameter injections, so we need to take care
        of this.
        """
        fun = lambda f: subprocess.check_output([_get_exiftool_path(), '-json', f])
        if re.search('^[a-z0-9/]', self.filename) is None:
            out = self.__handle_problematic_filename(self.filename, fun)
        else:
            out = fun(self.filename)
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

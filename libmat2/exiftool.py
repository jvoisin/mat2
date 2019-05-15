import functools
import json
import logging
import os
from typing import Dict, Union, Set

from . import abstract
from . import subprocess

# Make pyflakes happy
assert Set


class ExiftoolParser(abstract.AbstractParser):
    """ Exiftool is often the easiest way to get all the metadata
    from a import file, hence why several parsers are re-using its `get_meta`
    method.
    """
    meta_allowlist = set()  # type: Set[str]

    def get_meta(self) -> Dict[str, Union[str, dict]]:
        out = subprocess.run([_get_exiftool_path(), '-json', self.filename],
                             input_filename=self.filename,
                             check=True, stdout=subprocess.PIPE).stdout
        meta = json.loads(out.decode('utf-8'))[0]
        for key in self.meta_allowlist:
            meta.pop(key, None)
        return meta

    def _lightweight_cleanup(self) -> bool:
        if os.path.exists(self.output_filename):
            try:
                # exiftool can't force output to existing files
                os.remove(self.output_filename)
            except OSError as e:  # pragma: no cover
                logging.error("The output file %s is already existing and \
                               can't be overwritten: %s.", self.filename, e)
                return False

        # Note: '-All=' must be followed by a known exiftool option.
        # Also, '-CommonIFD0' is needed for .tiff files
        cmd = [_get_exiftool_path(),
               '-all=',         # remove metadata
               '-adobe=',       # remove adobe-specific metadata
               '-exif:all=',    # remove all exif metadata
               '-Time:All=',    # remove all timestamps
               '-quiet',        # don't show useless logs
               '-CommonIFD0=',  # remove IFD0 metadata
               '-o', self.output_filename,
               self.filename]
        try:
            subprocess.run(cmd, check=True,
                           input_filename=self.filename,
                           output_filename=self.output_filename)
        except subprocess.CalledProcessError as e:  # pragma: no cover
            logging.error("Something went wrong during the processing of %s: %s", self.filename, e)
            return False
        return True

@functools.lru_cache()
def _get_exiftool_path() -> str:  # pragma: no cover
    possible_pathes = {
        '/usr/bin/exiftool',              # debian/fedora
        '/usr/bin/vendor_perl/exiftool',  # archlinux
    }

    for possible_path in possible_pathes:
        if os.path.isfile(possible_path):
            if os.access(possible_path, os.X_OK):
                return possible_path

    raise RuntimeError("Unable to find exiftool")

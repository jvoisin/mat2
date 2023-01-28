import functools
import json
import logging
import os
import shutil
import subprocess
from typing import Union, Set, Dict

from . import abstract
from . import bubblewrap


class ExiftoolParser(abstract.AbstractParser):
    """ Exiftool is often the easiest way to get all the metadata
    from a import file, hence why several parsers are re-using its `get_meta`
    method.
    """
    meta_allowlist = set()  # type: Set[str]

    def get_meta(self) -> Dict[str, Union[str, Dict]]:
        try:
            if self.sandbox:
                out = bubblewrap.run([_get_exiftool_path(), '-json',
                                      self.filename],
                                     input_filename=self.filename,
                                     check=True, stdout=subprocess.PIPE).stdout
            else:
                out = subprocess.run([_get_exiftool_path(), '-json',
                                      self.filename],
                                     check=True, stdout=subprocess.PIPE).stdout
        except subprocess.CalledProcessError:  # pragma: no cover
            raise ValueError
        meta = json.loads(out.decode('utf-8'))[0]
        for key in self.meta_allowlist:
            meta.pop(key, None)
        return meta

    def _lightweight_cleanup(self) -> bool:
        if os.path.exists(self.output_filename):
            try:  # exiftool can't force output to existing files
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
            if self.sandbox:
                bubblewrap.run(cmd, check=True,
                               input_filename=self.filename,
                               output_filename=self.output_filename)
            else:
                subprocess.run(cmd, check=True)
        except subprocess.CalledProcessError as e:  # pragma: no cover
            logging.error("Something went wrong during the processing of %s: %s", self.filename, e)
            return False
        return True

@functools.lru_cache
def _get_exiftool_path() -> str:  # pragma: no cover
    which_path = shutil.which('exiftool')
    if which_path:
        return which_path

    # Exiftool on Arch Linux has a weird path
    if os.access('/usr/bin/vendor_perl/exiftool', os.X_OK):
        return '/usr/bin/vendor_perl/exiftool'

    raise RuntimeError("Unable to find exiftool")

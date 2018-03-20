import subprocess
import json

import cairo

from . import abstract

class PNGParser(abstract.AbstractParser):
    mimetypes = {'image/png', }
    meta_list = set()

    def get_meta(self):
        out = subprocess.check_output(['exiftool', '-json', self.filename])
        return json.loads(out)[0]

    def remove_all(self):
        surface = cairo.ImageSurface.create_from_png(self.filename)
        surface.write_to_png(self.output_filename)

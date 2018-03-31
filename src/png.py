import subprocess
import json

import cairo

from . import abstract

class PNGParser(abstract.AbstractParser):
    mimetypes = {'image/png', }
    meta_whitelist = {'SourceFile', 'ExifToolVersion', 'FileName',
            'Directory', 'FileSize', 'FileModifyDate', 'FileAccessDate',
            "FileInodeChangeDate", 'FilePermissions', 'FileType',
            'FileTypeExtension', 'MIMEType', 'ImageWidth', 'BitDepth', 'ColorType',
            'Compression', 'Filter', 'Interlace', 'BackgroundColor', 'ImageSize',
            'Megapixels', 'ImageHeight'}

    def get_meta(self):
        out = subprocess.check_output(['exiftool', '-json', self.filename])
        meta = json.loads(out.decode('utf-8'))[0]
        for key in self.meta_whitelist:
            meta.pop(key, None)
        return meta

    def remove_all(self):
        surface = cairo.ImageSurface.create_from_png(self.filename)
        surface.write_to_png(self.output_filename)
        return True

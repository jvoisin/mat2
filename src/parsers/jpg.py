import subprocess
import json

import gi
gi.require_version('GdkPixbuf', '2.0')
from gi.repository import GdkPixbuf

from . import abstract

class JPGParser(abstract.AbstractParser):
    mimetypes = {'image/jpg', }
    meta_whitelist = {'SourceFile', 'ExifToolVersion', 'FileName',
            'Directory', 'FileSize', 'FileModifyDate', 'FileAccessDate',
            "FileInodeChangeDate", 'FilePermissions', 'FileType',
            'FileTypeExtension', 'MIMEType', 'ImageWidth',
            'ImageSize', 'BitsPerSample', 'ColorComponents', 'EncodingProcess',
            'JFIFVersion', 'ResolutionUnit', 'XResolution', 'YCbCrSubSampling',
            'YResolution', 'Megapixels', 'ImageHeight'}

    def get_meta(self):
        out = subprocess.check_output(['exiftool', '-json', self.filename])
        meta = json.loads(out)[0]
        for key in self.meta_whitelist:
            meta.pop(key, None)
        return meta

    def remove_all(self):
        pixbuf = GdkPixbuf.Pixbuf.new_from_file(self.filename)
        pixbuf.savev(self.output_filename, "jpeg", ["quality"], ["100"])
        return True

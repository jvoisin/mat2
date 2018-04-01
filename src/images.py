import subprocess
import json
import os

import cairo

import gi
gi.require_version('GdkPixbuf', '2.0')
from gi.repository import GdkPixbuf

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

class GdkPixbufAbstractParser(abstract.AbstractParser):
    def get_meta(self):
        out = subprocess.check_output(['exiftool', '-json', self.filename])
        meta = json.loads(out.decode('utf-8'))[0]
        for key in self.meta_whitelist:
            meta.pop(key, None)
        return meta

    def remove_all(self):
        _, extension = os.path.splitext(self.filename)
        pixbuf = GdkPixbuf.Pixbuf.new_from_file(self.filename)
        if extension == '.jpg':
            extension = '.jpeg'
        pixbuf.savev(self.output_filename, extension[1:], ["quality"], ["100"])
        return True


class JPGParser(GdkPixbufAbstractParser):
    mimetypes = {'image/jpg'}
    meta_whitelist = {'SourceFile', 'ExifToolVersion', 'FileName',
            'Directory', 'FileSize', 'FileModifyDate', 'FileAccessDate',
            "FileInodeChangeDate", 'FilePermissions', 'FileType',
            'FileTypeExtension', 'MIMEType', 'ImageWidth',
            'ImageSize', 'BitsPerSample', 'ColorComponents', 'EncodingProcess',
            'JFIFVersion', 'ResolutionUnit', 'XResolution', 'YCbCrSubSampling',
            'YResolution', 'Megapixels', 'ImageHeight'}


class TiffParser(GdkPixbufAbstractParser):
    mimetypes = {'image/tiff'}
    meta_whitelist = {'Compression', 'ExifByteOrder', 'ExtraSamples',
            'FillOrder', 'PhotometricInterpretation', 'PlanarConfiguration',
            'RowsPerStrip', 'SamplesPerPixel', 'StripByteCounts',
            'StripOffsets', 'BitsPerSample', 'Directory', 'ExifToolVersion',
            'FileAccessDate', 'FileInodeChangeDate', 'FileModifyDate',
            'FileName', 'FilePermissions', 'FileSize', 'FileType',
            'FileTypeExtension', 'ImageHeight', 'ImageSize', 'ImageWidth',
            'MIMEType', 'Megapixels', 'SourceFile'}


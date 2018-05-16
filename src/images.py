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
                      'Directory', 'FileSize', 'FileModifyDate',
                      'FileAccessDate', 'FileInodeChangeDate',
                      'FilePermissions', 'FileType', 'FileTypeExtension',
                      'MIMEType', 'ImageWidth', 'BitDepth', 'ColorType',
                      'Compression', 'Filter', 'Interlace', 'BackgroundColor',
                      'ImageSize', 'Megapixels', 'ImageHeight'}

    def __init__(self, filename):
        super().__init__(filename)
        try:  # better fail here than later
            cairo.ImageSurface.create_from_png(self.filename)
        except MemoryError:
            raise ValueError

    def get_meta(self):
        out = subprocess.check_output(['/usr/bin/exiftool', '-json', self.filename])
        meta = json.loads(out.decode('utf-8'))[0]
        for key in self.meta_whitelist:
            meta.pop(key, None)
        return meta

    def remove_all(self):
        surface = cairo.ImageSurface.create_from_png(self.filename)
        surface.write_to_png(self.output_filename)
        return True


class GdkPixbufAbstractParser(abstract.AbstractParser):
    """ GdkPixbuf can handle a lot of surfaces, so we're rending images on it,
        this has the side-effect of removing metadata completely.
    """
    def get_meta(self):
        out = subprocess.check_output(['/usr/bin/exiftool', '-json', self.filename])
        meta = json.loads(out.decode('utf-8'))[0]
        for key in self.meta_whitelist:
            meta.pop(key, None)
        return meta

    def remove_all(self):
        _, extension = os.path.splitext(self.filename)
        pixbuf = GdkPixbuf.Pixbuf.new_from_file(self.filename)
        if extension == '.jpg':
            extension = '.jpeg'
        pixbuf.savev(self.output_filename, extension[1:], [], [])
        return True


class JPGParser(GdkPixbufAbstractParser):
    mimetypes = {'image/jpeg'}
    meta_whitelist = {'SourceFile', 'ExifToolVersion', 'FileName',
                      'Directory', 'FileSize', 'FileModifyDate',
                      'FileAccessDate', "FileInodeChangeDate",
                      'FilePermissions', 'FileType', 'FileTypeExtension',
                      'MIMEType', 'ImageWidth', 'ImageSize', 'BitsPerSample',
                      'ColorComponents', 'EncodingProcess', 'JFIFVersion',
                      'ResolutionUnit', 'XResolution', 'YCbCrSubSampling',
                      'YResolution', 'Megapixels', 'ImageHeight'}


class TiffParser(GdkPixbufAbstractParser):
    mimetypes = {'image/tiff'}
    meta_whitelist = {'Compression', 'ExifByteOrder', 'ExtraSamples',
                      'FillOrder', 'PhotometricInterpretation',
                      'PlanarConfiguration', 'RowsPerStrip', 'SamplesPerPixel',
                      'StripByteCounts', 'StripOffsets', 'BitsPerSample',
                      'Directory', 'ExifToolVersion', 'FileAccessDate',
                      'FileInodeChangeDate', 'FileModifyDate', 'FileName',
                      'FilePermissions', 'FileSize', 'FileType',
                      'FileTypeExtension', 'ImageHeight', 'ImageSize',
                      'ImageWidth', 'MIMEType', 'Megapixels', 'SourceFile'}


class BMPParser(GdkPixbufAbstractParser):
    mimetypes = {'image/x-ms-bmp'}
    meta_whitelist = {'SourceFile', 'ExifToolVersion', 'FileName', 'Directory',
                      'FileSize', 'FileModifyDate', 'FileAccessDate',
                      'FileInodeChangeDate', 'FilePermissions', 'FileType',
                      'FileTypeExtension', 'MIMEType', 'BMPVersion',
                      'ImageWidth', 'ImageHeight', 'Planes', 'BitDepth',
                      'Compression', 'ImageLength', 'PixelsPerMeterX',
                      'PixelsPerMeterY', 'NumColors', 'NumImportantColors',
                      'RedMask', 'GreenMask', 'BlueMask', 'AlphaMask',
                      'ColorSpace', 'RedEndpoint', 'GreenEndpoint',
                      'BlueEndpoint', 'GammaRed', 'GammaGreen', 'GammaBlue',
                      'ImageSize', 'Megapixels'}

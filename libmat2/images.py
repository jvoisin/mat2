import subprocess
import imghdr
import json
import os
import shutil
import tempfile
import re

import cairo

import gi
gi.require_version('GdkPixbuf', '2.0')
from gi.repository import GdkPixbuf

from . import abstract


class _ImageParser(abstract.AbstractParser):
    @staticmethod
    def __handle_problematic_filename(filename: str, callback) -> str:
        """ This method takes a filename with a problematic name,
        and safely applies it a `callback`."""
        tmpdirname = tempfile.mkdtemp()
        fname = os.path.join(tmpdirname, "temp_file")
        shutil.copy(filename, fname)
        out = callback(fname)
        shutil.rmtree(tmpdirname)
        return out

    def get_meta(self):
        """ There is no way to escape the leading(s) dash(es) of the current
        self.filename to prevent parameter injections, so we need to take care
        of this.
        """
        fun = lambda f: subprocess.check_output(['/usr/bin/exiftool', '-json', f])
        if re.search('^[a-z0-9/]', self.filename) is None:
            out = self.__handle_problematic_filename(self.filename, fun)
        else:
            out = fun(self.filename)
        meta = json.loads(out.decode('utf-8'))[0]
        for key in self.meta_whitelist:
            meta.pop(key, None)
        return meta

class PNGParser(_ImageParser):
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

    def remove_all(self):
        surface = cairo.ImageSurface.create_from_png(self.filename)
        surface.write_to_png(self.output_filename)
        return True


class GdkPixbufAbstractParser(_ImageParser):
    """ GdkPixbuf can handle a lot of surfaces, so we're rending images on it,
        this has the side-effect of removing metadata completely.
    """
    _type = ''

    def remove_all(self):
        _, extension = os.path.splitext(self.filename)
        pixbuf = GdkPixbuf.Pixbuf.new_from_file(self.filename)
        if extension == '.jpg':
            extension = '.jpeg'  # gdk is picky
        pixbuf.savev(self.output_filename, extension[1:], [], [])
        return True

    def __init__(self, filename):
        super().__init__(filename)
        if imghdr.what(filename) != self._type:  # better safe than sorry
            raise ValueError


class JPGParser(GdkPixbufAbstractParser):
    _type = 'jpeg'
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
    _type = 'tiff'
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
    _type = 'bmp'
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

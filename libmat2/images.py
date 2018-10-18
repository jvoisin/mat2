import imghdr
import os
from typing import Set

import cairo

import gi
gi.require_version('GdkPixbuf', '2.0')
from gi.repository import GdkPixbuf

from . import exiftool

# Make pyflakes happy
assert Set

class PNGParser(exiftool.ExiftoolParser):
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

        if imghdr.what(filename) != 'png':
            raise ValueError

        try:  # better fail here than later
            cairo.ImageSurface.create_from_png(self.filename)
        except MemoryError:  # pragma: no cover
            raise ValueError

    def remove_all(self) -> bool:
        surface = cairo.ImageSurface.create_from_png(self.filename)
        surface.write_to_png(self.output_filename)
        return True


class GdkPixbufAbstractParser(exiftool.ExiftoolParser):
    """ GdkPixbuf can handle a lot of surfaces, so we're rending images on it,
        this has the side-effect of completely removing metadata.
    """
    _type = ''

    def __init__(self, filename):
        super().__init__(filename)
        if imghdr.what(filename) != self._type:  # better safe than sorry
            raise ValueError

    def remove_all(self) -> bool:
        _, extension = os.path.splitext(self.filename)
        pixbuf = GdkPixbuf.Pixbuf.new_from_file(self.filename)
        if extension.lower() == '.jpg':
            extension = '.jpeg'  # gdk is picky
        pixbuf.savev(self.output_filename, extension[1:], [], [])
        return True


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

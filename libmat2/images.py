import imghdr
import os
from typing import Set

import cairo

import gi
gi.require_version('GdkPixbuf', '2.0')
from gi.repository import GdkPixbuf, GLib

from . import exiftool

# Make pyflakes happy
assert Set

class PNGParser(exiftool.ExiftoolParser):
    mimetypes = {'image/png', }
    meta_allowlist = {'SourceFile', 'ExifToolVersion', 'FileName',
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
        if self.lightweight_cleaning:
            return self._lightweight_cleanup()
        surface = cairo.ImageSurface.create_from_png(self.filename)
        surface.write_to_png(self.output_filename)
        return True


class GIFParser(exiftool.ExiftoolParser):
    mimetypes = {'image/gif'}
    meta_allowlist = {'AnimationIterations', 'BackgroundColor', 'BitsPerPixel',
                      'ColorResolutionDepth', 'Directory', 'Duration',
                      'ExifToolVersion', 'FileAccessDate',
                      'FileInodeChangeDate', 'FileModifyDate', 'FileName',
                      'FilePermissions', 'FileSize', 'FileType',
                      'FileTypeExtension', 'FrameCount', 'GIFVersion',
                      'HasColorMap', 'ImageHeight', 'ImageSize', 'ImageWidth',
                      'MIMEType', 'Megapixels', 'SourceFile',}

    def remove_all(self) -> bool:
        return self._lightweight_cleanup()


class GdkPixbufAbstractParser(exiftool.ExiftoolParser):
    """ GdkPixbuf can handle a lot of surfaces, so we're rending images on it,
        this has the side-effect of completely removing metadata.
    """
    _type = ''

    def __init__(self, filename):
        super().__init__(filename)
        # we can't use imghdr here because of https://bugs.python.org/issue28591
        try:
            GdkPixbuf.Pixbuf.new_from_file(self.filename)
        except GLib.GError:
            raise ValueError

    def remove_all(self) -> bool:
        if self.lightweight_cleaning:
            return self._lightweight_cleanup()

        _, extension = os.path.splitext(self.filename)
        pixbuf = GdkPixbuf.Pixbuf.new_from_file(self.filename)
        if extension.lower() == '.jpg':
            extension = '.jpeg'  # gdk is picky
        pixbuf.savev(self.output_filename, type=extension[1:], option_keys=[], option_values=[])
        return True


class JPGParser(GdkPixbufAbstractParser):
    _type = 'jpeg'
    mimetypes = {'image/jpeg'}
    meta_allowlist = {'SourceFile', 'ExifToolVersion', 'FileName',
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
    meta_allowlist = {'Compression', 'ExifByteOrder', 'ExtraSamples',
                      'FillOrder', 'PhotometricInterpretation',
                      'PlanarConfiguration', 'RowsPerStrip', 'SamplesPerPixel',
                      'StripByteCounts', 'StripOffsets', 'BitsPerSample',
                      'Directory', 'ExifToolVersion', 'FileAccessDate',
                      'FileInodeChangeDate', 'FileModifyDate', 'FileName',
                      'FilePermissions', 'FileSize', 'FileType',
                      'FileTypeExtension', 'ImageHeight', 'ImageSize',
                      'ImageWidth', 'MIMEType', 'Megapixels', 'SourceFile'}

import os
import re
from typing import Union, Any, Dict

import cairo

import gi
gi.require_version('GdkPixbuf', '2.0')
gi.require_version('Rsvg', '2.0')
from gi.repository import GdkPixbuf, GLib, Rsvg

from . import exiftool, abstract

# Make pyflakes happy
assert Any

class SVGParser(exiftool.ExiftoolParser):
    mimetypes = {'image/svg+xml', }
    meta_allowlist = {'Directory', 'ExifToolVersion', 'FileAccessDate',
                      'FileInodeChangeDate', 'FileModifyDate', 'FileName',
                      'FilePermissions', 'FileSize', 'FileType',
                      'FileTypeExtension', 'ImageHeight', 'ImageWidth',
                      'MIMEType', 'SVGVersion', 'SourceFile', 'ViewBox'
                      }

    def remove_all(self) -> bool:
        try:
            svg = Rsvg.Handle.new_from_file(self.filename)
        except GLib.GError:
            raise ValueError

        try:
            _, _, _, _, has_viewbox, viewbox = svg.get_intrinsic_dimensions()
            if has_viewbox is False:
                raise ValueError
            _, width, height = svg.get_intrinsic_size_in_pixels()
        except AttributeError:
            dimensions = svg.get_dimensions()
            height, width = dimensions.height, dimensions.width

        surface = cairo.SVGSurface(self.output_filename, height, width)
        context = cairo.Context(surface)
        try:
            svg.render_document(context, viewbox)
        except AttributeError:
            svg.render_cairo(context)

        surface.finish()
        return True

    def get_meta(self) -> Dict[str, Union[str, Dict]]:
        meta = super().get_meta()

        # The namespace is mandatory, but only the …/2000/svg is valid.
        ns = 'http://www.w3.org/2000/svg'
        if meta.get('Xmlns') == ns:
            meta.pop('Xmlns')
        return meta


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

        try:  # better fail here than later
            cairo.ImageSurface.create_from_png(self.filename)
        except:  # pragma: no cover
            # Cairo is returning some weird exceptions :/
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
        elif extension.lower() == '.tif':
            extension = '.tiff'  # gdk is picky
        try:
            pixbuf.savev(self.output_filename, type=extension[1:],
                         option_keys=[], option_values=[])
        except GLib.GError:  # pragma: no cover
            return False
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


class PPMParser(abstract.AbstractParser):
    mimetypes = {'image/x-portable-pixmap'}

    def get_meta(self) -> Dict[str, Union[str, Dict]]:
        meta = {}  # type: Dict[str, Union[str, Dict[Any, Any]]]
        with open(self.filename) as f:
            for idx, line in enumerate(f):
                if line.lstrip().startswith('#'):
                    meta[str(idx)] = line.lstrip().rstrip()
        return meta

    def remove_all(self) -> bool:
        with open(self.filename) as fin:
            with open(self.output_filename, 'w') as fout:
                for line in fin:
                    if not line.lstrip().startswith('#'):
                        line = re.sub(r"\s+", "", line, flags=re.UNICODE)
                        fout.write(line)
        return True


class HEICParser(exiftool.ExiftoolParser):
    mimetypes = {'image/heic'}
    meta_allowlist = {'SourceFile', 'ExifToolVersion', 'FileName', 'Directory',
            'FileSize', 'FileModifyDate', 'FileAccessDate',
            'FileInodeChangeDate', 'FilePermissions', 'FileType',
            'FileTypeExtension', 'MIMEType', 'MajorBrand', 'MinorVersion',
            'CompatibleBrands','HandlerType', 'PrimaryItemReference',
            'HEVCConfigurationVersion', 'GeneralProfileSpace',
            'GeneralTierFlag', 'GeneralProfileIDC',
            'GenProfileCompatibilityFlags', 'ConstraintIndicatorFlags',
            'GeneralLevelIDC', 'MinSpatialSegmentationIDC',
            'ParallelismType','ChromaFormat', 'BitDepthLuma', 'BitDepthChroma',
            'NumTemporalLayers', 'TemporalIDNested', 'ImageWidth',
            'ImageHeight', 'ImageSpatialExtent', 'ImagePixelDepth',
            'AverageFrameRate', 'ConstantFrameRate', 'MediaDataSize',
            'MediaDataOffset','ImageSize', 'Megapixels'}

    def remove_all(self) -> bool:
        return self._lightweight_cleanup()

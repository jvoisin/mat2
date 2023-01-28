""" Handle PDF

"""

import os
import re
import logging
import tempfile
import io
from typing import Union, Dict

import cairo
import gi
gi.require_version('Poppler', '0.18')
from gi.repository import Poppler, GLib

from . import abstract

FIXED_PDF_VERSION = cairo.PDFVersion.VERSION_1_5


class PDFParser(abstract.AbstractParser):
    mimetypes = {'application/pdf', }
    meta_list = {'author', 'creation-date', 'creator', 'format', 'keywords',
                 'metadata', 'mod-date', 'producer', 'subject', 'title',
                 'viewer-preferences'}

    def __init__(self, filename):
        super().__init__(filename)
        self.uri = 'file://' + os.path.abspath(self.filename)
        self.__scale = 200 / 72.0  # how much precision do we want for the render
        try:  # Check now that the file is valid, to avoid surprises later
            Poppler.Document.new_from_file(self.uri, None)
        except GLib.GError:  # Invalid PDF
            raise ValueError

    def remove_all(self) -> bool:
        if self.lightweight_cleaning is True:
            return self.__remove_all_lightweight()
        return self.__remove_all_thorough()

    def __remove_all_lightweight(self) -> bool:
        """
            Load the document into Poppler, render pages on a new PDFSurface.
        """
        document = Poppler.Document.new_from_file(self.uri, None)
        pages_count = document.get_n_pages()

        tmp_path = tempfile.mkstemp()[1]
        pdf_surface = cairo.PDFSurface(tmp_path, 10, 10)  # resized later anyway
        pdf_surface.restrict_to_version(FIXED_PDF_VERSION)
        pdf_context = cairo.Context(pdf_surface)  # context draws on the surface

        for pagenum in range(pages_count):
            logging.info("Rendering page %d/%d", pagenum + 1, pages_count)
            page = document.get_page(pagenum)
            page_width, page_height = page.get_size()
            pdf_surface.set_size(page_width, page_height)
            pdf_context.save()
            page.render_for_printing(pdf_context)
            pdf_context.restore()
            pdf_context.show_page()  # draw pdf_context on pdf_surface
        pdf_surface.finish()

        self.__remove_superficial_meta(tmp_path, self.output_filename)
        os.remove(tmp_path)

        return True

    def __remove_all_thorough(self) -> bool:
        """
            Load the document into Poppler, render pages on PNG,
            and shove those PNG into a new PDF.
        """
        document = Poppler.Document.new_from_file(self.uri, None)
        pages_count = document.get_n_pages()

        _, tmp_path = tempfile.mkstemp()
        pdf_surface = cairo.PDFSurface(tmp_path, 32, 32)  # resized later anyway
        pdf_surface.restrict_to_version(FIXED_PDF_VERSION)
        pdf_context = cairo.Context(pdf_surface)

        for pagenum in range(pages_count):
            page = document.get_page(pagenum)
            if page is None:  # pragma: no cover
                logging.error("Unable to get PDF pages")
                return False
            page_width, page_height = page.get_size()
            logging.info("Rendering page %d/%d", pagenum + 1, pages_count)

            width = int(page_width * self.__scale)
            height = int(page_height * self.__scale)
            img_surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, width, height)
            img_context = cairo.Context(img_surface)

            img_context.scale(self.__scale, self.__scale)
            page.render_for_printing(img_context)
            img_context.show_page()

            buf = io.BytesIO()
            img_surface.write_to_png(buf)
            img_surface.finish()
            buf.seek(0)

            img = cairo.ImageSurface.create_from_png(buf)
            if cairo.version_info < (1, 12, 0):
                pdf_surface.set_size(width, height)
            else:
                pdf_surface.set_size(page_width, page_height)
                pdf_surface.set_device_scale(1 / self.__scale, 1 / self.__scale)
            pdf_context.set_source_surface(img, 0, 0)
            pdf_context.paint()
            pdf_context.show_page()  # draw pdf_context on pdf_surface

        pdf_surface.finish()

        # Removes metadata added by Poppler
        self.__remove_superficial_meta(tmp_path, self.output_filename)
        os.remove(tmp_path)

        return True

    @staticmethod
    def __remove_superficial_meta(in_file: str, out_file: str) -> bool:
        document = Poppler.Document.new_from_file('file://' + in_file)
        document.set_producer('')
        document.set_creator('')
        document.set_creation_date(-1)
        document.save('file://' + os.path.abspath(out_file))

        # Cairo adds "/Producer" and "/CreationDate", and Poppler sometimes
        # fails to remove them, we have to use this terrible regex.
        # It should(tm) be alright though, because cairo's output format
        # for metadata is fixed.
        with open(out_file, 'rb') as f:
            out = re.sub(rb'<<[\s\n]*/Producer.*?>>', b' << >>', f.read(), 0,
                         re.DOTALL | re.IGNORECASE)
        with open(out_file, 'wb') as f:
            f.write(out)

        return True

    @staticmethod
    def __parse_metadata_field(data: str) -> Dict[str, str]:
        metadata = {}
        for (_, key, value) in re.findall(r"<(xmp|pdfx|pdf|xmpMM):(.+)>(.+)</\1:\2>", data, re.I):
            metadata[key] = value
        return metadata

    def get_meta(self) -> Dict[str, Union[str, Dict]]:
        """ Return a dict with all the meta of the file
        """
        metadata = {}
        document = Poppler.Document.new_from_file(self.uri, None)

        for key in self.meta_list:
            if document.get_property(key):
                metadata[key] = document.get_property(key)
        if 'metadata' in metadata:
            parsed_meta = self.__parse_metadata_field(metadata['metadata'])
            for key, value in parsed_meta.items():
                metadata[key] = value
        return metadata

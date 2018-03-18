""" Handle PDF

"""

import os
import logging
import tempfile
import shutil
import io

import cairo
import gi
gi.require_version('Poppler', '0.18')
from gi.repository import Poppler, Gio, GLib

try:
    from PIL import Image
except ImportError:
    Image = None

from . import abstract

logging.basicConfig(level=logging.DEBUG)


class PDFParser(abstract.AbstractParser):
    def __init__(self, filename):
        super().__init__(filename)
        self.meta_list = {'title', 'author', 'subject',
            'keywords', 'creator', 'producer', 'metadata'}
        self.uri = 'file://' + os.path.abspath(self.filename)
        self.password = None

    def remove_all(self):
        """
            Load the document into Poppler, render pages on PNG,
            and shove those PNG into a new PDF. Metadata from the new
            PDF are removed via Poppler, because there is no way to tell
            cairo to not add "created by cairo" during rendering.

            TODO: Improve the resolution
            TODO: Don't use a temp file
        """
        document = Poppler.Document.new_from_file(self.uri, self.password)

        pdf_out = io.BytesIO()
        pdf_surface = cairo.PDFSurface(pdf_out, 128, 128)
        pdf_context = cairo.Context(pdf_surface)

        for pagenum in range(document.get_n_pages()):
            page = document.get_page(pagenum)
            page_width, page_height = page.get_size()
            logging.info("Rendering page %d/%d", pagenum + 1, document.get_n_pages())

            img_surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, int(page_width)*2, int(page_height)*2)
            img_context = cairo.Context(img_surface)

            img_context.scale(2, 2)
            page.render_for_printing_with_options(img_context, Poppler.PrintFlags.DOCUMENT)
            img_context.show_page()

            buf = io.BytesIO()
            img_surface.write_to_png(buf)
            img_surface.finish()
            buf.seek(0)

            img = cairo.ImageSurface.create_from_png(buf)
            pdf_surface.set_size(page_width*2, page_height*2)
            pdf_context.set_source_surface(img, 0, 0)
            pdf_context.paint()
            pdf_context.show_page()

        pdf_surface.finish()

        b = GLib.Bytes(pdf_out.getvalue())
        input_stream = Gio.MemoryInputStream.new_from_bytes(b)
        out_document = Poppler.Document.new_from_stream(input_stream, -1, self.password, None)
        metadata = {}
        for key in self.meta_list:
            if out_document.get_property(key):
                metadata[key] = str(out_document.get_property(key))
        out_document.set_producer('totally not MAT2 ;)')
        out_document.set_creator('')
        print("AFTER")
        metadata = {}
        for key in self.meta_list:
            if out_document.get_property(key):
                metadata[key] = str(out_document.get_property(key))
        print("LOL")
        out_document.save('file://' + os.path.abspath("olol.pdf"))

        print(metadata)

        return True

    def get_meta(self):
        """ Return a dict with all the meta of the file
        """
        print("URI: %s", self.uri)
        document = Poppler.Document.new_from_file(self.uri, self.password)
        metadata = {}
        for key in self.meta_list:
            if document.get_property(key):
                metadata[key] = str(document.get_property(key))
        return metadata

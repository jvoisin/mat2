#!/usr/bin/env python3

# pylint: disable=unused-argument,len-as-condition,arguments-differ

"""
Because writing GUI is non-trivial (cf. https://0xacab.org/jvoisin/mat2/issues/3),
we decided to write a Nautilus extensions instead
(cf. https://0xacab.org/jvoisin/mat2/issues/2).

The code is a little bit convoluted because Gtk isn't thread-safe,
so we're not allowed to call anything Gtk-related outside of the main
thread, so we'll have to resort to using a `queue` to pass "messages" around.
"""

import os
import queue
import threading
from urllib.parse import unquote

import gi
gi.require_version('Nautilus', '3.0')
gi.require_version('Gtk', '3.0')
from gi.repository import Nautilus, GObject, Gtk, Gio, GLib

from libmat2 import parser_factory

def _remove_metadata(fpath):
    """ This is a simple wrapper around libmat2, because it's
    easier and cleaner this way.
    """
    parser, mtype = parser_factory.get_parser(fpath)
    if parser is None:
        return False, mtype
    return parser.remove_all(), mtype

class ColumnExtension(GObject.GObject, Nautilus.MenuProvider, Nautilus.LocationWidgetProvider):
    """ This class adds an item to the right-clic menu in Nautilus. """
    def __init__(self):
        super().__init__()
        self.infobar_hbox = None
        self.infobar = None
        self.failed_items = list()

    def __infobar_failure(self):
        """ Add an hbox to the `infobar` warning about the fact that we didn't
        manage to remove the metadata from every single file.
        """
        self.infobar.set_show_close_button(True)
        self.infobar_hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)

        btn = Gtk.Button("Show")
        btn.connect("clicked", self.__cb_show_failed)
        self.infobar_hbox.pack_end(btn, False, False, 0)

        infobar_msg = Gtk.Label("Failed to clean some items")
        self.infobar_hbox.pack_start(infobar_msg, False, False, 0)

        self.infobar.get_content_area().pack_start(self.infobar_hbox, True, True, 0)
        self.infobar.show_all()

    def get_widget(self, uri, window):
        """ This is the method that we have to implement (because we're
        a LocationWidgetProvider) in order to show our infobar.
        """
        self.infobar = Gtk.InfoBar()
        self.infobar.set_message_type(Gtk.MessageType.ERROR)
        self.infobar.connect("response", self.__cb_infobar_response)

        return self.infobar

    def __cb_infobar_response(self, infobar, response):
        """ Callback for the infobar close button.
        """
        if response == Gtk.ResponseType.CLOSE:
            self.infobar_hbox.destroy()
            self.infobar.hide()

    def __cb_show_failed(self, button):
        """ Callback to show a popup containing a list of files
        that we didn't manage to clean.
        """

        # FIXME this should be done only once the window is destroyed
        self.infobar_hbox.destroy()
        self.infobar.hide()

        window = Gtk.Window()
        headerbar = Gtk.HeaderBar()
        window.set_titlebar(headerbar)
        headerbar.props.title = "Metadata removal failed"

        exit_buton = Gtk.Button("Exit")
        exit_buton.connect("clicked", lambda _: window.close())
        headerbar.pack_end(exit_buton)

        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        window.add(box)

        listbox = Gtk.ListBox()
        listbox.set_selection_mode(Gtk.SelectionMode.NONE)
        box.pack_start(listbox, True, True, 0)

        for fname, mtype in self.failed_items:
            row = Gtk.ListBoxRow()
            hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
            row.add(hbox)

            icon = Gio.content_type_get_icon('text/plain' if not mtype else mtype)
            select_image = Gtk.Image.new_from_gicon(icon, Gtk.IconSize.BUTTON)
            hbox.pack_start(select_image, False, False, 0)

            label = Gtk.Label(os.path.basename(fname))
            hbox.pack_start(label, True, False, 0)

            listbox.add(row)

        listbox.show_all()
        window.show_all()


    @staticmethod
    def __validate(fileinfo):
        """ Validate if a given file FileInfo `fileinfo` can be processed."""
        if fileinfo.get_uri_scheme() != "file" or fileinfo.is_directory():
            return False
        elif not fileinfo.can_write():
            return False
        return True

    def __create_progressbar(self):
        """ Create the progressbar used to notify that files are currently
        being processed.
        """
        self.infobar.set_show_close_button(False)
        self.infobar.set_message_type(Gtk.MessageType.INFO)
        self.infobar_hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)

        progressbar = Gtk.ProgressBar()
        self.infobar_hbox.pack_start(progressbar, True, True, 0)
        progressbar.set_show_text(True)

        self.infobar.get_content_area().pack_start(self.infobar_hbox, True, True, 0)
        self.infobar.show_all()

        return progressbar

    def __update_progressbar(self, processing_queue, progressbar):
        """ This method is run via `Glib.add_idle` to update the progressbar."""
        try:
            fname = processing_queue.get(block=False)
        except queue.Empty:
            return True

        # `None` is the marker put in the queue to signal that every selected
        # file was processed.
        if fname is None:
            self.infobar_hbox.destroy()
            self.infobar.hide()
            if len(self.failed_items):
                self.__infobar_failure()
            if not processing_queue.empty():
                print("Something went wrong, the queue isn't empty :/")
            return False

        progressbar.pulse()
        progressbar.set_text("Cleaning %s" % fname)
        progressbar.show_all()
        self.infobar_hbox.show_all()
        self.infobar.show_all()
        return True

    def __clean_files(self, files, processing_queue):
        """ This method is threaded in order to avoid blocking the GUI
        while cleaning up the files.
        """
        for fileinfo in files:
            fname = fileinfo.get_name()
            processing_queue.put(fname)

            if not self.__validate(fileinfo):
                self.failed_items.append((fname, None))
                continue

            fpath = unquote(fileinfo.get_uri()[7:])  # `len('file://') = 7`
            success, mtype = _remove_metadata(fpath)
            if not success:
                self.failed_items.append((fname, mtype))
        processing_queue.put(None)  # signal that we processed all the files
        return True


    def __cb_menu_activate(self, menu, files):
        """ This method is called when the user clicked the "clean metadata"
        menu item.
        """
        self.failed_items = list()
        progressbar = self.__create_progressbar()
        progressbar.set_pulse_step = 1.0 / len(files)
        self.infobar.show_all()

        processing_queue = queue.Queue()
        GLib.idle_add(self.__update_progressbar, processing_queue, progressbar)

        thread = threading.Thread(target=self.__clean_files, args=(files, processing_queue))
        thread.daemon = True
        thread.start()


    def get_background_items(self, window, file):
        """ https://bugzilla.gnome.org/show_bug.cgi?id=784278 """
        return None

    def get_file_items(self, window, files):
        """ This method is the one allowing us to create a menu item.
        """
        # Do not show the menu item if not a single file has a chance to be
        # processed by mat2.
        if not any(map(self.__validate, files)):
            return None

        item = Nautilus.MenuItem(
            name="MAT2::Remove_metadata",
            label="Remove metadata",
            tip="Remove metadata"
        )
        item.connect('activate', self.__cb_menu_activate, files)

        return [item, ]

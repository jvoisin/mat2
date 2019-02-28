#!/usr/bin/env python3

"""
Because writing GUI is non-trivial (cf. https://0xacab.org/jvoisin/mat2/issues/3),
we decided to write a Nautilus extensions instead
(cf. https://0xacab.org/jvoisin/mat2/issues/2).

The code is a little bit convoluted because Gtk isn't thread-safe,
so we're not allowed to call anything Gtk-related outside of the main
thread, so we'll have to resort to using a `queue` to pass "messages" around.
"""

# pylint: disable=no-name-in-module,unused-argument,no-self-use,import-error

import queue
import threading
from typing import Tuple, Optional, List
from urllib.parse import unquote

import gi
gi.require_version('Nautilus', '3.0')
gi.require_version('Gtk', '3.0')
gi.require_version('GdkPixbuf', '2.0')
from gi.repository import Nautilus, GObject, Gtk, Gio, GLib, GdkPixbuf

from libmat2 import parser_factory


def _remove_metadata(fpath) -> Tuple[bool, Optional[str]]:
    """ This is a simple wrapper around libmat2, because it's
    easier and cleaner this way.
    """
    parser, mtype = parser_factory.get_parser(fpath)
    if parser is None:
        return False, mtype
    return parser.remove_all(), mtype

class Mat2Extension(GObject.GObject, Nautilus.MenuProvider, Nautilus.LocationWidgetProvider):
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

    def get_widget(self, uri, window) -> Gtk.Widget:
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

        close_buton = Gtk.Button("Close")
        close_buton.connect("clicked", lambda _: window.close())
        headerbar.pack_end(close_buton)

        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        window.add(box)

        box.add(self.__create_treeview())
        window.show_all()

    @staticmethod
    def __validate(fileinfo) -> Tuple[bool, str]:
        """ Validate if a given file FileInfo `fileinfo` can be processed.
        Returns a boolean, and a textreason why"""
        if fileinfo.get_uri_scheme() != "file" or fileinfo.is_directory():
            return False, "Not a file"
        elif not fileinfo.can_write():
            return False, "Not writeable"
        return True, ""

    def __create_treeview(self) -> Gtk.TreeView:
        liststore = Gtk.ListStore(GdkPixbuf.Pixbuf, str, str)
        treeview = Gtk.TreeView(model=liststore)

        renderer_pixbuf = Gtk.CellRendererPixbuf()
        column_pixbuf = Gtk.TreeViewColumn("Icon", renderer_pixbuf, pixbuf=0)
        treeview.append_column(column_pixbuf)

        for idx, name in enumerate(['File', 'Reason']):
            renderer_text = Gtk.CellRendererText()
            column_text = Gtk.TreeViewColumn(name, renderer_text, text=idx+1)
            treeview.append_column(column_text)

        for (fname, mtype, reason) in self.failed_items:
            # This part is all about adding mimetype icons to the liststore
            icon = Gio.content_type_get_icon('text/plain' if not mtype else mtype)
            # in case we don't have the corresponding icon,
            # we're adding `text/plain`, because we have this one for sure™
            names = icon.get_names() + ['text/plain', ]
            icon_theme = Gtk.IconTheme.get_default()
            for name in names:
                try:
                    img = icon_theme.load_icon(name, Gtk.IconSize.BUTTON, 0)
                    break
                except GLib.GError:
                    pass

            liststore.append([img, fname, reason])

        treeview.show_all()
        return treeview

    def __create_progressbar(self) -> Gtk.ProgressBar:
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

    def __update_progressbar(self, processing_queue, progressbar) -> bool:
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
            if self.failed_items:
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

    def __clean_files(self, files: list, processing_queue: queue.Queue) -> bool:
        """ This method is threaded in order to avoid blocking the GUI
        while cleaning up the files.
        """
        for fileinfo in files:
            fname = fileinfo.get_name()
            processing_queue.put(fname)

            valid, reason = self.__validate(fileinfo)
            if not valid:
                self.failed_items.append((fname, None, reason))
                continue

            fpath = unquote(fileinfo.get_uri()[7:])  # `len('file://') = 7`
            success, mtype = _remove_metadata(fpath)
            if not success:
                self.failed_items.append((fname, mtype, 'Unsupported/invalid'))
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

    def get_file_items(self, window, files) -> Optional[List[Nautilus.MenuItem]]:
        """ This method is the one allowing us to create a menu item.
        """
        # Do not show the menu item if not a single file has a chance to be
        # processed by mat2.
        if not any([is_valid for (is_valid, _) in map(self.__validate, files)]):
            return None

        item = Nautilus.MenuItem(
            name="MAT2::Remove_metadata",
            label="Remove metadata",
            tip="Remove metadata"
        )
        item.connect('activate', self.__cb_menu_activate, files)

        return [item, ]

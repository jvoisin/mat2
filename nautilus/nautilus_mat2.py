#!/usr/bin/env python3

# TODO:
# - Test with a large amount of files.
# - Show a progression bar when the removal takes time.
# - Improve the MessageDialog list for failed items.

import os
from urllib.parse import unquote

import gi
gi.require_version('Nautilus', '3.0')
gi.require_version('Gtk', '3.0')
from gi.repository import Nautilus, GObject, Gtk, Gio

from libmat2 import parser_factory

class Mat2Wrapper():
    def __init__(self, filepath):
        self.__filepath = filepath

    def remove_metadata(self):
        parser, mtype = parser_factory.get_parser(self.__filepath)
        if parser is None:
            return False, mtype
        return parser.remove_all(), mtype

class ColumnExtension(GObject.GObject, Nautilus.MenuProvider, Nautilus.LocationWidgetProvider):
    def notify(self):
        self.infobar_msg.set_text("Failed to clean some items")
        self.infobar.show_all()

    def get_widget(self, uri, window):
        self.infobar = Gtk.InfoBar()
        self.infobar.set_message_type(Gtk.MessageType.ERROR)
        self.infobar.set_show_close_button(True)
        self.infobar.connect("response", self.__cb_infobar_response)

        hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        self.infobar.get_content_area().pack_start(hbox, False, False, 0)

        btn = Gtk.Button("Show")
        btn.connect("clicked", self.__cb_show_failed)
        self.infobar.get_content_area().pack_end(btn, False, False, 0)

        self.infobar_msg = Gtk.Label()
        hbox.pack_start(self.infobar_msg, False, False, 0)

        return self.infobar

    def __cb_infobar_response(self, infobar, response):
        if response == Gtk.ResponseType.CLOSE:
            self.infobar.hide()

    def __cb_show_failed(self, button):
        self.infobar.hide()

        window = Gtk.Window()
        hb = Gtk.HeaderBar()
        window.set_titlebar(hb)
        hb.props.title = "Metadata removal failed"

        exit_buton = Gtk.Button("Exit")
        exit_buton.connect("clicked", lambda _: window.close())
        hb.pack_end(exit_buton)

        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        window.add(box)

        listbox = Gtk.ListBox()
        listbox.set_selection_mode(Gtk.SelectionMode.NONE)
        box.pack_start(listbox, True, True, 0)

        for i, mtype in self.failed_items:
            row = Gtk.ListBoxRow()
            hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
            row.add(hbox)

            icon = Gio.content_type_get_icon('text/plain' if not mtype else mtype)
            select_image = Gtk.Image.new_from_gicon(icon, Gtk.IconSize.BUTTON)
            hbox.pack_start(select_image, False, False, 0)

            label = Gtk.Label(os.path.basename(i))
            hbox.pack_start(label, True, False, 0)

            listbox.add(row)

        listbox.show_all()
        window.show_all()


    @staticmethod
    def __validate(f):
        if f.get_uri_scheme() != "file" or f.is_directory():
            return False
        elif not f.can_write():
            return False
        return True

    def __cb_menu_activate(self, menu, files):
        self.failed_items = list()
        for f in files:
            if not self.__validate(f):
                self.failed_items.append((f.get_name(), None))
                continue

            fname = unquote(f.get_uri()[7:])
            ret, mtype = Mat2Wrapper(fname).remove_metadata()
            if not ret:
                self.failed_items.append((f.get_name(), mtype))

        if len(self.failed_items):
            self.notify()

    def get_background_items(self, window, file):
        """ https://bugzilla.gnome.org/show_bug.cgi?id=784278 """
        return None

    def get_file_items(self, window, files):
        # Do not show the menu item if not a single file has a chance to be
        # processed by mat2.
        if not any(map(self.__validate, files)):
            return

        item = Nautilus.MenuItem(
            name="MAT2::Remove_metadata",
            label="Remove metadata",
            tip="Remove metadata"
        )
        item.connect('activate', self.__cb_menu_activate, files)

        return [item]

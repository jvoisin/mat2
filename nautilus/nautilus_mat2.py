#!/usr/bin/env python3

import gi
gi.require_version('Nautilus', '3.0')
from gi.repository import Nautilus, GObject

class ColumnExtension(GObject.GObject, Nautilus.MenuProvider):
    def menu_activate_cb(self, menu, file):
        print "menu_activate_cb", file
        # TODO: clean metadata here

    def get_background_items(self, window, file):
        """ https://bugzilla.gnome.org/show_bug.cgi?id=784278 """
        return None

    def get_file_items(self, window, files):
        if len(files) != 1:  # we're not supporting multiple files for now
            return

        file = files[0]

        item = Nautilus.MenuItem(
            name="MAT2::Remove_metadata",
            label="Remove metadata from %s" % file.get_name(),
            tip="Remove metadata from %s" % file.get_name()
        )
        item.connect('activate', self.menu_activate_cb, file)

        return [item]

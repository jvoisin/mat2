# GNU/Linux

## Fedora

Thanks to [atenart](https://ack.tf/), there is a package available on
[Fedora's copr]( https://copr.fedorainfracloud.org/coprs/atenart/mat2/ ).

## Debian

There is currently no package for Debian. If you want to help to make this
happen, there is an [issue](https://0xacab.org/jvoisin/mat2/issues/16) open.

But fear not, there is a way to install it *manually*:

```
# apt install python3-mutagen python3-gi-cairo gir1.2-gdkpixbuf-2.0 libimage-exiftool-perl gir1.2-glib-2.0 gir1.2-poppler-0.18
$ git clone https://0xacab.org/jvoisin/mat2.git
$ cd mat2
$ ./mat2
```

and if you want to install the über-fancy Nautilus extension:

```
# apt install python-gi-dev
$ git clone https://github.com/GNOME/nautilus-python
$ cd nautilus-python
$ PYTHON=/usr/bin/python3 ./autogen.sh
$ make
# make install
$ cp ./nautilus/nautilus_mat2.py ~/.local/share/nautilus-python/extensions/
$ PYTHONPATH=/home/$USER/mat2 PYTHON=/usr/bin/python3 nautilus
```


# GNU/Linux

## Fedora

Thanks to [atenart](https://ack.tf/), there is a package available on
[Fedora's copr]( https://copr.fedorainfracloud.org/coprs/atenart/mat2/ ).

We use copr (cool other packages repo) as the Mat2 Nautilus plugin depends on
python3-nautilus, which isn't available yet in Fedora (but is distributed
through this copr).

First you need to enable Mat2's copr:

```
dnf -y copr enable atenart/mat2
```

Then you can install both the Mat2 command and Nautilus extension:

```
dnf -y install mat2 mat2-nautilus
```

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
# apt install gnome-common gtk-doc-tools libnautilus-extension-dev python-gi-dev
$ git clone https://github.com/GNOME/nautilus-python
$ cd nautilus-python
$ PYTHON=/usr/bin/python3 ./autogen.sh
$ make
# make install
$ mkdir -p ~/.local/share/nautilus-python/extensions/
$ cp ../nautilus/mat2.py ~/.local/share/nautilus-python/extensions/
$ PYTHONPATH=/home/$USER/mat2 PYTHON=/usr/bin/python3 nautilus
```

## Arch Linux

Thanks to [Francois_B](https://www.sciunto.org/), there is an package available on
[Arch linux's AUR](https://aur.archlinux.org/packages/mat2/).

# Python ecosystem

If you feel like running arbitrary code downloaded over the
internet (pypi doesn't support gpg signatures [anymore](https://github.com/pypa/python-packaging-user-guide/pull/466)),
mat2 is [available on pypi](https://pypi.org/project/mat2/), and can be
installed like this:

```
pip3 install mat2
```

# GNU/Linux

## Optional dependencies

When [bubblewrap](https://github.com/projectatomic/bubblewrap) is
installed, MAT2 uses it to sandbox any external processes it invokes.

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

There a package available in Debian *buster/sid*. The package [doesn't include
the Nautilus extension yet](https://bugs.debian.org/910491).

For Debian 9 *stretch*, there is a way to install it *manually*:

```
# apt install python3-mutagen python3-gi-cairo gir1.2-gdkpixbuf-2.0 libimage-exiftool-perl gir1.2-glib-2.0 gir1.2-poppler-0.18 ffmpeg
# apt install bubblewrap  # if you want sandboxing
$ git clone https://0xacab.org/jvoisin/mat2.git
$ cd mat2
$ ./mat2
```

and if you want to install the über-fancy Nautilus extension:

```
# apt install gnome-common gtk-doc-tools libnautilus-extension-dev python-gi-dev python3-dev build-essential
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

## Gentoo

MAT2 is available in the [torbrowser overlay](https://github.com/MeisterP/torbrowser-overlay).

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
installed, mat2 uses it to sandbox any external processes it invokes.

## Arch Linux

Thanks to [kpcyrd](https://archlinux.org/packages/?maintainer=kpcyrd), there is an package available on
[Arch linux's AUR]([https://archlinux.org/packages/community/any/mat2/](https://archlinux.org/packages/community/any/mat2/)).

## Debian

There is a package available in [Debian](https://packages.debian.org/search?keywords=mat2&searchon=names&section=all) and you can install Mat2 with:

```
sudo apt install mat2
```

## Fedora

Thanks to [atenart](https://ack.tf/), there is a package available on
[Fedora's copr]( https://copr.fedorainfracloud.org/coprs/atenart/mat2/ ).

We use copr (cool other packages repo) as the Mat2 Nautilus plugin depends on
python3-nautilus, which isn't available yet in Fedora (but is distributed
through this copr).

First you need to enable Mat2's copr:

```
sudo dnf -y copr enable atenart/mat2
```

Then you can install both the Mat2 command and Nautilus extension:

```
sudo dnf -y install mat2 mat2-nautilus
```

## Gentoo

mat2 is available in the [torbrowser overlay](https://github.com/MeisterP/torbrowser-overlay).

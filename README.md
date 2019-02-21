```
 _____ _____ _____ ___
|     |  _  |_   _|_  |  Keep your data,
| | | |     | | | |  _|     trash your meta!
|_|_|_|__|__| |_| |___|

```

This software is currently in **beta**, please don't use it for anything
critical.

# Metadata and privacy

Metadata consist of information that characterizes data.
Metadata are used to provide documentation for data products.
In essence, metadata answer who, what, when, where, why, and how about
every facet of the data that are being documented.

Metadata within a file can tell a lot about you.
Cameras record data about when a picture was taken and what
camera was used. Office documents like PDF or Office automatically adds
author and company information to documents and spreadsheets.
Maybe you don't want to disclose those information on the web.

This is precisely the job of MAT2: getting rid, as much as possible, of
metadata.

# Requirements

- `python3-mutagen` for audio support
- `python3-gi-cairo` and `gir1.2-poppler-0.18` for PDF support
- `gir1.2-gdkpixbuf-2.0` for images support
- `FFmpeg`, optionally, for video support 
- `libimage-exiftool-perl` for everything else
- `bubblewrap`, optionally, for sandboxing

Please note that MAT2 requires at least Python3.5, meaning that it
doesn't run on [Debian Jessie](https://packages.debian.org/jessie/python3).

# Running the test suite

```bash
$ python3 -m unittest discover -v
```

And if you want to see the coverage:

```bash
$ python3-coverage run --branch -m unittest discover -s tests/
$ python3-coverage report --include -m --include /libmat2/*'
```

# How to use MAT2

```bash
usage: mat2 [-h] [-v] [-l] [--check-dependencies] [-V]
            [--unknown-members policy] [-s | -L]
            [files [files ...]]

Metadata anonymisation toolkit 2

positional arguments:
  files                 the files to process

optional arguments:
  -h, --help            show this help message and exit
  -v, --version         show program's version number and exit
  -l, --list            list all supported fileformats
  --check-dependencies  check if MAT2 has all the dependencies it needs
  -V, --verbose         show more verbose status information
  --unknown-members policy
                        how to handle unknown members of archive-style files
                        (policy should be one of: abort, omit, keep)
  -s, --show            list harmful metadata detectable by MAT2 without
                        removing them
  -L, --lightweight     remove SOME metadata
```

Note that MAT2 **will not** clean files in-place, but will produce, for
example, with a file named "myfile.png" a cleaned version named
"myfile.cleaned.png".

# Notes about detecting metadata

While MAT2 is doing its very best to display metadata when the `--show` flag is
passed, it doesn't mean that a file is clean from any metadata if MAT2 doesn't
show any. There is no reliable way to detect every single possible metadata for
complex file formats.

This is why you shouldn't rely on metadata's presence to decide if your file must
be cleaned or not.

# Notes about the lightweight mode

By default, mat2 might alter a bit the data of your files, in order to remove
as much metadata as possible. For example, texts in PDF might not be selectable anymore,
compressed images might get compressed again, …
Since some users might be willing to trade some metadata's presence in exchange
of the guarantee that mat2 won't modify the data of their files, there is the
`-L` flag that precisely does that.

# Related software

- The first iteration of [MAT](https://mat.boum.org)
- [Exiftool](https://sno.phy.queensu.ca/~phil/exiftool/mat)
- [pdf-redact-tools](https://github.com/firstlookmedia/pdf-redact-tools), that
	tries to deal with *printer dots* too.
- [pdfparanoia](https://github.com/kanzure/pdfparanoia), that removes
	watermarks from PDF.
- [Scrambled Exif](https://f-droid.org/packages/com.jarsilio.android.scrambledeggsif/),
	an open-source Android application to remove metadata from pictures.

# Contact

If possible, use the [issues system](https://0xacab.org/jvoisin/mat2/issues)
or the [mailing list](https://mailman.boum.org/listinfo/mat-dev)
Should a more private contact be needed (eg. for reporting security issues),
you can email Julien (jvoisin) Voisin at `julien.voisin+mat2@dustri.org`,
using the gpg key `9FCDEE9E1A381F311EA62A7404D041E8171901CC`.

# License

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Lesser General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU Lesser General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.

Copyright 2018 Julien (jvoisin) Voisin <julien.voisin+mat2@dustri.org>
Copyright 2016 Marie Rose for MAT2's logo

# Thanks

MAT2 wouldn't exist without:

- the [Google Summer of Code](https://summerofcode.withgoogle.com/);
- the fine people from [Tails]( https://tails.boum.org);
- friends

Many thanks to them!


```
 _____ _____ _____ ___ 
|     |  _  |_   _|_  |  Keep you data,
| | | |     | | | |  _|     trash your meta!
|_|_|_|__|__| |_| |___|
                       
```

[![pipeline status](https://0xacab.org/jvoisin/mat2/badges/master/pipeline.svg)](https://0xacab.org/jvoisin/mat2/commits/master)
[![coverage report](https://0xacab.org/jvoisin/mat2/badges/master/coverage.svg)](https://0xacab.org/jvoisin/mat2/commits/master)


# Requirements

- `python3-mutagen` for audio support
- `python3-gi-cairo` and `gir1.2-poppler-0.18` for PDF support
- `gir1.2-gdkpixbuf-2.0` for images support
- `libimage-exiftool-perl` for everything else

Please note that MAT2 requires at least Python3.5, meaning that it
doesn't run on [Debian Jessie](Stretc://packages.debian.org/jessie/python3),

# Run the testsuite

```bash
$ python3 -m unittest discover -v
```

# Related softwares

- The first iteration of [MAT](http://mat.boum.org)
- [Exiftool](https://sno.phy.queensu.ca/~phil/exiftool/mat)
- [pdf-redact-tools](https://github.com/firstlookmedia/pdf-redact-tools), that
	try to deal with *printer dots* too.
- [pdfparanoia](https://github.com/kanzure/pdfparanoia), that removes
	watermarks from PDF.

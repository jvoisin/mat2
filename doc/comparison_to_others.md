# Exiftool

mat2 is in fact using exiftool to extract metadata from files,
but not to remove them. The previous iteration of mat2, MAT,
was using exiftool to remove metadata, which lead to several cases where
they weren't correctly removed, if at all.
For example, [Exiftool's documentation](https://www.sno.phy.queensu.ca/~phil/exiftool/TagNames/PDF.html)
states the following with regard to PDF:

> All metadata edits are reversible. While this would normally be considered an
advantage, it is a potential security problem because old information is never
actually deleted from the file.

To remove metadata, mat2 usually re-render the file completely, eliminating
all possible original metadata. See the `implementation_notes.md` file for
details.


# jpegoptim, optipng, …

While designed to reduce as much as possible the size of pictures,
those software can be used to remove metadata. They usually have very good
support for a single picture format, and can be used in place of mat2 for them.


# PDF Redact Tools

[PDF Redact Tools](https://github.com/firstlookmedia/pdf-redact-tools) is
a software developed by the people from [First Look
Media](https://firstlook.media/), the entity behind, amongst other things, 
[The Intercept](https://theintercept.com/).

The tool uses roughly the same approach than mat2 to deal with PDF,
which is unfortunately the only fileformat that it does support.
It's interesting to note that it has counter-measures against
[yellow dots](https://en.wikipedia.org/wiki/Machine_Identification_Code),
a capacity that mat2 [doesn't possess yet](https://0xacab.org/jvoisin/mat2/issues/43).


# Exiv2

[Exiv2](https://www.exiv2.org/) was considered for mat2,
but it currently [misses a lot of metadata](https://0xacab.org/jvoisin/mat2/issues/85)


# Others non open source software/online service

There are a lot of closed-source software and online service claiming to remove
metadata from your files, but since there is no way to actually verify that
they're effectively removing them, let alone adding unique markers, they
shouldn't be used.

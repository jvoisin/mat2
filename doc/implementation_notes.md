Implementation notes
====================

Lightweight cleaning mode
-------------------------

Due to *popular* request, MAT2 is providing a *lightweight* cleaning mode,
that only cleans the superficial metadata of your file, but not
the ones that might be in **embedded** resources. Like for example,
images in a PDF or an office document.

Revisions handling
------------------

Revisions are handled according to the principle of least astonishment: they are entirely removed.

- Either the users aren't aware of the revisions, are thus they should be deleted. For example journalists that are editing a document to erase mentions sources mentions.

- Or they are aware of it, and will likely not expect MAT2 to be able to keep the revisions, that are basically traces about how, when and who edited the document.


Race conditions
---------------

MAT2 does its very best to avoid crashing at runtime. This is why it's checking
if the file is valid __at parser creation__. MAT2 doesn't take any measure to
ensure that the file is not changed between the time the parser is
instantiated, and the call to clean or show the metadata.

Symlink attacks
---------------

MAT2 output predictable filenames (like yourfile.jpg.cleaned).
This may lead to symlink attack. Please check if you OS prevent
against them

Archives handling
-----------------

MAT2 doesn't support archives yet, because we haven't found an usable way to ask the user
what to do when a non-supported files are encountered.

PDF handling
------------

MAT was doing some kind of rendering for PDF files, on a cairo surface, then
printed it to a file. This kept the text selectable, but unfortunately, it
didn't remove any *deep metadata*, like the ones in embedded pictures. This was
on of the reason MAT was abandoned: the absence of satisfying solution to
handle PDF. But apparently, people are ok with [pdf redact
tools](https://github.com/firstlookmedia/pdf-redact-tools), that simply
transform the PDF into images. So this is what's MAT2 is doing too.

Of course, it would be possible to detect images in PDf file, and process them
with MAT2, but since a PDF can contain a lot of things, like images, videos,
javascript, pdf, blobs, … this is the easiest and safest way to clean them.

Images handling
---------------

When possible, images are handled like PDF: rendered on a surface, then saved
to the filesystem. This ensures that every metadata is removed.


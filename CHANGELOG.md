# 0.12.4 - 2022-04-30

- Fix possible errors/crashes when processing multiple files
  via the command line interface
- Use a fixed PDF version for the output
- Improve compatibility with modern versions of rsvg
- Improve the robustness of the command line interface with
  regard to control characters

# 0.12.3 - 2022-01-06

- Implement code for internationalization
- Keep individual files compression type in zip files
- Increase the robustness of mat2 against weird/corrupted files
- Fix the dolphin integration
- Add a fuzzer

# 0.12.2 - 2021-08-29

- Add support for aiff files
- Improve MS Office support
- Improve compatibility with newer/older version of mat2's dependencies
- Fix possible issues with the resolution of processed pdf

# 0.12.1 - 2021-03-19

- Improve epub support
- Improve MS Office support

# 0.12.0 - 2020-12-18

- Improve significantly MS Office formats support
- Fix some typos in the Nautilus extension
- Improve reliability of the mp3, pdf and svg parsers
- Improve compatibility with ffmpeg when sandboxing is used
- Improve the dolphin extension usability
- libmat2 now raises a ValueError on malformed files while trying to 
  find the right parser, instead of returning None

# 0.11.0 - 2020-03-29

- Improve significantly MS Office formats support
- Refactor how mat2 looks for executables

# 0.10.1 - 2020-02-09

- Improve the documentation and the manpage
- Improve the robustness of css, html, png, gdk-based, exiftool-based parsers
- Future-proof a bit the testsuite
- Handle tiff files with a .tif extension
- Improve the sandbox' usability
- Add support for wav files

# 0.10.0 - 2019-11-30

- Make mat2 work on Python3.8
- Minor improvement of ppt handling
- Minor improvement of odt handling
- Add an integration KDE's file manager: Dolphin
- mat2 now copies file permissions on the cleaned files
- Add a flag to disable sandboxing
- Tighten a bit the sandboxing
- Improve handling of MSOffice documents
- Add support for inplace cleaning
- Better handling of mutually-exclusive arguments in the command line
- Add support for svg
- Add support for ppm
- Cleaned zip files are compressed by default
- Minor performances improvement when dealing with images/video files
- Better handling of optional dependencies

# 0.9.0 - 2019-05-10

- Add tar/tar.gz/tar.bz2/tar.zx archives support
- Add support for xhtml files
- Improve handling of read-only files
- Improve a bit the command line's documentation
- Fix a confusing error message
- Add even more tests
- Usuals internal cleanups/refactorings

# 0.8.0 - 2019-02-28

- Add support for epub files
- Fix the setup.py file crashing on non-utf8 platforms
- Improve css support
- Improve html support

# 0.7.0 - 2019-02-17

- Add support for wmv files
- Add support for gif files
- Add support for html files
- Sandbox external processes via bubblewrap
- Simplify archive-based formats processing
- The Nautilus extension now plays nicer with other extensions

# 0.6.0 - 2018-11-10

- Add lightweight cleaning for jpeg
- Add support for zip files
- Add support for mp4 files
- Improve metadata extraction for archives
- Improve robustness against corrupted embedded files
- Fix a possible security issue on some terminals (control character
	injection via --show)
- Various internal cleanup/improvements

# 0.5.0 - 2018-10-23

- Video (.avi files for now) support, via FFmpeg, optionally
- Lightweight cleaning for png and tiff files
- Processing files starting with a dash is now quicker
- Metadata are now displayed sorted
- Recursive metadata support for FLAC files
- Unsupported extensions aren't displayed in `./mat2 -l` anymore
- Improve the display when no metadata are found
- Update the logo according to the GNOME guidelines
- The testsuite is now runnable on the installed version of mat2
- Various internal cleanup/improvements

# 0.4.0 - 2018-10-03

- There is now a policy, for advanced users, to deal with unknown embedded fileformats
- Improve the documentation
- Various minor refactoring
- Improve how corrupted PNG are handled
- Dangerous/advanced cli's options no longer have short versions
- Significant improvements to office files anonymisation
	- Archive members are sorted lexicographically
	- XML attributes are sorted lexicographically too
	- RSID are now stripped
	- Dangling references in [Content_types].xml are now removed
- Significant improvements to office files support
- Anonimysed office files can now be opened by MS Office without warnings
- The CLI isn't threaded anymore, for it was causing issues
- Various misc typo fix

# 0.3.1 - 2018-09-01

- Document how to install mat2 for various distributions
- Fix various typos in the documentation/comments
- Add ArchLinux to the CI to ensure that mat2 is running on it
- Fix the handling of files with a name ending in `.JPG`
- Improve the detection of unsupported extensions in upper-case
- Streamline mat2's logging


# 0.3.0 - 2018-08-03

- Add a check for missing dependencies
- Add Nautilus extension
- Minors code simplifications
- Improve our linters' coverage
- Add a manpage
- Add folder/multiple files related tests
- Change the logo


# 0.2.0 - 2018-07-10

- Fix various crashes dues to malformed files
- Simplify various code-paths
- Remove superfluous debug message
- Remove the `--check` option that never was implemented anyway
- Add a `-c` option to check for mat2's dependencies


# 0.1.3 - 2018-07-06

- Improve mat2 resilience against corrupted images
- Check that the minimal version of Poppler is available
- Simplify how mat2 deals with office files
- Improve cleaning of office files
	- Thumbnails are removed
	- Revisions are removed
- Add support for plain text files


# 0.1.2 - 2018-06-21

- Rename some files to ease the packaging
- Add linters to the CI (mypy, bandit and pyflakes)
- Prevent exitftool-related parameters injections
- Improve mat2's resilience against corrupted files
- Make mat2 work on fedora, thanks to @atenart
- Tighten the threat model
- Simplify and improve how office files are handled

# 0.1.1 - 2018-05-16

- Improve the cli usage
- Refuse to process files with a supported mimetype but an unsupported
	extension, like `text/plain` for a `.c`

# 0.1.0 - 2018-05-14

- Initial release

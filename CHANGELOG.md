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

- Document how to install MAT2 for various distributions
- Fix various typos in the documentation/comments
- Add ArchLinux to the CI to ensure that MAT2 is running on it
- Fix the handling of files with a name ending in `.JPG`
- Improve the detection of unsupported extensions in upper-case
- Streamline MAT2's logging


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
- Add a `-c` option to check for MAT2's dependencies


# 0.1.3 - 2018-07-06

- Improve MAT2 resilience against corrupted images
- Check that the minimal version of Poppler is available
- Simplify how MAT2 deals with office files
- Improve cleaning of office files
	- Thumbnails are removed
	- Revisions are removed
- Add support for plain text files


# 0.1.2 - 2018-06-21

- Rename some files to ease the packaging
- Add linters to the CI (mypy, bandit and pyflakes)
- Prevent exitftool-related parameters injections
- Improve MAT2's resilience against corrupted files
- Make MAT2 work on fedora, thanks to @atenart
- Tighten the threat model
- Simplify and improve how office files are handled

# 0.1.1 - 2018-05-16

- Improve the cli usage
- Refuse to process files with a supported mimetype but an unsupported
	extension, like `text/plain` for a `.c`

# 0.1.0 - 2018-05-14

- Initial release

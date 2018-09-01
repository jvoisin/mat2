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

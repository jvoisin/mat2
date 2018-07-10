# 0.2.0 - 2018-07-010

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

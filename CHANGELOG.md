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

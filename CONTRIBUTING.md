# Contributing to mat2

The main repository for mat2 is on [github]( https://github.com/jvoisin/mat2 ),
but you can send patches to jvoisin by [email](https://dustri.org/) if you prefer.

Do feel free to pick up [an issue]( https://github.com/jvoisin/mat2/issues )
and to send a pull-request.

Mat2 also has unit tests (that are also run in the full test suite). You can run
them with `python3 -m unittest discover -v`.

If you're fixing a bug or adding a new feature, please add tests accordingly,
this will greatly improve the odds of your merge-request getting merged.

If you're adding a new fileformat, please add tests for:

1. Getting metadata
2. Cleaning metadata
3. Raising `ValueError` upon a corrupted file

Since mat2 is written in Python3, please conform as much as possible to the
[pep8]( https://pep8.org/ ) style; except where it makes no sense of course.

# Doing a release

1. Update the [changelog](https://github.com/jvoisin/mat2/blob/master/CHANGELOG.md)
2. Update the version in the [mat2](https://github.com/jvoisin/mat2/blob/master/mat2) file
3. Update the version in the [setup.py](https://github.com/jvoisin/mat2/blob/master/setup.py) file
4. Update the version in the [pyproject.toml](https://github.com/jvoisin/mat2/blob/master/yproject.toml) file
5. Update the version and date in the [man page](https://github.com/jvoisin/mat2/blob/master/doc/mat2.1)
6. Commit the modified files
7. Create a tag with `git tag -s $VERSION`
8. Push the commit with `git push origin master`
9. Push the tag with `git push --tags`
10. Download the github archive of the release
11. Diff it against the local copy
12. If there is no difference, sign the archive with `gpg --armor --detach-sign mat2-$VERSION.tar.xz`
13. Upload the signature on github [tag page](https://github.com/jvoisin/mat2/tags) and add the changelog there
14. Announce the release on the [mailing list](https://mailman.boum.org/listinfo/mat-dev)
15. Sign'n'upload the new version on pypi with `python3 setup.py sdist bdist_wheel` then `twine upload -s dist/*`
16. Do the secret release dance

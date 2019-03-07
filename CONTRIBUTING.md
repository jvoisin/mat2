# Contributing to MAT2

The main repository for MAT2 is on [0xacab]( https://0xacab.org/jvoisin/mat2 ),
but you can send patches to jvoisin by [email](https://dustri.org/) if you prefer.

Do feel free to pick up [an issue]( https://0xacab.org/jvoisin/mat2/issues )
and to send a pull-request. Please do check that everything is fine by running the
testsuite with `python3 -m unittest discover -v` before submitting one :)

If you're fixing a bug or adding a new feature, please add tests accordingly,
this will greatly improve the odds of your merge-request getting merged.

If you're adding a new fileformat, please add tests for:

1. Getting metadata
2. Cleaning metadata
3. Raising `ValueError` upon a corrupted file

Since MAT2 is written in Python3, please conform as much as possible to the
[pep8]( https://pep8.org/ ) style; except where it makes no sense of course.

# Doing a release

1. Update the [changelog](https://0xacab.org/jvoisin/mat2/blob/master/CHANGELOG.md)
2. Update the version in the [mat2](https://0xacab.org/jvoisin/mat2/blob/master/mat2) file
3. Update the version in the [setup.py](https://0xacab.org/jvoisin/mat2/blob/master/setup.py) file
4. Update the version and date in the [man page](https://0xacab.org/jvoisin/mat2/blob/master/doc/mat2.1)
5. Commit the changelog, man page, mat2 and setup.py files
6. Create a tag with `git tag -s $VERSION`
7. Push the commit with `git push origin master`
8. Push the tag with `git push --tags`
9. Download the gitlab archive of the release
10. Diff it against the local copy
11. If there is no difference, sign the archive with `gpg --armor --detach-sign mat2-$VERSION.tar.xz`
12. Upload the signature on Gitlab's [tag page](https://0xacab.org/jvoisin/mat2/tags) and add the changelog there
13. Announce the release on the [mailing list](https://mailman.boum.org/listinfo/mat-dev)
14. Sign'n'upload the new version on pypi with `python3 setup.py sdist bdist_wheel` then `twine upload -s dist/*`
15. Do the secret release dance

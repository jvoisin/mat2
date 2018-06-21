# Contributing to MAT2

The main repository for MAT2 is on [0xacab]( https://0xacab.org/jvoisin/mat2 ),
with a mirror on [gitlab.com]( https://gitlab.com/jvoisin/mat2 ).

Do feel free to pick up [an issue]( https://0xacab.org/jvoisin/mat2/issues )
and to send a pull-request. Please do check that everything is fine by running the
testsuite with `python3 -m unittest discover -v` before submitting one :)

If you're fixing a bug or adding a new feature, please add tests accordingly,
this will greatly improve the odds of your merge-request getting merged.

# Doing a release

1. Update the [changelog](https://0xacab.org/jvoisin/mat2/blob/master/CHANGELOG.md)
2. Update the version in the [mat2](https://0xacab.org/jvoisin/mat2/blob/master/mat2) file
3. Update the version in the [setup.py](https://0xacab.org/jvoisin/mat2/blob/master/setup.py) file
4. Commit the changelog, mat2 and setup.py files
5. Create a tag with `git tag -s $VERSION`
6. Push the tag with `git push --tags`

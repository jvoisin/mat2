# Contributing to MAT2

The main repository for MAT2 is on [0xacab]( https://0xacab.org/jvoisin/mat2 ),
with a mirror on [gitlab.com]( https://gitlab.com/jvoisin/mat2 ).

Do feel free to pick up [an issue]( https://0xacab.org/jvoisin/mat2/issues )
and to send a pull-request. Please do check that everything is fine by running the
testsuite with `python3 -m unittest discover -v` before submitting one :)

# Doing a release

1. Update the [changelog](https://0xacab.org/jvoisin/mat2/blob/master/CHANGELOG.md)
2. Update the version in the [main.py](https://0xacab.org/jvoisin/mat2/blob/master/main.py) file
3. Commit the changelog and the main.py file
4. Create a tag with `git tag -s $VERSION`
5. Push the tag with `git push --tags`

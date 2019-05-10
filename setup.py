import setuptools

with open("README.md", encoding='utf-8') as fh:
    long_description = fh.read()

setuptools.setup(
    name="mat2",
    version='0.9.0',
    author="Julien (jvoisin) Voisin",
    author_email="julien.voisin+mat2@dustri.org",
    description="A handy tool to trash your metadata",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://0xacab.org/jvoisin/mat2",
    python_requires = '>=3.5.0',
    scripts=['mat2'],
    install_requires=[
        'mutagen',
        'PyGObject',
        'pycairo',
    ],
    packages=setuptools.find_packages(exclude=('tests', )),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Environment :: Console",
        "License :: OSI Approved :: GNU Lesser General Public License v3 or later (LGPLv3+)",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3 :: Only",
        "Topic :: Security",
        "Intended Audience :: End Users/Desktop",
    ],
    project_urls={
        'bugtacker': 'https://0xacab.org/jvoisin/mat2/issues',
    },
)

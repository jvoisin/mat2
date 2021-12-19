import mimetypes
import os
import sys

sys.path.append('..')

import atheris

with atheris.instrument_imports(enable_loader_override=False):
    from libmat2 import parser_factory, UNSUPPORTED_EXTENSIONS

extensions = set()
for parser in parser_factory._get_parsers():  # type: ignore
    for mtype in parser.mimetypes:
        if mtype.startswith('video'):
            continue
        if 'aif' in mtype:
            continue
        if 'wav' in mtype:
            continue
        if 'gif' in mtype:
            continue
        if 'aifc' in mtype:
            continue
        for extension in mimetypes.guess_all_extensions(mtype):
            if extension not in UNSUPPORTED_EXTENSIONS:
                extensions.add(extension)
extensions = list(extensions)



def TestOneInput(data):
    fdp = atheris.FuzzedDataProvider(data)
    extension = fdp.PickValueInList(extensions)
    data = fdp.ConsumeBytes(sys.maxsize)

    fname = '/tmp/mat2_fuzz' + extension

    with open(fname, 'wb') as f:
        f.write(data)
    try:
        p, _ = parser_factory.get_parser(fname)
        if p:
            p.sandbox = False
            p.get_meta()
            p.remove_all()
            p, _ = parser_factory.get_parser(fname)
            p.get_meta()
    except ValueError:
        pass
    os.remove(fname)

atheris.Setup(sys.argv, TestOneInput)
atheris.Fuzz()

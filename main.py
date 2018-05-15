#!/usr/bin/python3

import os
from typing import Tuple
import sys
import itertools
import mimetypes
import argparse
import multiprocessing

from src import parser_factory

__version__ = '0.1.0'

def __check_file(filename:str, mode:int = os.R_OK) -> bool:
    if not os.path.isfile(filename):
        print("[-] %s is not a regular file." % filename)
        return False
    elif not os.access(filename, mode):
        print("[-] %s is not readable and writeable." % filename)
        return False
    return True


def create_arg_parser():
    parser = argparse.ArgumentParser(description='Metadata anonymisation toolkit 2')
    parser.add_argument('files', nargs='*')
    parser.add_argument('-v', '--version', action='version',
            version='MAT2 %s' % __version__)
    parser.add_argument('-l', '--list', action='store_true',
                      help='list all supported fileformats')

    info = parser.add_argument_group('Information')
    info.add_argument('-c', '--check', action='store_true',
                      help='check if a file is free of harmful metadatas')
    info.add_argument('-s', '--show', action='store_true',
                      help='list all the harmful metadata of a file without removing them')
    info.add_argument('-L', '--lightweight', action='store_true',
                      help='remove SOME metadata')
    return parser


def show_meta(filename:str):
    if not __check_file(filename):
        return

    p, mtype = parser_factory.get_parser(filename)
    if p is None:
        print("[-] %s's format (%s) is not supported" % (filename, mtype))
        return
    print("[+] Metadata for %s:" % filename)
    for k,v in p.get_meta().items():
        try:  # FIXME this is ugly.
            print("  %s: %s" % (k, v))
        except UnicodeEncodeError:
            print("  %s: harmful content" % k)


def clean_meta(params:Tuple[str, bool]) -> bool:
    filename, is_lightweigth = params
    if not __check_file(filename, os.R_OK|os.W_OK):
        return

    p, mtype = parser_factory.get_parser(filename)
    if p is None:
        print("[-] %s's format (%s) is not supported" % (filename, mtype))
        return False
    if is_lightweigth:
        return p.remove_all_lightweight()
    return p.remove_all()


def show_parsers():
    print('[+] Supported formats:')
    for parser in parser_factory._get_parsers():
        for mtype in parser.mimetypes:
            extensions = ', '.join(mimetypes.guess_all_extensions(mtype))
            print('  - %s (%s)' % (mtype, extensions))


def __get_files_recursively(files):
    for f in files:
        if os.path.isfile(f):
            yield f
        else:
            for path, _, _files in os.walk(f):
                for _f in _files:
                    yield os.path.join(path, _f)

def main():
    arg_parser = create_arg_parser()
    args = arg_parser.parse_args()

    if not args.files:
        if not args.list:
            return arg_parser.print_help()
        show_parsers()
        return

    elif args.show:
        for f in __get_files_recursively(args.files):
            show_meta(f)
        return

    else:
        p = multiprocessing.Pool()
        mode = (args.lightweight is True)
        l = zip(__get_files_recursively(args.files), itertools.repeat(mode))

        ret = list(p.imap_unordered(clean_meta, list(l)))
        return 0 if all(ret) else -1

if __name__ == '__main__':
    sys.exit(main())

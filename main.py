#!/usr/bin/python3

import os
import mimetypes
import argparse

from src import parser_factory


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

    info = parser.add_argument_group('Information')
    info.add_argument('-c', '--check', action='store_true',
                      help='check if a file is free of harmful metadatas')
    info.add_argument('-l', '--list', action='store_true',
                      help='list all supported fileformats')
    info.add_argument('-s', '--show', action='store_true',
                      help='list all the harmful metadata of a file without removing them')
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


def clean_meta(filename:str):
    if not __check_file(filename, os.R_OK|os.W_OK):
        return

    p, mtype = parser_factory.get_parser(filename)
    if p is None:
        print("[-] %s's format (%s) is not supported" % (filename, mtype))
        return
    p.remove_all()


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

    if args.show:
        for f in __get_files_recursively(args.files):
            show_meta(f)
    else:
        for f in __get_files_recursively(args.files):
            clean_meta(f)


if __name__ == '__main__':
    main()

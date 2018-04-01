import sys
import mimetypes
from shutil import copyfile
import argparse

from src import parser_factory


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
    p = parser_factory.get_parser(filename)
    if p is None:
        mtype, _ = mimetypes.guess_type(filename)
        print("[-] %s's format (%s) is not supported" % (filename, mtype))
        return
    for k,v in p.get_meta().items():
        print("%s: %s" % (k, v))

def main():
    argparser = create_arg_parser()
    args = argparser.parse_args()

    if args.show:
        for f in args.files:
            show_meta(f)
        return 0

    for f in args.files:
        p = parser_factory.get_parser(f)
        if p is None:
            print("[-] %s's format (%s) is not supported" % (f, "meh"))
            continue
        p.remove_all()


if __name__ == '__main__':

    main()

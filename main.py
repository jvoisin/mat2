import sys
from shutil import copyfile
import argparse

from src.parsers import pdf
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

def show_meta(file_name:str):
    p = parser_factory(file_name)
    for k,v in p.get_meta().items():
        print("%s: %s" % (k, v))

def main():
    argparser = create_arg_parser()
    args = argparser.parse_args()

    if args.show:
        for f in args.files:
            show_meta(f)
        return 0
    elif not args.files:
        return argparser.show_help()

    #p = pdf.PDFParser(sys.argv[1])
    p = parser_factory.get_parser(sys.argv[1])
    p.remove_all()
    p = pdf.PDFParser('OUT_clean.pdf')
    print("ok")


if __name__ == '__main__':

    main()

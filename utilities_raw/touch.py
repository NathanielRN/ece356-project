#!/usr/bin/env python3
"""change file timestamps

"""
from sys import exit
from argparse import ArgumentParser

from client_backend.fs_db_io import FSDatabase
from client_backend.fs_db_file import File, RegularFile
from client_backend.fs_db_file import IncorrectFileTypeError, MissingFileError

def parse_args():
    global ARGV, SHELL
    parser = ArgumentParser(description='change file timestamps')
    parser.add_argument('file', 
                        help='file(s) whose time should be updated. If does not exist, an empty file is created.',
                        nargs='+')

    return parser.parse_args(ARGV)

def main(args):
    global FS
    for filename in args.file:
        f = None
        try:
            f = RegularFile(FS, filename, create_if_missing=True, contents="")
        except IncorrectFileTypeError:
            f = File(FS, filename)
        f.modify()


if __name__ == "__main__":
    import sys
    from client_backend import shell_context
    FS = FSDatabase('.fs_db_rdbsh')
    ARGV = sys.argv[1:]
    SHELL = shell_context
    exit(main(parse_args()))


if __name__ == "__rdbsh__":
    exit(main(parse_args()))


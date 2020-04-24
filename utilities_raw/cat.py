#!/usr/bin/env python3
"""Output the contents of a file to the shell console
"""

from sys import exit
from argparse import ArgumentParser
from pathlib import PurePosixPath
from pathlib import Path

from client_backend.fs_db_file import Directory, File, RegularFile, SymbolicLink, IncorrectFileTypeError, MissingFileError
from client_backend.fs_db_io import FSDatabase

def parse_args():
    global ARGV, SHELL
    parser = ArgumentParser(description='Output the contents of a file.')
    parser.add_argument('target_filename', 
    help='the path of the directory whose files should be listed')

    return parser.parse_args(ARGV)


def main(args):
    global FS, SHELL

    try:
        matched_file = File.resolve_to(FS, args.target_filename, RegularFile)
    except IncorrectFileTypeError:
        print(f"cat: '{args.target_filename}/': Is a directory.")
        return 1
    except MissingFileError:
        print(f"cat: '{args.target_filename}': No such file or directory.")
        return 1

    for line in matched_file.readlines():
        print(line, end="")


if __name__ == "__main__":
    import sys
    from client_backend import shell_context
    FS = FSDatabase('.fs_db_rdbsh')
    ARGV = sys.argv[1:]
    SHELL = shell_context
    exit(main(parse_args()))


if __name__ == "__rdbsh__":
    exit(main(parse_args()))


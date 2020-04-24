#!/usr/bin/env python3
"""display a line of text

-n: do not output the trailing newline
"""
from sys import exit
from argparse import ArgumentParser

from client_backend.fs_db_io import FSDatabase

def parse_args():
    global ARGV, SHELL
    parser = ArgumentParser(description='display a line of text')
    parser.add_argument('-n', "--no-newline", action='store_true', help="do not output the trailing newline")
    parser.add_argument('line_to_print', 
    help='the text to echo',
    nargs='*',
    default="")

    return parser.parse_args(ARGV)

def main(args):
    print(*args.line_to_print, end="")
    if not args.no_newline:
        print("")
    # if error:
    #     return -1
    return 0

if __name__ == "__main__":
    import sys
    from client_backend import shell_context
    FS = FSDatabase('.fs_db_rdbsh')
    ARGV = sys.argv[1:]
    SHELL = shell_context
    exit(main(parse_args()))


if __name__ == "__rdbsh__":
    exit(main(parse_args()))


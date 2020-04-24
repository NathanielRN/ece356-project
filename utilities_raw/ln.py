#!/usr/bin/env python3
"""make links between files

-s: make symbolic links instead of hard links
"""
from sys import exit
from argparse import ArgumentParser

from client_backend.fs_db_io import FSDatabase
from client_backend.fs_db_file import File, SymbolicLink, RegularFile

def parse_args():
    global ARGV, SHELL
    parser = ArgumentParser(description='display a line of text')
    parser.add_argument('-s', "--soft-link", action='store_true', help="do not output the trailing newline")
    parser.add_argument('target', help="file that link will point to")
    parser.add_argument('link_name', help="filename/path of link file")

    return parser.parse_args(ARGV)

def main(args):
    global FS
    #TODO: Verify that link_path does not exist


    if args.soft_link:
        #TODO: Convert to absolute path
        target = args.target
        #NOTE: Errors with link_name shouldn't occur since already verified that it doesn't exist
        SymbolicLink(FS, args.link_name, create_if_missing=True, linked_path=target)
        return

    try:
        target_file = File.resolve_to(FS, args.target, RegularFile)
        target_file.hardlink(args.link_name)
    except IncorrectType:
        # TODO: Catch hardlink errors
        print("is directory")
        return 1

if __name__ == "__main__":
    import sys
    from client_backend import shell_context
    FS = FSDatabase('.fs_db_rdbsh')
    ARGV = sys.argv[1:]
    SHELL = shell_context
    exit(main(parse_args()))


if __name__ == "__rdbsh__":
    exit(main(parse_args()))

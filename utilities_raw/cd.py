#!/usr/bin/env python3
"""Change the shell working directory

Note: Change shebang to `rdbsh` to use has system utility with shell
"""
from argparse import ArgumentParser

from client_backend.fs_db_file import Directory, MissingFileError

def parse_args():
    global ARGV
    parser = ArgumentParser(description="Change the current working directory.")
    parser.add_argument('path_to_change_to', help='The relative or absoulte path to navigate to')

    return parser.parse_args(ARGV)

def main(args):
    global FS, SHELL
    try:
        new_dir = Directory(FS, args.path_to_change_to)
    except MissingFileError:
        print (f"cd: No such directory")
        return 1
    SHELL.PWD = new_dir.full_name


if __name__ == "__main__":
    import sys
    from client_backend import shell_context
    FS = FSDatabase('.fs_db_rdbsh')
    ARGV = sys.argv[1:]
    SHELL = shell_context
    main(parse_args())

if __name__ == "__rdbsh__":
    main(parse_args())


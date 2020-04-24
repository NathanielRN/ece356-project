#!/usr/bin/env python3
"""Change the shell working directory

Note: Change shebang to `rdbsh` to use has system utility with shell
"""
from sys import exit
from argparse import ArgumentParser

from client_backend.fs_db_file import File, Directory, RegularFile, IncorrectFileTypeError, MissingFileError
from client_backend.fs_db_io import FSDatabase

def parse_args():
    global ARGV
    parser = ArgumentParser(description="Change the current working directory.")
    parser.add_argument('path_to_change_to', help='The relative or absoulte path to navigate to')

    return parser.parse_args(ARGV)

def main(args):
    global FS, SHELL
    path = args.path_to_change_to
    if args.path_to_change_to == "-":
        path = SHELL.OLDPWD
    try:
        new_dir = File.resolve_to(FS, path, Directory)
        SHELL.OLDPWD, SHELL.PWD = SHELL.PWD, new_dir.full_name
    except MissingFileError:
        print(f"cd: '{path}': No such file or directory.")
        return 1
    except IncorrectFileTypeError:
        print(f"cd: '{path}': Not a directory.")
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


#!/usr/bin/env python3
"""make links between files

-s: make symbolic links instead of hard links
"""
from sys import exit
from pathlib import PurePosixPath
from argparse import ArgumentParser

from client_backend.fs_db_io import FSDatabase
from client_backend.fs_db_file import File, SymbolicLink, RegularFile
from client_backend.fs_db_file import MissingFileError, IncorrectFileTypeError

def parse_args():
    global ARGV, SHELL
    parser = ArgumentParser(description='display a line of text')
    parser.add_argument('-s', "--soft-link", action='store_true', help="do not output the trailing newline")
    parser.add_argument('target', help="file that link will point to")
    parser.add_argument('link_name', help="filename/path of link file")

    return parser.parse_args(ARGV)

# See FSDatabase._resolve_relative_path
def to_abs_path(path):
    global SHELL
    ctx_path = PurePosixPath("/")
    path = PurePosixPath(path)
    if path.parts and path.parts[0] == "~":
        ctx_path = PurePosixPath(SHELL.HOME)
    else:
        ctx_path = PurePosixPath(SHELL.PWD)

    assert ctx_path.anchor
    # if path starts with /, will ignore ctx_path automatically
    return ctx_path.joinpath(path)

def main(args):
    global FS
    try:
        File(FS, args.link_name)
        print(f"ln: failed to create symbolic link '{args.link_name}': File exists")
        return 1
    except MissingFileError:
        pass
    # NOTE: IncorrectFileTypeEror is impossible.

    if args.soft_link:
        target = to_abs_path(args.target)
        # NOTE: Errors with link_name shouldn't occur since already verified that it doesn't exist
        SymbolicLink(FS, args.link_name, create_if_missing=True, linked_path=target)
        return

    try:
        target_file = File.resolve_to(FS, args.target, RegularFile)
        target_file.hardlink(args.link_name)
    except MissingFileError:
        print(f"ln: failed to access '{args.target}': No such file or directory")
        return 1
    except IncorrectFileTypeError:
        print(f"ln: {args.target}: hard link not allowed for directory")
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

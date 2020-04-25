#!/usr/bin/env python3
"""Output the contents of a directory

-l: Use long-format when viewing output
"""
from sys import exit
from argparse import ArgumentParser
from pathlib import PurePosixPath
from pathlib import Path

from client_backend.fs_db_file import File, Directory, SymbolicLink
from client_backend.fs_db_file import MissingFileError, IncorrectFileTypeError
from client_backend.fs_db_io import FSDatabase

def parse_args():
    global ARGV, SHELL
    parser = ArgumentParser(description='List files in a directory.')
    parser.add_argument('-l', '--long-format', action='store_true')
    parser.add_argument('path', 
    help='the path(s) of directories whose files should be listed',
    nargs='*')

    return parser.parse_args(ARGV)


def resolve_to_dir(path):
    global FS
    try:
        f = File.resolve_to(FS, path, Directory)
        return f
    except IncorrectFileTypeError:
        return None

def list_contents(directory, args, include_header=True):
    global FS, SHELL
    files = list(directory.walk()) if isinstance(directory, Directory) else [directory]
    if args.long_format:
        file_desc_list = []
        total_size = 0

        for curr_file in files:
            total_size += curr_file.size
            filetype_desc = '-'
            link_desc = ''
            filetype = curr_file.type
            if filetype is Directory:
                filetype_desc = 'd'
            elif filetype is SymbolicLink:
                filetype_desc = 'l'
                link_desc = f' -> {curr_file.linked_path}'
            file_desc = (
                f"{filetype_desc}{str(curr_file.permissions)} "
                f"{curr_file.num_of_hard_links} "
                f"{curr_file.owner.name} "
                f"{curr_file.group_owner.name} "
                f"{curr_file.size} "
                f"{curr_file.modified_date.strftime('%b %d %H:%M')} "
                f"{curr_file.full_name}{link_desc}"
            )

            file_desc_list.append(file_desc)
        if include_header:
            print(f"total {total_size}")
        for file_desc in file_desc_list:
            print(file_desc)
    else:
        for curr_file in files:
            print(curr_file.name, end=" ")


def main(args):
    global FS
    to_list = args.path or ["."]

    if len(to_list) == 1:
        try:
            f = File(FS, to_list[0])
            as_dir = resolve_to_dir(to_list[0])
            list_contents(as_dir or f, args)
            print()
            return
        except MissingFileError:
            print(f"Cannot access '{to_list[0]}': No such file or directory.")
            return 1

    for path in to_list:
        try:
            f = File(FS, path)
            as_dir = resolve_to_dir(path)
            if as_dir:
                print(f"{f.full_name}:")
                list_contents(as_dir, args)
                print()
            else:
                list_contents(f, args, include_header=False)

        except MissingFileError:
            print(f"Cannot access '{path}': No such file or directory.")
            return 1
        print()


if __name__ == "__main__":
    import sys
    from client_backend import shell_context
    FS = FSDatabase('.fs_db_rdbsh')
    ARGV = sys.argv[1:]
    SHELL = shell_context
    exit(main(parse_args()))


if __name__ == "__rdbsh__":
    exit(main(parse_args()))

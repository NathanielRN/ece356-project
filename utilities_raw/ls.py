#!/usr/bin/env python3

from argparse import ArgumentParser
from pathlib import PurePosixPath
from pathlib import Path

from client_backend.fs_db_file import Directory, SymbolicLink, MissingFileError
from client_backend.fs_db_io import FSDatabase

def parse_args():
    global ARGV
    parser = ArgumentParser(description='List files in a directory.')
    parser.add_argument('-l', '--long-format', action='store_true')
    parser.add_argument('directory_listing_path', 
    help='the path of the directory whose files should be listed',
    nargs='?',
    default=shell_context.PWD)

    return parser.parse_args(ARGV)


def main(args):
    global FS, SHELL

    try:
        parsedTargetFile = Directory(FS, args.directory_listing_path)
    except MissingFileError:
        print(f"Cannot access '{args.directory_listing_path}': No such file or directory.")
        return 1

    files = list(parsedTargetFile.walk()) if parsedTargetFile.type is Directory else [parsedTargetFile]

    if args.long_format:
        file_desc_list = []
        total_size = 0

        for curr_file in files:
            total_size += curr_file.size
            filetype_desc = '-'
            filetype = curr_file.type
            if filetype is Directory:
                filetype_desc = 'd'
            elif filetype is SymbolicLink:
                filetype_desc = 'l'
            file_desc = (
                f"{filetype_desc}{str(curr_file.permissions)} "
                f"{curr_file.num_of_hard_links} "
                f"{curr_file.owner.name} "
                f"{curr_file.group_owner.name} "
                f"{curr_file.size} "
                f"{curr_file.modified_date.strftime('%b %d %H:%M')} "
                f"{curr_file.full_name}"
            )

            file_desc_list.append(file_desc)
        print(f"total {total_size}")
        [print(file_desc) for file_desc in file_desc_list]
    else:
        [print(curr_file.name, end=" ") for curr_file in files]
        print()


if __name__ == "__main__":
    import sys
    from client_backend import shell_context
    FS = FSDatabase('.fs_db_rdbsh')
    ARGV = sys.argv[1:]
    SHELL = shell_context
    main(parse_args())


if __name__ == "__rdbsh__":
    main(parse_args())


#!/usr/bin/env python3
"""Search for files in a directory hierarchy

Note: Change shebang to `rdbsh` to use has system utility with shell
"""
from sys import exit
from argparse import ArgumentParser

from client_backend.fs_db_file import Directory, SymbolicLink
from client_backend.fs_db_io import FSDatabase

def parse_args():
    global ARGV
    parser = ArgumentParser(description='Finds directories and files matching provided name')
    parser.add_argument('path_pattern', help='the directory and (partial) name of the file to be found')

    return parser.parse_args(ARGV)

def main(args):
    global FS, SHELL
    file_path = args.path_pattern

    pattern_components = file_path.split('/')

    search_directory = None

    if len(pattern_components) == 1:
        search_directory = Directory(FS, SHELL.PWD)
    else:
        search_directory = Directory(FS, pattern_components[:-1].join('/') if len(pattern_components) > 2 else pattern_components[0])

    matched_files = None
    if '*' in pattern_components[-1]:
        foundFiles = list(search_directory.get_children_like(pattern_components[-1], search_subdirs=True))

        if foundFiles.empty():
            print(f"'{pattern_components[-1]}': No such file or directory")
            return 1
        
        matched_files = list(foundFiles)
    else:
        matched = search_directory.get_file(pattern_components[-1])
        if matched is None:
            print(f"'{pattern_components[-1]}': No such file or directory")
            return 1
        elif matched.type is Directory:
            print(f"'{matched.name}' is a directory.")
            return 1
        matched_files = [matched]

    for curr_file in matched_files:
        filetype_desc = '-'
        filetype = curr_file.type
        if filetype is Directory:
            filetype_desc = 'd'
        elif filetype is SymbolicLink:
            filetype_desc = 'l'
        print(
            f"{filetype_desc}{str(curr_file.permissions)} "
            f"{curr_file.num_of_hard_links} "
            f"{curr_file.owner.name} "
            f"{curr_file.group_owner.name} "
            f"{curr_file.size} "
            f"{curr_file.modified_date.strftime('%b %d %H:%M')} "
            f"{curr_file.full_name}"
        )


if __name__ == "__main__":
    import sys
    from client_backend import shell_context
    FS = FSDatabase('.fs_db_rdbsh')
    ARGV = sys.argv[1:]
    SHELL = shell_context
    exit(main(parse_args()))

if __name__ == "__rdbsh__":
    exit(main(parse_args()))

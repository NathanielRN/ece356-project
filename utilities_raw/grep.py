#!/usr/bin/env python3
"""Search for pattern matches within files

Note: Change shebang to `rdbsh` to use has system utility with shell
"""
from argparse import ArgumentParser

from client_backend.fs_db_file import Directory
from client_backend.fs_db_io import FSDatabase

def parse_args():
    global ARGV
    parser = ArgumentParser(description='Find provided pattern in files')
    parser.add_argument('-r', '--recursive', help='recursively search the directory', action='store_true')
    parser.add_argument('search_pattern', help='the pattern to search for in matching files')
    parser.add_argument('file_pattern', help='files that match this file pattern will be searched')

    return parser.parse_args(ARGV)

def main(args):
    global FS, SHELL
    file_pattern_components = args.file_pattern.split('/')

    find_directory = None

    if len(file_pattern_components) == 1:
        find_directory = Directory(FS, SHELL.PWD)
    else:
        find_directory = Directory(FS, file_pattern_components[:-1].join('/') if len(file_pattern_components) > 2 else file_pattern_components[0])

    matchedFiles = None
    if '*' in file_pattern_components[-1]:
        foundFiles = list(find_directory.get_children_like(file_pattern_components[-1].replace('*', '%'), search_subdirs=args.recursive))

        if foundFiles.empty():
            print(f"'{file_pattern_components[-1]}': No such file or directory")
            return 1
        
        matchedFiles = list(foundFiles)
    else:
        foundFile = find_directory.get_file(file_pattern_components[-1])
        if foundFile is None:
            print(f"'{file_pattern_components[-1]}': No such file or directory")
            return 1
        elif foundFile.type is Directory:
            print(f"'{foundFile.name}' is a directory.")
            return 1
        matchedFiles = [foundFile]
 
    if len(matchedFiles) == 1:
        for line_no, line_content in matchedFiles[0].find_in_file(f".*{args.search_pattern}.*"):
            print(f"Line {line_no}: {line_content}", end="")
    else:
        for file_to_search in matchedFiles:
            for line_no, line_content in file_to_search.find_in_file(f".*{args.search_pattern}.*"):
                print(f"{file_to_search.full_name} - Line {line_no}: {line_content}", end="")


if __name__ == "__main__":
    import sys
    from client_backend import shell_context
    FS = FSDatabase('.fs_db_rdbsh')
    ARGV = sys.argv[1:]
    SHELL = shell_context
    main(parse_args())

if __name__ == "__rdbsh__":
    main(parse_args())

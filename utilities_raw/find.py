#!/usr/bin/env python3
"""Search for files in a directory hierarchy

Note: Change shebang to `rdbsh` to use has system utility with shell
"""
import re
from datetime import datetime, timedelta
from sys import exit
from argparse import ArgumentParser, Namespace, RawTextHelpFormatter

from client_backend.fs_db_file import File, Directory, RegularFile, SymbolicLink
from client_backend.fs_db_file import MissingFileError
from client_backend.fs_db_users import User, Group
from client_backend.fs_db_users import MissingGroupError, MissingUserError
from client_backend.fs_db_io import FSDatabase

def parse_args():
    global ARGV
    parser = ArgumentParser(description='Finds directories and files matching provided name', formatter_class=RawTextHelpFormatter)
    parser.add_argument(
            'path_pattern', 
            help='paths to verify against '
            'followed by an expression to match these paths against. '
            'Directories are recusively searched. \n\n'
            'Expressions should be preceded by a \'+\' sign and follow all paths. \n\n'
            'Supported expressions:\n\n'
            '+ls - print using long list format\n'
            '+name [EXPRESSION] - only files whose name match the (glob) expression\n'
            '+group [GROUP] - only files who are owned by GROUP \n'
            '+gid [GROUP] - alias for +group\n'
            '+uid [USER] - only files who are owned by USER\n'
            '+user [USER] - alias for +user\n'
            '+type [TYPE] - only files of type TYPE. Possible options are link (\'l\'), directory (\'d\') & file (\'f\') \n'
            '+empty - only empty files/directories',
            nargs="*"
    )
    return parser.parse_args(ARGV)

def split_paths_from_expression(paths_and_expression):
    paths = []
    expression = Namespace()
    pattern_mode = False
    curr_pattern = None
    pattern_args = []
    for arg in paths_and_expression:
        if arg.startswith("+"):
            if curr_pattern:
                if len(pattern_args) <= 1:
                    pattern_args = pattern_args[0] if len(pattern_args) == 1 else True
                setattr(expression, curr_pattern, pattern_args)
            curr_pattern = arg.strip("+")
            pattern_args = []
            pattern_mode = True
        elif pattern_mode:
            pattern_args.append(arg)
        else:
            paths.append(arg)
    if curr_pattern:
        if len(pattern_args) <= 1:
            pattern_args = pattern_args[0] if len(pattern_args) == 1 else True
        setattr(expression, curr_pattern, pattern_args)
    return paths, expression

def verify_expression(expression):
    global FS
    if hasattr(expression, "ls"):
        if not isinstance(expression.ls, bool):
            return False
    else:
        expression.ls = False
    if hasattr(expression, "name"):
        if isinstance(expression.name, (bool, list)):
            return False
    else:
        expression.name = "*"
    if hasattr(expression, "type"):
        if isinstance(expression.type, (bool, list)) or len(expression.type) > 1:
            return False
    if hasattr(expression, "uid"):
        expression.user = expression.uid
        delattr(expression, "uid")
    if hasattr(expression, "user"):
        if isinstance(expression.user, (bool, list)):
            return False
        user = int(expression.user) if expression.user.isdigit() else expression.user
        try:
            expression.user = User(FS, user)
        except MissingUserError:
            print(f"find: No user '{user}'")
            return False
    if hasattr(expression, "empty"):
        if not isinstance(expression.empty, bool):
            return False

    if hasattr(expression, "gid"):
        expression.group = expression.gid
        delattr(expression, "gid")
    if hasattr(expression, "group"):
        if isinstance(expression.group, (bool, list)):
            return False
        group = int(expression.group) if expression.group.isdigit() else expression.group
        try:
            expression.group = Group(FS, group)
        except MissingGroupError:
            print(f"find: No group '{group}'")
            return False
    return True

def check_against_expression(f, expression):
    type_to_filetype = {
        "d": Directory,
        "f": RegularFile,
        "l": SymbolicLink,
    }
    if hasattr(expression, "type"):
        if expression.type not in type_to_filetype:
            return False
        else:
            if not isinstance(f, type_to_filetype[expression.type]):
                return False
    if hasattr(expression, "user"):
        if f.owner != expression.user:
            return False
    if hasattr(expression, "empty"):
        if isinstance(f, Directory):
            if not f.empty():
                return False
        elif isinstance(f, RegularFile):
            for line in f.readlines():
                if line:
                    # Has content
                    return False
        else:
            # All other file types are "non-empty"
            return False
    if hasattr(expression, "group"):
        if f.group_owner != expression.group:
            return False
    return True

def as_long_format(curr_file):
    filetype_desc = '-'
    link_desc = ''
    filetype = curr_file.type
    if filetype is SymbolicLink:
        filetype_desc = 'l'
        link_desc = f' -> {curr_file.linked_path}'
    permissions_str = f"{filetype_desc}{str(curr_file.permissions)} "
    hard_links_str = f"{curr_file.num_of_hard_links} "
    owner_str = f"{curr_file.owner.name} "
    group_owner_str = f"{curr_file.group_owner.name} "
    file_size_str = f"{curr_file.size} "
    file_date = curr_file.modified_date if isinstance(curr_file, Directory) else curr_file.created_date
    date_time_str = f"{file_date.strftime('%b %d %H:%M')} " if datetime.now() - file_date < timedelta(days=6*30) and file_date < datetime.now() else f"{file_date.strftime('%b %d %Y')}"
    full_name_str = f"{curr_file.full_name}{link_desc}"
    file_desc = [
        permissions_str,
        hard_links_str,
        owner_str,
        group_owner_str,
        file_size_str,
        date_time_str,
        full_name_str
    ]
    return " ".join(file_desc)

def _glob_to_sql(glob):
    # Will change any glob characters
    return (glob.replace("\\", "\\\\")
            .replace("%", "\%")
            .replace("*", "%")
            .replace("_", "\_")
            .replace("?", "_"))

def _glob_to_regex(glob):
    # Will change any glob characters
    return glob.replace("*", ".*").replace("_", "?")

def main(args):
    global FS, SHELL
    path_pattern = args.path_pattern
    paths, expression = split_paths_from_expression(args.path_pattern)
    if not verify_expression(expression):
        print("find: invalid expression")
        return 1
    regex_name = re.compile(_glob_to_regex(expression.name))
    sql_name = _glob_to_sql(expression.name)
    paths = paths or ["."]
    failed_any_paths = False
    for path in paths:
        try:
            files_to_check = []
            start_file = File(FS, path)
            files_to_check.append(start_file)
            if isinstance(start_file, Directory):
                    files_to_check.extend(start_file.get_children_like(sql_name, search_subdirs=True))
            for check_file in files_to_check:
                if regex_name.match(check_file.name) and check_against_expression(check_file, expression):
                    print(as_long_format(check_file) if expression.ls else check_file.full_name)
        except MissingFileError:
            print(f"find: '{path}': No such file or directory")
            failed_any_paths = True
    return int(failed_any_paths)

if __name__ == "__main__":
    import sys
    from client_backend import shell_context
    FS = FSDatabase('.fs_db_rdbsh')
    ARGV = sys.argv[1:]
    SHELL = shell_context
    exit(main(parse_args()))

if __name__ == "__rdbsh__":
    exit(main(parse_args()))

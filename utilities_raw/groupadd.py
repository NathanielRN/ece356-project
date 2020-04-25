#!/usr/bin/env python3
"""create a new group

-g: Specify specific group ID
"""
from sys import exit
from contextlib import suppress
from argparse import ArgumentParser

from client_backend.fs_db_io import FSDatabase
from client_backend.fs_db_users import Group, User, MissingGroupError, MissingUserError

def parse_args():
    global ARGV, SHELL
    parser = ArgumentParser(description='creates a new group account using specified values')
    parser.add_argument('-g', "--gid", help="group ID to use", nargs="?", type=int)
    parser.add_argument('group_name', help="the name of the group to add")

    return parser.parse_args(ARGV)


def main(args):
    global FS
    with suppress(MissingGroupError):
        if args.gid:
            Group(FS, uid=args.gid)
            print(f"groupadd: GID {args.gid} is not unique")
            return 1

    with suppress(MissingUserError):
        User(FS, user_name=args.group_name)
        print(f"groupadd: group {args.group_name} already exists")
        return 1

    new_group = Group(FS, gid=args.gid, group_name=args.group_name, create_if_missing=True)

if __name__ == "__main__":
    import sys
    from client_backend import shell_context
    FS = FSDatabase('.fs_db_rdbsh')
    ARGV = sys.argv[1:]
    SHELL = shell_context
    exit(main(parse_args()))


if __name__ == "__rdbsh__":
    exit(main(parse_args()))


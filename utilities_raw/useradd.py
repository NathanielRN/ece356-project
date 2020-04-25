#!/etc/bin/env python3
"""create a new user or update default new user information

-D: print or change default useradd configuration
-g: name or ID of of the primary group of the new account
-G: list of supplementary groups of the new account
-u: userid to assign to this user
"""
from sys import exit
from contextlib import suppress
from argparse import ArgumentParser

from client_backend.fs_db_io import FSDatabase
from client_backend.fs_db_users import Group, User, MissingGroupError, MissingUserError

def parse_args():
    global ARGV, SHELL
    parser = ArgumentParser(description='create a new user or update default new user information')
    parser.add_argument('-g', "--gid", help="name or ID of of the primary group of the new account", nargs="?")
    parser.add_argument('-G', "--groups", help="list of supplementary groups of the new account", nargs="*")
    parser.add_argument('-u', "--uid", help="userid to assign to this user", nargs="?", type=int)
    parser.add_argument('user_name', help="the name of the user to add")

    return parser.parse_args(ARGV)

def main(args):
    global FS

    groups = []
    if args.gid:
        group = None
        gid = args.gid
        try:
            if gid.isdigit():
                group = Group(FS, gid=int(gid))
            else:
                group = Group(FS, group_name=gid)
            groups.append(group)
        except MissingGroupError:
            print(f"useradd: group '{args.gid}' does not exist")
            return 1

    if args.groups:
        for group in args.groups:
            try:
                if group.isdigit():
                    groups.append(Group(FS, gid=int(group)))
                else:
                    groups.append(Group(FS, None, group_name=group))
            except MissingGroupError:
                print(f"useradd: group '{group}' does not exist")
                return 1

    with suppress(MissingUserError):
        if args.uid is not None:
            User(FS, uid=args.uid)
            print(f"useradd: UID {args.uid} is not unique")
            return 1

    with suppress(MissingUserError):
        User(FS, user_name=args.user_name)
        print(f"useradd: user {args.user_name} already exists")
        return 1

    new_user = User(FS, args.uid, create_if_missing=True, user_name=args.user_name)

    for groupEntity in groups:
        new_user.add_to_group(groupEntity)


if __name__ == "__main__":
    import sys
    from client_backend import shell_context
    FS = FSDatabase('.fs_db_rdbsh')
    ARGV = sys.argv[1:]
    SHELL = shell_context
    exit(main(parse_args()))


if __name__ == "__rdbsh__":
    exit(main(parse_args()))

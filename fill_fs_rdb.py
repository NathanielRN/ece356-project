#!/usr/bin/env python3
import pwd

from argparse import ArgumentParser

from os import chdir
from pathlib import PurePath, Path

from client_backend.fs_db_io import FSDatabase 
from client_backend.fs_db_file import *
from client_backend.fs_db_users import *

from stat import S_IRWXU, S_IRWXG, S_IRWXO

FS_DB = FSDatabase('.fs_db_rdbsh')
ROOTFS_PATH = Path('setup/rootfs/')

# Should create root user (uid/gid = 0) & nobody user (uid/gid = 99)

def _to_db_path(path):
    try:
        if path.anchor:
            currentPath = Path().resolve()
            path = path.relative_to(currentPath)
        return PurePath("/").joinpath(path)
    except ValueError:
        print(f"Warning: Could not locate'{path}' in Relational Database File System Root ({ROOTFS_PATH} by default)")
        return None

def insertDataIntoDB(x, fs_db):
    print(f'Copying & Uploading: {x.as_posix()}')
    if x.is_symlink():
        SymbolicLink(fs_db, _to_db_path(x), create_if_missing=True, linked_path=_to_db_path(x.resolve(strict=False)))
    elif x.is_dir():
        Directory(fs_db, _to_db_path(x), create_if_missing=True)
        for x_child in x.iterdir():
            insertDataIntoDB(x_child, fs_db)
    elif x.is_file():
        db_file = RegularFile(fs_db, _to_db_path(x), create_if_missing=True, contents="")
        # NOTE: Unix doesn't return the original creator, so we just call the user the author
        # NOTE: Also API doesn't support changing the author
        # db_file.author = user
        user = User(fs_db, x.stat().st_uid, create_if_missing=True, user_name=x.owner())
        group = Group(fs_db, x.stat().st_gid, create_if_missing=True, group_name=x.group())
        db_file.owner = user
        db_file.group_owner = group
        db_file.permissions = x.stat().st_mode & (S_IRWXU | S_IRWXG | S_IRWXO)
        with x.open('rb') as f:
            db_file.write(f.readlines())
    else:
        print('Warning: Encountered unsupported file type', x.as_posix())

if __name__ == "__main__":
    parser = ArgumentParser(description="Upload files to your MySQL File System")
    parser.add_argument("custom_rdb_fs_root",
        help=f"The path realtive to {ROOTFS_PATH} to upload from, otherwise upload from {ROOTFS_PATH} by default",
        nargs='?',
        default='.')
    
    args = parser.parse_args()

    chdir(Path(ROOTFS_PATH).joinpath(args.custom_rdb_fs_root))
    insertDataIntoDB(Path(), FS_DB)
#!/usr/bin/env python3
from os import chdir
from pathlib import PurePath, Path
import pwd

from client_backend.fs_db_io import FSDatabase 
from client_backend.fs_db_file import *
from client_backend.fs_db_users import *

FS_DB = FSDatabase('.fs_db_rdbsh')
ROOTFS_PATH = Path('setup/rootfs')

# Should create root user (uid/gid = 0) & nobody user (uid/gid = 99)

def _to_db_path(path):
    try:
        if path.anchor:
            path.relative_to(ROOTFS_PATH.resolve())
        return PurePath("/").joinpath(path)
    except ValueError:
        print(f"Warning: Couldn't convert path {path} to a DB Path")
        return None

def insertDataIntoDB(x, fs_db):
    if x.is_dir():
        Directory(fs_db, _to_db_path(x), create_if_missing=True)
        for x_child in x.iterdir():
            insertDataIntoDB(x_child, fs_db)
    elif x.is_symlink():
        SymbolicLink(fs_db, _to_db_path(x), create_if_missing=True, linked_path=_to_db_path(x.resolve(strict=False)))
    elif x.is_file():
        db_file = RegularFile(fs_db, _to_db_path(x), create_if_missing=True, contents="")
        user = User(fs_db, x.stat().st_uid, create_if_missing=True, name=x.owner())
        author = User(fs_db, x.stat().st_creator, create_if_missing=True, name=pwd.getpwuid(x.stat().st_creator)[0])
        group = Group(fs_db, x.stat().st_gid, create_if_missing=True, name=x.group())
        db_file.author = author
        db_file.owner = user
        db_file.group_owner = group
        with x.open() as f:
            db_file.write(f.readlines())
    else:
        print('Warning: Encountered unsupported file type', x.resolve())

if __name__ == "__main__":
    chdir(ROOTFS_PATH)
    insertDataIntoDB(Path(), FS_DB)
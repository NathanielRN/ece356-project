from pathlib import Path
import pwd
from client_backend.fs_db_io import FSDatabase 
from fs_db_file import *
from fs_db_users import *

fs_db = FSDatabase('~/.fs_db_rdbsh')
# Should create root user (uid/gid = 0) & nobody user (uid/gid = 99)

def insertDataIntoDB(x, fs_db):
    if x.is_dir():
        Directory(fs_db, x, create_if_missing=True)
        for x_child in x.iterdir():
            insertDataIntoDB(x_child)
    elif x.is_symlink():
        SymbolicLink(fs_db, x, create_if_missing=True, linked_path=x.resolve(strict=False))
    elif x.is_file():
        db_file = RegularFile(fs_db, x, create_if_missing=True, contents="")
        user = User(fs_db, x.stat().st_uid, create_if_missing=True, name=x.owner())
        author = User(fs_db, x.stat().st_creator, create_if_missing=True, name=pwd.getpwuid(x.stat().st_creator)[0])
        group = Group(fs_db, x.stat().st_gid, create_if_missing=True, name=x.group())
        db_file.author = author
        db_file.owner = user
        db_file.group_owner = group
        with x.open() as f:
            while 1:
                line = f.readline()
                if not line:
                    break
                db_file.write(line)
    else:
        print('Error: Encountred unsupport file type', x.resolve())

insertDataIntoDB(Path('./rootfs'), fs_db)
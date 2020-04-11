"""Filesystem DB File Entities

Defines a set of entities and associated operations that can be performed
on the various file types in the file system
"""

from stat import S_IRWXU, S_IRWXG, S_IRWXO

from os import PathLike
from datetime import datetime

class File:
    def __init__(self, fs_db, path_or_id, create_if_missing=False):
        self.fs_db = fs_db
        if isinstance(path_or_id, (PathLike, str)):
            path = path_or_id
            self.fid = self.fs_db.find_file(path)
            if not self.exists() and create_if_missing:
                self.fid = self.fs_db.add_file(path)
        else:
            self.fid = path_or_id

    def exists(self):
        return self.fid is not None

    @property
    def permissions(self):
        return self.fs_db.get_permissions(self)

    @permissions.setter
    def permissions(self, permission_bits):
        self.fs_db.set_permissions(self, permission_bits)

    def check_access(self, user, operation):
        perm_bits = self.permissions
        if perm_bits.value & S_IRWXO & operation:
            return True
        if perm_bits.value & S_IRWXG & operation:
            if user.has_group(self.group_owner):
                return True
        if perm_bits.value & S_IRWXU & operation:
            if user == self.owner:
                return True
        return False

    @property
    def size(self):
        return self.fs_db.get_size(self)
    
    @property
    def full_name(self):
        return self.fs_db.get_full_name(self)

    @property
    def name(self):
        return self.fs_db.get_name(self)

    @name.setter
    def name(self, new_name):
        self.fs_db.set_name(self, new_name)

    @property
    def owner(self):
        return self.fs_db.get_owner(self)

    @owner.setter
    def owner(self, new_owner):
        self.fs_db.set_owner(self, new_owner)

    @property
    def group_owner(self):
        return self.fs_db.get_group_owner(self)

    @group_owner.setter
    def group_owner(self, new_owner):
        self.fs_db.set_group_owner(self, new_owner)

    @property
    def author(self):
        return self.fs_db.get_author(self)

    @property
    def created_date(self):
        return self.fs_db.get_created_date(self)


    @property
    def num_of_hard_links(self):
        return 1

    # TODO: Should allow arbitrary date changes maybe

    @property
    def modified_date(self):
        return self.fs_db.get_modified_date(self)

    @property
    def last_opened_date(self):
        return self.fs_db.get_accessed_date(self)

    def get_parent_directory(self):
        return self.fs_db.get_parent_dir(self)

    def open(self):
        self.fs_db.update_accessed_date(self)

    def modify(self):
        self.open()
        self.fs_db.update_modified_date(self)

    def move(self, new_directory):
        self.fs_db.set_parent_dir(self, new_directory)

    def remove(self):
        self.fs_db.remove(self)

    @property
    def type(self):
        return self.fs_db.get_type(self)

class SymbolicLink(File):
    def __init__(self, fs_db, path_or_id, create_if_missing=False, linked_path=None):
        if create_if_missing and linked_path is None:
            raise ValueError("Cannot create file without specified contents")
        super().__init__(fs_db, path_or_id, create_if_missing)
        # if type is file then there is generic and not one of the specific types
        if create_if_missing and self.fs_db.get_type(self) is File:
            self.fs_db.add_symbolic_link(self, linked_path)

    @property
    def size(self):
        return len(self.linked_path)

    @property
    def linked_path(self):
        return self.fs_db.get_linked_path(self)

    @linked_path.setter
    def linked_path(self, linked_path):
        self.fs_db.set_linked_path(self, linked_path)
        self.modify()

    def resolve(self):
        return self.fs_db.resolve_link(self)
        self.open()

class Directory(File):
    def __init__(self, fs_db, path_or_id, create_if_missing=False):
        super().__init__(fs_db, path_or_id, create_if_missing)
        # if type is file then there is generic and not one of the specific types
        if create_if_missing and self.fs_db.get_type(self) is File:
            self.fs_db.add_directory(self)

    @property
    def size(self):
        return 0

    def walk(self):
        yield from self.fs_db.get_children(self)
        self.open()

    def get_file(self, filename):
        child_file = self.fs_db.find_file_in_dir(self, filename)
        self.open()
        return self.fs_db.get_type(child_file)(self.fs_db, child_file) if child_file else None

    def get_children_like(self, pattern, search_subdirs=False):
        yield from self.fs_db.get_children_like(self, pattern, search_subdirs)

    def empty(self):
        for _ in self.walk():
            return False
        return True

    def remove(self, recursive=False):
        if not recursive and not self.empty():
            raise ValueError("Cannot remove non-empty directory")
        super().remove(self)

class RegularFile(File):
    def __init__(self, fs_db, path_or_id, create_if_missing=False, contents=None):
        if create_if_missing and contents is None:
            raise ValueError("Cannot create file without specified contents")
        super().__init__(fs_db, path_or_id, create_if_missing)
        # if type is file then there is generic and not one of the specific types
        if create_if_missing and self.fs_db.get_type(self) is File:
            self.fs_db.add_regular_file(self, contents)

    @property
    def num_of_hard_links(self):
        return self.fs_db.count_hardlinks(self)

    def hardlink(self, path):
        return self.fs_db.add_hardlink(self, path)

    def find_in_file(self, glob_pattern):
        yield from self.fs_db.find_in_file(self, glob_pattern)
        self.open()

    def is_system_utility(self):
        res = self.fs_db.check_if_utility(self)
        self.open()
        return res

    def readlines(self):
        yield from self.fs_db.readlines(self)
        self.open()

    def append(self, new_content):
        self.fs_db.append_content(self, new_content)
        self.modify()

    def write(self, new_content):
        self.fs_db.write_content(self, new_content)
        self.modify()

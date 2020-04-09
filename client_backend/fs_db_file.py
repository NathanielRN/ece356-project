"""Filesystem DB File Entities

Defines a set of entities and associated operations that can be performed
on the various file types in the file system
"""
class File:
    def __init__(self, fs_db, path, create_if_missing=False):
        self.fs_db = fs_db
        self.fid = self.fs_db.find_file(path)
        if not self.exists() and create_if_missing:
            self.fid = self.fs_db.add_file(path)

    def exists(self):
        return self.fid is not None

    @property
    def permissions(self):
        self.fs_db.get_permissions(self)

    @property.setter
    def permissions(self, permission_bits):
        self.fs_db.set_permissions(self, permission_bits)

    @property
    def size(self):
        self.fs_db.get_size(self)

    @property
    def name(self):
        self.fs_db.get_name(self)

    @property.setter
    def name(self):
        self.fs_db.set_name(self)

    @property
    def owner(self):
        self.fs_db.get_owner(self)

    @property.setter
    def owner(self, new_owner):
        self.fs_db.set_owner(self, new_owner)

    @property
    def group_owner(self):
        self.fs_db.get_group_owner(self)

    @property.setter
    def group_owner(self):
        self.fs_db.set_group_owner(self)

    @property
    def author(self):
        self.fs_db.get_author(self)

    @property
    def created_date(self):
        self.fs_db.get_created_date(self)

    @property
    def modified_date(self):
        self.fs_db.get_modified_date(self)

    @property
    def last_opened_date(self):
        self.fs_db.get_last_opened_date(self)

    def get_parent_directory(self):
        return self.fs_db.get_parent_dir(self)

    def get_parent_directory(self):
        return self.fs_db.get_parent_dir(self)

    def open():
        self.fs_db.update_last_opened_date(self)

    def modify():
        self.open()
        self.fs_db.update_last_modified_date(self)

class SymbolicLink(File):
    def __init__(self, fs_db, path, create_if_missing=False):
        if create_if_missing and contents is None:
            raise ValueError("Cannot create file without specified contents")
        super().__init__(fs_db, path, create_if_missing)
        # if type is file then there is generic and not one of the specific types
        if self.create_if_missing and self.fs_db.get_type(self) is File:
            self.fs_db.add_symbolic_link(self)

    def resolve(self):
        return self.fs_db.resolve_link(self)

class Directory(File):
    def __init__(self, fs_db, path, create_if_missing=False):
        if create_if_missing and contents is None:
            raise ValueError("Cannot create file without specified contents")
        super().__init__(fs_db, path, create_if_missing)
        # if type is file then there is generic and not one of the specific types
        if self.create_if_missing and self.fs_db.get_type(self) is File:
            self.fs_db.add_directory(self)

    def walk(self):
        yield from self.fs_db.get_all_files(self)

class RegularFile(File):
    def __init__(self, fs_db, path, create_if_missing=False, contents=None):
        if create_if_missing and contents is None:
            raise ValueError("Cannot create file without specified contents")
        super().__init__(fs_db, path, create_if_missing)
        # if type is file then there is generic and not one of the specific types
        if self.create_if_missing and self.fs_db.get_type(self) is File:
            self.fs_db.add_regular_file(self, contents)

    def hardlink(self, path):
        self.fs_db.add_hardlink(self, path)

    def find_in_file(self, glob_pattern):
        self.open()
        self.fs_db.search_file(self, glob_pattern)

    def readlines(self):
        yield from self.fs_db.get_lines(self)

    def append(self, new_content):
        self.fs_db.append_content(self, new_content)

    def write(self, new_content):
        self.fs_db.write_content(self, new_content)

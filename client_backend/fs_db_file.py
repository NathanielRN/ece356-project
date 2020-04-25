"""Filesystem DB File Entities

Defines a set of entities and associated operations that can be performed
on the various file types in the file system
"""

import errno
from stat import S_IRWXU, S_IRWXG, S_IRWXO


from os import PathLike, strerror
from datetime import datetime


class MissingFileError(IOError):
    def __init__(self, path):
        super().__init__(errno.ENOENT, strerror(errno.ENOENT), path)


class IncorrectFileTypeError(ValueError):
    pass

class TooManyLinkError(IOError):
    def __init__(self, path):
        super().__init__(errno.EMLINK, strerror(errno.EMLINK), path)
    pass


class File:
    MAX_LINK_DEPTH = 256
    def __new__(cls, fs_db, path_or_id, *args, create_if_missing=False, **kwargs):
        """
        Does error checking/reporting on instantiation of object

        Ensures that Python type of object == actual type of file
        """
        if not fs_db:
            raise ValueError("Did not provide filesystem DB connection")
        if create_if_missing and cls is File:
            raise ValueError("Attempting to create a file without a type")

        inst = super().__new__(cls)
        inst.fs_db = fs_db
        if isinstance(path_or_id, (PathLike, str)):
            path = path_or_id
            inst.fid = fs_db.find_file(path)
            if inst.fid is None and not create_if_missing:
                raise MissingFileError(path)
        else:
            inst.fid = path_or_id

        if create_if_missing:
            return inst

        inst_type = fs_db.get_type(inst.fid)
        if inst_type is None:
            raise ValueError(f"Invalid File ID = '{path_or_id}'")
        if not issubclass(inst_type, cls):
            raise IncorrectFileTypeError(f"Trying to create instance of type {cls.__name__} "
                             f"when file is {inst_type.__name__}. "
                             "Use generic types if type is unknown")
        return inst if inst_type is cls else inst_type(fs_db, inst.fid)

    def __init__(self, fs_db, path_or_id, create_if_missing=False):
        if not self.fid and isinstance(path_or_id, (PathLike, str)) and create_if_missing:
            path = path_or_id
            self.fid = self.fs_db.add_file(path)

    @staticmethod
    def resolve_to(fs_db, path, file_type):
        not_at_max_depth = File.MAX_LINK_DEPTH
        f = File(fs_db, path)
        if isinstance(f, file_type):
            return f
        while isinstance(f, SymbolicLink) and not_at_max_depth:
            f = f.resolve()
            if f is None:
                raise MissingFileError(path)
            not_at_max_depth -= 1
        
        if isinstance(f, SymbolicLink):
            raise TooManyLinkError(path)
        if not isinstance(f, file_type):
            raise IncorrectFileTypeError()
        return f
        

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
        own_type = self.fs_db.get_type(self)
        assert own_type is type(self)
        return own_type


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
        resolved = self.fs_db.resolve_link(self)
        self.open()
        return resolved


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
        return File(self.fs_db, child_file) if child_file else None

    def get_children_like(self, pattern, search_subdirs=False):
        yield from self.fs_db.get_children_like(self, pattern, search_subdirs)
        self.open()

    def empty(self):
        for _ in self.walk():
            return False
        return True

    def remove(self, recursive=False):
        for child in self.walk():
            if not recursive:
                raise ValueError("Cannot remove non-empty directory")
            if isinstance(child, Directory):
                child.remove(recursive=True)
            child.remove()
        super().remove()


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

    def remove(self):
        if self.num_of_hard_links > 1:
            self.fs_db.remove_hardlink(self)
        else:
            super().remove()

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

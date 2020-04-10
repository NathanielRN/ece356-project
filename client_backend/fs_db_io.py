"""Filesystem IO

Manages communication with the DB to perform IO
"""
from client_backend import shell_context

from client_backend.fs_db_file import *
from client_backend.fs_db_users import *

import yaml
from enum import Enum
from collections.abc import Sequence
from pathlib import PurePosixPath

import mysql.connector as MySQLConnection
from mysql.connector import errorcode as MySQLError
from mysql.connector.errors import ProgrammingError
from mysql.connector.cursor import MySQLCursor, MySQLCursorNamedTuple

class FSUserQuery(Enum):
    DB_QUERY_ADD_USER = (
        "INSERT INTO Users "
        "(userID, userName) "
        "VALUES (%(uid)s, %(user_name)s)"
    )
    DB_QUERY_ADD_GROUP = (
        "INSERT INTO UserGroups "
        "(groupID, groupName) "
        "VALUES (%(gid)s, %(group_name)s)"
    )
    DB_QUERY_DEL_USER = "DELETE FROM Users WHERE userID = %(uid)s"
    DB_QUERY_DEL_GROUP = "DELETE FROM Users WHERE userID = %(uid)s"
    DB_QUERY_ADD_GROUP_MEMBERSHIP = (
        "INSERT INTO GroupMemberships "
        "(groupID, userID) "
        "VALUES (%(gid)s, %(uid)s)"
    )
    DB_QUERY_REVOKE_GROUP_MEMBERSHIP = (
        "DELETE FROM GroupMemberships "
        "WHERE userID = %(uid)s AND groupID = %(gid)s"
    )
    # TODO: Expose these two queries
    DB_QUERY_GET_GROUP_MEMBERSHIP = (
        "SELECT groupID FROM GroupMemberships INNER JOIN UserGroups USING (groupID)"
        "WHERE userID = %(uid)s"
    )
    DB_QUERY_CHECK_GROUP_MEMBERSHIP = (
        "SELECT * FROM GroupMemberships "
        "WHERE userID = %(uid)s AND groupID = %(gid)s"
    )

    DB_QUERY_GET_USER_PROP = "SELECT {prop} FROM Users WHERE userID = %(uid)s"
    DB_QUERY_SET_USER_PROP = "UPDATE Users SET {prop}=%(value)s WHERE userID = %(uid)s"
    DB_QUERY_GET_GROUP_PROP = "SELECT {prop} FROM UserGroups WHERE groupID = %(gid)s"
    DB_QUERY_SET_GROUP_PROP = "UPDATE UserGroups SET {prop}=%(value)s WHERE groupID = %(gid)s"

class Permissions(Enum):
    READ = 0b001
    WRITE = 0b010
    EXECUTE = 0b100
    ALL = 0b111

    def for_user(self):
        return self.value << 6

    @classmethod
    def get_user(cls, perms):
        return (perms >> 6) & cls.ALL.value

    def for_group(self):
        return self.value << 3

    @classmethod
    def get_group(cls, perms):
        return (perms >> 3) & cls.ALL.value

    def for_anyone(self):
        return self.value

    @classmethod
    def get_anyone(cls, perms):
        return (perms) & cls.ALL.value

class FSGenericFileQuery(Enum):
    DEFAULT_DIRECTORY_PERMISSIONS = 0b111_101_101
    DB_QUERY_ADD_FILE = (
        "INSERT INTO Files "
        "(fileName, groupOwnerID, authorID, ownerID) "
        "VALUES (%(name)s, %(group)s, %(author)s, %(author)s)"
    )
    DB_QUERY_DEL_FILE = "DELETE FROM Files WHERE fileID = %(fid)s"

    DB_QUERY_GET_PARENT_DIRECTORY = (
        "SELECT parentDirectoryFileID "
        "FROM ParentDirectory INNER JOIN Files USING (fileID) "
        "WHERE fileID = %(fid)s"
    )

    DB_QUERY_GET_PROP = "SELECT {prop} FROM Files WHERE fileID = %(fid)s"
    DB_QUERY_SET_PROP = "UPDATE Files SET {prop}=%(value)s WHERE fileID = %(fid)s"

class FSRegularFileQuery(Enum):
    DB_QUERY_ADD_REG_FILE_METADATA = "INSERT INTO RegularFileMetadata (size) VALUES (0)"
    DB_QUERY_ADD_REG_FILE = (
        "INSERT INTO HardLinks "
        "(fileID, fileContentID) "
        "VALUES (%(fid)s, %(file_content_id)s)"
    )
    DB_QUERY_DEL_REG_FILE = (
        "DELETE FROM RegularFileMetadata WHERE fileContentID = (SELECT fileContentID FROM HardLinks WHERE fileID=%(fid)s)",
        "DELETE FROM HardLinks WHERE fileID = %(fid)s"
    )
    DB_QUERY_ADD_HARDLINK = (
        "INSERT INTO HardLinks "
        "SELECT %(link_fid)s AS fileID, "
        "(SELECT fileContentID FROM fileID = %(orig_fid)s)"
    )

    DB_QUERY_DEL_HARDLINK = (
        "DELETE FROM HardLinks WHERE fileID = %(fid)s"
    )

    DB_QUERY_ADD_FILE_CONTENT = (
        "REPLACE INTO FileContents "
        "SELECT fileContentID, %(line_no)s AS lineNumber, %(lineContent)s AS lineContent "
        "FROM HardLinks WHERE fileID=%(fid)s"
    )
    DB_QUERY_GET_FILE_LENGTH = (
        "SELECT MAX(lineNumber) "
        "FROM FileContents INNER JOIN RegularFileMetadata USING (fileContentID) "
        "INNER JOIN HardLinks USING (fileContentID) "
        "WHERE fileID = %(fid)s"
    )
    DB_QUERY_GET_FILE_CONTENT = (
        "SELECT lineNumber, lineContent "
        "FROM FileContents INNER JOIN RegularFileMetadata USING (fileContentID) "
        "INNER JOIN HardLinks USING (fileContentID) "
        "WHERE fileID = %(fid)s ORDER BY lineNumber"
    )

    DB_QUERY_GET_PROP = "SELECT {prop} FROM RegularFileMetadata INNER JOIN HardLinks USING (fileContentID) WHERE fileID = %(fid)s"
    DB_QUERY_SET_PROP = "UPDATE RegularFileMetadata SET {prop}=%(value)s WHERE fileContentID = (SELECT fileContentID FROM HardLinks WHERE fileID=%(fid)s)"


class FSDirectoryQuery(Enum):
    DB_QUERY_ADD_DIRECTORY = (
        "INSERT INTO Directories (fileID) VALUES (%(fid)s)"
    )
    DB_QUERY_DEL_DIRECTORY = (
        "DELETE FROM Directories WHERE fileID = %(fid)s"
    )
    DB_QUERY_ADD_CHILD_FILE = (
        "INSERT INTO ParentDirectory "
        "(fileID, parentDirectoryFileID) "
        "VALUES (%(fid)s, %(parent_fid)s)"
    )
    DB_QUERY_MOVE_CHILD_FILE = "UPDATE ParentDirectory SET parentDirectoryFileID = %(parent_fid)s WHERE fileID = %(fid)s"
    DB_QUERY_GET_FILE_WITH_PARENT = (
        "SELECT fileID "
        "FROM ParentDirectory INNER JOIN Files USING (fileID) "
        "WHERE parentDirectoryFileID = %(parent_fid)s AND fileName = %(name)s"
    )

    DB_QUERY_GET_PROP = "SELECT {prop} FROM Directories WHERE fileID = %(fid)s"
    DB_QUERY_SET_PROP = "UPDATE Directories SET {prop}=%(value)s WHERE fileID = %(fid)s"

    DB_QUERY_GET_ALL_FILES = (
        "SELECT fileID "
        "FROM ParentDirectory INNER JOIN Files USING (fileID) "
        "WHERE parentDirectoryFileID = %(parent_fid)s"
    )
    DB_QUERY_GET_ALL_FILES_LIKE = (
        "SELECT fileID "
        "FROM ParentDirectory INNER JOIN Files USING (fileID) "
        "WHERE parentDirectoryFileID = %(parent_fid)s AND fileName LIKE %(pattern)s"
    )

class FSSymbolicLinkQuery(Enum):
    DB_QUERY_ADD_SYMBOLIC_LINK = (
        "INSERT INTO SymbolicLinks (fileID, linkToFullPath) VALUES (%(fid)s, %(path)s)"
    )
    DB_QUERY_DEL_SYMBOLIC_LINK = (
        "DELETE FROM SymbolicLinks WHERE fileID = %(fid)s"
    )

    DB_QUERY_GET_PROP = "SELECT {prop} FROM SymbolicLinks WHERE fileID = %(fid)s"
    DB_QUERY_SET_PROP = "UPDATE SymbolicLinks SET {prop}=%(value)s WHERE fileID = %(fid)s"


class FSDatabase:
    ROOTDIR_ID = 1
    ROOTUSER_ID = 0
    NOBODYUSER_ID = 99
    def __init__(self, db_config_path):
        db_configs = dict()
        with open(db_config_path) as db_config_file:
            db_configs = yaml.load(db_config_file)
        self.connection = MySQLConnection.connect(**db_configs)
        self.cursor = None
    
    def __enter__(self):
        # self.cursor = MySQLCursorNamedTuple(self.connection)
        self.cursor = self.connection.cursor(named_tuple=True)
    
    def __exit__(self, type, value, traceback):
        self.cursor.close()
        self.cursor = None

    def _execute_queries(self, queries, params, format_params=None):
        format_params = format_params or {}
        if not isinstance(queries, Sequence):
            queries = (queries,)
        for query in queries:
            try:
                formatted_query = query.value.format(**format_params)
                self.cursor.execute(formatted_query, params)
            except ProgrammingError:
                print(">>>", query.value, params, format_params)
                raise
            except KeyError:
                print(">>>", query.value, params, format_params)
                raise
    """
    User/Group Creation
    """
    def add_user(self, uid, user_name):
        user_params = {"uid": uid, "user_name": user_name}
        group_params = {"gid": uid, "group_name": user_name}
        membership_params = {"uid": uid, "gid": uid}
        with self:
            # Add to group
            self._execute_queries(FSUserQuery.DB_QUERY_ADD_USER, user_params)
            self.connection.commit()
            # Transaction should fail if group already exists
            self._execute_queries(FSUserQuery.DB_QUERY_ADD_GROUP, group_params)
            self._execute_queries(FSUserQuery.DB_QUERY_ADD_GROUP_MEMBERSHIP, membership_params)
            self.connection.commit()

    def add_group(self, gid, group_name):
        group_params = {"gid": gid, "group_name": group_name}
        with self:
            self._execute_queries(FSUserQuery.DB_QUERY_ADD_GROUP, group_params)
            self.connection.commit()

    def add_membership(self, uid, gid):
        membership_params = {"uid": uid, "gid": gid}
        with self:
            # Add to group
            self._execute_queries(FSUserQuery.DB_QUERY_ADD_GROUP_MEMBERSHIP, membership_params)
            self.connection.commit()

    def get_user(self, uid):
        with self:
            self._execute_queries(FSUserQuery.DB_QUERY_GET_USER_PROP, {
                "uid": uid,
            }, format_params={"prop": "userID"})
            for (uid,) in self.cursor:
                return uid
            return None

    def get_group(self, gid):
        with self:
            self._execute_queries(FSUserQuery.DB_QUERY_GET_GROUP_PROP, {
                "gid": gid,
            }, format_params={"prop": "groupID"})
            for (gid,) in self.cursor:
                return gid
            return None


    """
    File helper
    """
    def get_type(self, file_entity):
        params = {"fid": file_entity.fid if isinstance(file_entity, File) else file_entity}
        format_params = {"prop": "fileID"}
        with self:
            self._execute_queries(FSDirectoryQuery.DB_QUERY_GET_PROP, params, format_params)
            for _ in self.cursor:
                return Directory
            print("=======")
            self._execute_queries(FSRegularFileQuery.DB_QUERY_GET_PROP, params, format_params)
            for _ in self.cursor:
                return RegularFile
            self._execute_queries(FSSymbolicLinkQuery.DB_QUERY_GET_PROP, params, format_params)
            for _ in self.cursor:
                return SymbolicLink
            self._execute_queries(FSGenericFileQuery.DB_QUERY_GET_PROP, params, format_params)
            for _ in self.cursor:
                return File
        return None

    def find_file_in_dir(self, parent_dir, filename):
        params = {"parent_fid": parent_dir, "name": filename}
        with self:
            self._execute_queries(FSDirectoryQuery.DB_QUERY_GET_FILE_WITH_PARENT, params)
            for file_info in self.cursor:
                return file_info.fileID
        return None

    def _resolve_relative_path(self, path):
        ctx_path = PurePosixPath("/")
        path = PurePosixPath(path)
        if path.parts[0] == "~":
            ctx_path = PurePosixPath(shell_context.HOME)
        else:
            ctx_path = PurePosixPath(shell_context.PWD)
        assert ctx_path.anchor
        # if path starts with /, will ignore ctx_path automatically
        return ctx_path.joinpath(path)
        
    def find_file(self, path, resolve_link=False):
        if PurePosixPath(path) == PurePosixPath("/"):
            self._verify_root()
            return FSDatabase.ROOTDIR_ID
        print("FINDING", path)
        path = self._resolve_relative_path(path)
        parent = self.find_file(path.parent, resolve_link=True)
        if parent is None:
            return None
        if path.name == "..":
            return parent

        parent_type = self.get_type(parent)
        if parent_type is not Directory:
            if parent_type is None:
                raise ValueError(f"Malformed path. '{path.parent}' does not exist")
            raise ValueError(f"Malformed path. Path element '{path.parent}' resolved to type '{parent_type}'")

        # TODO: Might wanna add this to API
        fid = self.find_file_in_dir(parent, path.name)

        if resolve_link and self.get_type(fid) is SymbolicLink:
            fid = self.resolve_link(SymbolicLink(self, fid)).fid
        return fid

    def resolve_link(self, link_entity):
        fid = self.find_file(link_entity.linked_path)
        if fid is None:
            return None
        return self.get_type(fid)(self, fid)

    """
    Creation/Deletion
    """
    def _verify_root(self):
        User(self, FSDatabase.ROOTUSER_ID, create_if_missing=True, user_name="root")
        if self.get_type(FSDatabase.ROOTDIR_ID) is None:
            self.add_file(PurePosixPath("/"))
        User(self, FSDatabase.NOBODYUSER_ID, create_if_missing=True, user_name="nobody")

    def add_file(self, path):
        author = User(self, shell_context.USER) or User(self, FSDatabase.ROOTUSER_ID) 
        group = Group(self, shell_context.USER) or Group(self, FSDatabase.ROOTUSER_ID)
        path = self._resolve_relative_path(path)
        params = {"name": path.name, "author": author.uid, "group": group.gid}
        if path != PurePosixPath("/"):
            parent_id = self.find_file(path.parent, resolve_link=True)
            if parent_id is None or self.get_type(parent_id) is not Directory:
                raise ValueError("Invalid path for file")
            params["parent_fid"] = parent_id
        #TODO: enforce that root dir is at ID=1
        with self:
            # Create file
            self._execute_queries(FSGenericFileQuery.DB_QUERY_ADD_FILE, params)
            params["fid"] = self.cursor.lastrowid
            # Add to folder
            if "parent_fid" in params:
                self._execute_queries(FSDirectoryQuery.DB_QUERY_ADD_CHILD_FILE, params)
            self.connection.commit()

    def add_directory(self, entity):
        params = {"fid": entity.fid}
        entity.permissions = FSGenericFileQuery.DEFAULT_DIRECTORY_PERMISSIONS
        with self:
            # Add to group
            self._execute_queries(FSDirectoryQuery.DB_QUERY_ADD_DIRECTORY, params)
            self.connection.commit()

    def add_regular_file(self, entity, contents):
        params = {"fid": entity.fid}
        with self:
            # Add to group
            self._execute_queries(FSRegularFileQuery.DB_QUERY_ADD_REG_FILE_METADATA, {})
            params["file_content_id"] = self.cursor.lastrowid
            self._execute_queries(FSRegularFileQuery.DB_QUERY_ADD_REG_FILE, params)
            if isinstance(contents, str):
                contents = contents.splitlines()
            for line_no, content in enumerate(contents, 1):
                content_params = {"line_no": line_no, "line_content": content}
                content_params.update(params)
                self._execute_queries(FSRegularFileQuery.DB_QUERY_ADD_FILE_CONTENT, content_params)
            self.connection.commit()

    def add_symbolic_link(self, entity, linked_path):
        params = {"fid": entity.fid, "path": linked_path}
        with self:
            # Add to group
            self._execute_queries(FSSymbolicLinkQuery.DB_QUERY_ADD_SYMBOLIC_LINK, params)
            self.connection.commit()

    def remove(self, entity):
        # TODO: Not needed by anyone and is kind of a pain to write so leaving for now
        raise NotImplementedError

    """
    Getters and Setters
    """
    def get_name(self, entity):
        with self:
            if isinstance(entity, User):
                self._execute_queries(FSUserQuery.DB_QUERY_GET_USER_PROP, {
                    "uid": entity.uid,
                }, format_params={"prop": "userName",})
            elif isinstance(entity, Group):
                self._execute_queries(FSUserQuery.DB_QUERY_GET_GROUP_PROP, {
                    "gid": entity.gid,
                }, format_params={"prop": "groupName",})
            elif isinstance(entity, File):
                self._execute_queries(FSGenericFileQuery.DB_QUERY_GET_PROP, {
                    "fid": entity.fid,
                }, format_params={"prop": "fileName",})
            for name in self.cursor:
                return name
            return None

    def set_name(self, entity, new_name):
        with self:
            if isinstance(entity, User):
                self._execute_queries(FSUserQuery.DB_QUERY_SET_USER_NAME, {
                    "uid": entity.uid,
                    "name": new_name
                })
            elif isinstance(entity, Group):
                self._execute_queries(FSUserQuery.DB_QUERY_SET_GROUP_NAME, {
                    "gid": entity.gid,
                    "name": new_name
                })
            elif isinstance(entity, File):
                self._execute_queries(FSGenericFileQuery.DB_QUERY_SET_PROP, {
                    "fid": entity.fid,
                    "value": new_name
                }, format_params={"prop": "name"})
            self.connection.commit()

    def get_owner(self, file_entity):
        with self:
            self._execute_queries(FSGenericFileQuery.DB_QUERY_GET_PROP, {
                "fid": file_entity.fid,
            }, format_params={"prop": "ownerID"})
            for (owner_id,) in self.cursor:
                return User(self, owner_id)
            return None

    def set_owner(self, file_entity, new_owner):
        with self:
            self._execute_queries(FSGenericFileQuery.DB_QUERY_SET_PROP, {
                "fid": file_entity.fid,
                "value": new_owner.uid
            }, format_params={"prop": "ownerID"})
            self.connection.commit()

    def get_group_owner(self, file_entity):
        with self:
            self._execute_queries(FSGenericFileQuery.DB_QUERY_GET_PROP, {
                "fid": file_entity.fid,
            }, format_params={"prop": "groupOwnerID"})
            for (owner_id,) in self.cursor:
                return Group(self, owner_id)
            return None

    def set_group_owner(self, file_entity, new_owner):
        with self:
            self._execute_queries(FSGenericFileQuery.DB_QUERY_SET_PROP, {
                "fid": file_entity.fid,
                "value": new_owner.gid
            }, format_params={"prop": "groupOwnerID"})
            self.connection.commit()

    def get_permissions(self, file_entity):
        with self:
            self._execute_queries(FSGenericFileQuery.DB_QUERY_GET_PROP, {
                "fid": file_entity.fid,
            }, format_params={"prop": "permissionBits"})
            for (perms,) in self.cursor:
                return perms
            return None

    def set_permissions(self, file_entity, permission_bits):
        with self:
            self._execute_queries(FSGenericFileQuery.DB_QUERY_SET_PROP, {
                "fid": file_entity.fid,
                "value": permission_bits
            }, format_params={"prop": "permissionBits"})
            self.connection.commit()

    def get_created_date(self, file_entity):
        with self:
            self._execute_queries(FSGenericFileQuery.DB_QUERY_GET_PROP, {
                "fid": file_entity.fid,
            }, format_params={"prop": "dateCreated"})
            for (perms,) in self.cursor:
                return perms
            return None

    def get_author(self, file_entity):
        with self:
            self._execute_queries(FSGenericFileQuery.DB_QUERY_GET_PROP, {
                "fid": file_entity.fid,
            }, format_params={"prop": "authorID"})
            for (author,) in self.cursor:
                return User(self, author)
            return None

    def get_modified_date(self, file_entity):
        query_map = {
            File: FSGenericFileQuery,
            Directory: FSDirectoryQuery,
            RegularFile: FSRegularFileQuery,
            SymbolicLink: FSSymbolicLinkQuery,
        }
        query_type = query_map[file_entity.type()]
        with self:
            self._execute_queries(query_type.DB_QUERY_GET_PROP, {
                "fid": file_entity.fid,
            }, format_params={"prop": "dateModified"})
            for (date,) in self.cursor:
                return date
            return None

    def set_modified_date(self, file_entity, date_modified):
        query_map = {
            File: FSGenericFileQuery,
            Directory: FSDirectoryQuery,
            RegularFile: FSRegularFileQuery,
            SymbolicLink: FSSymbolicLinkQuery,
        }
        query_type = query_map[file_entity.type()]
        with self:
            self._execute_queries(query_type.DB_QUERY_SET_PROP, {
                "fid": file_entity.fid,
                "value": date_modified
            }, format_params={"prop": "dateModified",})
            self.connection.commit()

    def get_accessed_date(self, file_entity):
        query_map = {
            File: FSGenericFileQuery,
            Directory: FSDirectoryQuery,
            RegularFile: FSRegularFileQuery,
            SymbolicLink: FSSymbolicLinkQuery,
        }
        query_type = query_map[file_entity.type()]
        with self:
            self._execute_queries(query_type.DB_QUERY_GET_PROP, {
                "fid": file_entity.fid,
            }, format_params={"prop": "dateLastOpened"})
            for (date,) in self.cursor:
                return date
            return None

    def set_accessed_date(self, file_entity, accessed_date):
        query_map = {
            File: FSGenericFileQuery,
            Directory: FSDirectoryQuery,
            RegularFile: FSRegularFileQuery,
            SymbolicLink: FSSymbolicLinkQuery,
        }
        query_type = query_map[file_entity.type()]
        with self:
            self._execute_queries(query_type.DB_QUERY_SET_PROP, {
                "fid": file_entity.fid,
                "value": accessed_date
            }, format_params={"prop": "dateLastOpened"})
            self.connection.commit()

    def get_parent_dir(self, file_entity):
        with self:
            self._execute_queries(FSGenericFileQuery.DB_QUERY_GET_PARENT_DIR, {
                "fid": file_entity.fid
            })
            for (parent_fid,) in self.cursor:
                return Directory(self, parent_fid)
            return None

    def set_parent_dir(self, file_entity, parent_dir):
        with self:
            self._execute_queries(FSGenericFileQuery.DB_QUERY_MOVE_CHILD_FILE, {
                "fid": file_entity.fid,
                "parent_fid": parent_dir.fid
            })
            self.connection.commit()

    def get_linked_path(self, link_entity):
        with self:
            self._execute_queries(FSSymbolicLinkQuery.DB_QUERY_GET_PROP, {
                "fid": link_entity.fid,
            }, format_params={"prop": "linkToFullPath"})
            for (link_path,) in self.cursor:
                return link_path
            return None

    def set_linked_path(self, link_entity, new_path):
        with self:
            self._execute_queries(FSSymbolicLinkQuery.DB_QUERY_SET_PROP, {
                "fid": link_entity.fid,
                "value": new_path,
            }, format_params={"prop": "linkToFullPath"})
            self.connection.commit()

    """
    Operations on file
    """
    def get_all_files(self, directory_entity):
        params = {"parent_fid": directory_entity.fid}
        files = []
        with self:
            self._execute_queries(FSDirectoryQuery.DB_QUERY_GET_ALL_FILES, params)
            files = [fid for (fid,) in self.cursor]
        for fid in files:
            yield self.get_type(fid)(self, fid)

    def get_all_files_like(self, directory_entity, pattern):
        params = {"parent_fid": directory_entity.fid, "pattern": pattern}
        files = []
        with self:
            self._execute_queries(FSDirectoryQuery.DB_QUERY_GET_ALL_FILES_LIKE, params)
            files = [fid for (fid,) in self.cursor]
        for fid in files:
            yield self.get_type(fid)(self, fid)
        subdirs = []
        with self:
            self._execute_queries(FSDirectoryQuery.DB_QUERY_GET_SUBDIRECTORIES, params)
            subdirs = [fid for (fid,) in self.cursor]
        for subdir in subdirs:
            yield from self.get_all_files_like(directory_entity, pattern)

    def write_content(self, file_entity, new_content):
        params = {"fid": file_entity.fid}
        with self:
            if isinstance(new_content, str):
                contents = new_content.splitlines()
            contents = new_content
            for line_no, content in enumerate(contents, 1):
                content_params = {"line_no": line_no, "line_content": content}
                content_params.update(params)
                self._execute_queries(FSRegularFileQuery.DB_QUERY_ADD_FILE_CONTENT, content_params)
            self.connection.commit()

    def append_content(self, file_entity, new_content):
        params = {"fid": file_entity.fid}
        with self:
            self._execute_queries(FSRegularFileQuery.DB_QUERY_GET_FILE_LENGTH, params)
            start_length = 1
            for length in self.cursor:
                start_length = length
            if isinstance(new_content, str):
                contents = new_content.splitlines()
            contents = new_content
            for line_no, content in enumerate(contents, line_no + 1):
                content_params = {"line_no": line_no, "line_content": content}
                content_params.update(params)
                self._execute_queries(FSRegularFileQuery.DB_QUERY_ADD_FILE_CONTENT, content_params)
            self.connection.commit()

    def readlines(self, file_entity):
        with self:
            self._execute_queries(FSRegularFileQuery.DB_QUERY_GET_FILE_CONTENT, {
                "fid": file_entity.fid
            })
            for _, line_content in self.cursor:
                yield line_content

    def find_in_file(self, file_entity, pattern):
        with self:
            self._execute_queries(FSRegularFileQuery.DB_QUERY_FIND_IN_FILE_CONTENT, {
                "fid": file_entity.fid,
                "pattern": pattern
            })
            for line_no, line_content in self.cursor:
                yield line_no, line_content

    def add_hardlink(self, file_entity, path):
        hardlink_file = File(self, path, create_if_missing=True)
        params = {"orig_fid": file_entity.fid, "link_fid": hardlink_file.fid}
        with self:
            self._execute_queries(FSRegularFileQuery.DB_QUERY_ADD_HARDLINK, params)
            self.connection.commit()

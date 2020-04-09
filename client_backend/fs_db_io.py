"""Filesystem IO

Manages communication with the DB to perform IO
"""
import shell_context

from fs_db_file import *
from fs_db_users import *

import yaml
from enum import Enum
from collections.abc import Sequence
from pathlib import PurePosixPath

import mysql.connector as MySQLConnection
from mysql.connector import errorcode as MySQLError
from mysql.connector.cursor import MySQLCursor, MySQLCursorNamedTuple

class FSUserQuery(Enum):
    DB_QUERY_ADD_USER = (
        "INSERT INTO Users "
        "(userID, userName) "
        "VALUES (%(uid)s, %(user_name)s)"
    )
    DB_QUERY_ADD_GROUP = (
        "INSERT INTO Groups "
        "(groupID, groupName) "
        "VALUES (%(gid)s, %(group_name)s)"
    )
    DB_QUERY_DEL_USER = "DELETE FROM Users WHERE userID = %(uid)s"
    DB_QUERY_DEL_GROUP = "DELETE FROM Users WHERE userID = %(uid)s"
    DB_QUERY_ADD_GROUP_MEMBERSHIP = (
        "INSERT INTO GroupMembership "
        "(groupID, userID) "
        "VALUES (%(gid)s, %(uid)s)"
    )
    DB_QUERY_REVOKE_GROUP_MEMBERSHIP = (
        "DELETE FROM GroupMembership "
        "WHERE userID = %(uid)s AND groupID = %(gid)s"
    )

class Permissions(Enum):
    READ = 0b001
    WRITE = 0b010
    EXECUTE = 0b100

    def for_user(self):
        return self.value << 6

    def for_group(self):
        return self.value << 3

    def for_anyone(self):
        return self.value

class FSGenericFileQuery(Enum):
    DEFAULT_DIRECTORY_PERMISSIONS = 0b111_101_101
    DB_QUERY_ADD_FILE = (
        "INSERT INTO Files "
        "(fileName, groupOwnerID, authorID, ownerID) "
        "VALUES (%(name)s, %(group)s, %(author)s, %(author)s"
    )
    DB_QUERY_DEL_FILE = "DELETE FROM Files WHERE fileID = %(fid)s"

class FSRegularFileQuery(Enum):
    DB_QUERY_ADD_REG_FILE_METADATA = "INSERT INTO RegularFileMetadata (size) VALUES (0)"
    DB_QUERY_ADD_REG_FILE = (
        "INSERT INTO Hardlinks "
        "(fileID, fileContentID) "
        "VALUES (%(fid)s, %(file_content_id)s"
    )
    DB_QUERY_DEL_REG_FILE = (
        "DELETE FROM RegularFileMetadata WHERE fileContentID = (SELECT fileContentID FROM Hardlinks WHERE fileID=%(fid)s)",
        "DELETE FROM Hardlinks WHERE fileID = %(fid)s"
    )
    DB_QUERY_ADD_HARDLINK = (
        "INSERT INTO Hardlinks "
        "SELECT %(link_fid)s AS fileID, "
        "(SELECT fileContentID FROM fileID = %(orig_fid)s)"
    )

    DB_QUERY_DEL_HARDLINK = (
        "DELETE FROM Hardlinks WHERE fileID = %(fid)s"
    )
    DB_QUERY_GET_FILE_WITH_PARENT = (
        "SELECT fileID "
        "FROM ParentDirectory INNER JOIN Files USING (fileID) "
        "WHERE parentDirectoryFileID = %(parent_fid)s AND fileName = %(name)s"
    )

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

class FSSymbolicLinkQuery(Enum):
    DB_QUERY_ADD_SYMBOLIC_LINK = (
        "INSERT INTO SymbolicLinks (fileID, linkToFullPath) VALUES (%(fid)s, %(path)s)"
    )
    DB_QUERY_DEL_SYMBOLIC_LINK = (
        "DELETE FROM SymbolicLinks WHERE fileID = %(fid)s"
    )

class FSDatabase:
    ROOTDIR_ID = 1
    def __init__(self, db_config_path):
        db_configs = yaml.load(db_config_path)
        self.connection = MySQLConnection.connect(**db_configs)
        self.cursor = None
    
    def __enter__(self):
        self.cursor = MySQLCursorNamedTuple(self.connection)
    
    def __exit__(self):
        self.cursor.close()
        self.cursor = None

    def _execute_queries(self, queries, params):
        queries = queries.value
        if not isinstance(queries, Sequence):
            queries = (queries,)
        for query in queries:
            self.cursor.execute(query.value, params)

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

    def get_name(self, entity):
        with self:
            if isinstance(entity, User):
                self._execute_queries(FSUserQuery.DB_QUERY_GET_USER_NAME, {
                    "uid": entity.uid
                })
            elif isinstance(entity, Group):
                self._execute_queries(FSUserQuery.DB_QUERY_GET_GROUP_NAME, {
                    "gid": entity.gid
                })
            elif isinstance(entity, File):
                self._execute_queries(FSGenericFileQuery.DB_QUERY_GET_NAME, {
                    "fid": entity.fid
                })
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
                self._execute_queries(FSGenericFileQuery.DB_QUERY_SET_NAME, {
                    "fid": entity.fid,
                    "name": new_name
                })
            self.connection.commit()

    def remove(self, entity):
        # Most are simple, regular files/hardlinks need special attention
        raise NotImplementedError

    def get_type(self, file_entity):
        params = {"fid": file_entity.fid if isinstance(file_entity, File) else file_entity}
        with self:
            self._execute_query(FSDirectoryQuery.DB_QUERY_GET_DIRECTORY, params)
            for (fid,) in self.cursor:
                return Directory
            self._execute_query(FSRegularFileQuery.DB_QUERY_GET_REGULAR_FILE, params)
            for (fid,) in self.cursor:
                return RegularFile
            self._execute_query(FSSymbolicLinkQuery.DB_QUERY_GET_SYMBOLIC_LINK, params)
            for (fid, _) in self.cursor:
                return SymbolicLink
        return File

    def find_file_in_dir(self, parent_dir, filename):
        params = {"parent_fid": parent_dir, "name": filename}
        with self:
            self._execute_query(FSGenericFileQuery.DB_QUERY_GET_FILE_WITH_PARENT, params)
            for file_info in self.cursor:
                return file_info.fileID
        return None

    def _resolve_relative_path(self, path):
        ctx_path = PurePosixPath("/")
        if path.startswith("~/"):
            ctx_path = PurePosixPath(shell_context.HOME)
        else:
            ctx_path = PurePosixPath(shell_context.PWD)
        assert ctx_path.anchor
        # if path starts with /, will ignore ctx_path automatically
        return ctx_path.joinpath(path)
        
    def find_file(self, path, resolve_link=False):
        if path == "/":
            return FSDatabase.ROOTDIR_ID
        path = self._resolve_relative_path(path)
        parent = find_file(path.parent, resolve_link=True)
        if parent is None:
            return None
        if path.name == "..":
            return parent

        if self.find_type(parent) is not Directory:
            raise ValueError("Malformed path")

        # TODO: Might wanna add this to API
        fid = self.find_file_in_dir(parent, path.name)

        if resolve_link and self.find_type(fid) is SymbolicLink:
            fid = self.resolve_link(parent)
        return fid

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
        with self:
            # Create file
            self._execute_query(FSGenericFileQuery.DB_QUERY_ADD_FILE, params)
            params["fid"] = self.cursor.lastrowid
            # Add to folder
            if "parent_fid" in params:
                self._execute_query(FSDirectoryQuery.DB_QUERY_ADD_CHILD_FILE, params)

    def add_directory(self, entity):
        params = {"fid": entity.fid}
        with self:
            entity.permissions = FSGenericFileQuery.DEFAULT_DIRECTORY_PERMISSIONS
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

    def set_owner(self, file_entity, user_entity):
        raise NotImplementedError

    def set_group_owner(self, file_entity, user_entity):
        raise NotImplementedError

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
        raise NotImplementedError

    def find_in_file(self, file_entity):
        raise NotImplementedError

    def add_hardlink(self, file_entity, path):
        hardlink_file = File(self, path, create_if_missing=True)
        params = {"orig_fid": file_entity.fid, "link_fid": hardlink_file.fid}
        with self:
            self._execute_queries(FSRegularFileQuery.DB_QUERY_ADD_HARDLINK, params)
            self.connection.commit()

"""Filesystem IO

Manages communication with the DB to perform IO
"""
from client_backend import shell_context

from client_backend.fs_db_file import *
from client_backend.fs_db_users import *

import stat
import yaml
import struct
from enum import Enum
from pathlib import PurePosixPath

import mysql.connector as MySQLConnection
from mysql.connector import errorcode as MySQLError
from mysql.connector.errors import ProgrammingError
from mysql.connector.cursor import MySQLCursor, MySQLCursorNamedTuple
from mysql.connector.constants import SQLMode

class FSUserQuery(Enum):
    DB_QUERY_ADD_USER = (
        "INSERT INTO Users "
        "(userID, userName) "
        "VALUES ({use_uid}, %(user_name)s)"
    )
    DB_QUERY_ADD_GROUP = (
        "INSERT INTO UserGroups "
        "(groupID, groupName) "
        "VALUES (%(gid)s, %(group_name)s)"
    )

    DB_QUERY_DEL_USER = (
        "DELETE FROM GroupMemberships WHERE userID = %(uid)s",
        "DELETE FROM Users WHERE userID = %(uid)s"
    )
    DB_QUERY_DEL_GROUP = (
        "DELETE FROM GroupMemberships WHERE groupID = %(gid)s",
        "DELETE FROM UserGroups WHERE groupID = %(gid)s"
    )
    DB_QUERY_ADD_GROUP_MEMBERSHIP = (
        "INSERT INTO GroupMemberships "
        "(groupID, userID) "
        "VALUES (%(gid)s, %(uid)s)"
    )
    DB_QUERY_REVOKE_GROUP_MEMBERSHIP = (
        "DELETE FROM GroupMemberships "
        "WHERE userID = %(uid)s AND groupID = %(gid)s"
    )
    DB_QUERY_CHECK_GROUP_MEMBERSHIP = (
        "SELECT * FROM GroupMemberships "
        "WHERE userID = %(uid)s AND groupID = %(gid)s"
    )
    DB_QUERY_GET_ALL_GROUPS = (
        "SELECT groupID FROM GroupMemberships "
        "WHERE userID = %(uid)s"
    )

    DB_QUERY_GET_USER_ID_BY_PROP = "SELECT userID FROM Users WHERE {prop} = %(prop_value)s"
    DB_QUERY_GET_USER_PROP = "SELECT {prop} FROM Users WHERE userID = %(uid)s"
    DB_QUERY_SET_USER_PROP = "UPDATE Users SET {prop}=%(value)s WHERE userID = %(uid)s"
    DB_QUERY_GET_GROUP_ID_BY_PROP = "SELECT groupID FROM UserGroups WHERE {prop} = %(prop_value)s"
    DB_QUERY_GET_GROUP_PROP = "SELECT {prop} FROM UserGroups WHERE groupID = %(gid)s"
    DB_QUERY_SET_GROUP_PROP = "UPDATE UserGroups SET {prop}=%(value)s WHERE groupID = %(gid)s"

class PermissionBits:
    READ_OPERATION = stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH
    WRITE_OPERATION = stat.S_IWUSR | stat.S_IWGRP | stat.S_IWOTH
    EXECUTE_OPERATION = stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH
    def __init__(self, permission_bits_string):
        self.value = struct.unpack(">H", permission_bits_string)[0]

    @staticmethod
    def as_bytes(value):
        return struct.pack(">H", value)

    def __str__(self):
        perm_string = ''
        PERM_TYPES = [
            PermissionBits.READ_OPERATION,
            PermissionBits.WRITE_OPERATION,
            PermissionBits.EXECUTE_OPERATION,
        ]
        PERM_SCOPES = [
            stat.S_IRWXU,
            stat.S_IRWXG,
            stat.S_IRWXO,
        ]

        PERM_TYPE_TO_STR = {
            PermissionBits.READ_OPERATION: "r",
            PermissionBits.WRITE_OPERATION: "w",
            PermissionBits.EXECUTE_OPERATION: "x",
        }

        for scope in PERM_SCOPES:
            for perm_type in PERM_TYPES:
                if self.value & scope & perm_type:
                    perm_string += PERM_TYPE_TO_STR[perm_type]
                else:
                    perm_string += "-"
        return perm_string

class FSGenericFileQuery(Enum):
    DEFAULT_DIRECTORY_PERMISSIONS = 0b001_101_101
    DB_QUERY_ADD_FILE = (
        "INSERT INTO Files "
        "(fileID, fileName, groupOwnerID, authorID, ownerID) "
        "VALUES ({use_fid}, %(name)s, %(group)s, %(author)s, %(author)s)"
    )
    DB_QUERY_DEL_FILE = (
        "DELETE FROM ParentDirectory WHERE fileID = %(fid)s",
        "DELETE FROM Files WHERE fileID = %(fid)s",
    )

    DB_QUERY_GET_PARENT_DIR = (
        "SELECT parentDirectoryFileID "
        "FROM ParentDirectory INNER JOIN Files USING (fileID) "
        "WHERE fileID = %(fid)s"
    )

    DB_QUERY_GET_PROP = "SELECT {prop} FROM Files WHERE fileID = %(fid)s"
    DB_QUERY_SET_PROP = "UPDATE Files SET {prop}=%(value)s WHERE fileID = %(fid)s"

class FSRegularFileQuery(Enum):
    # NOTE: size is calculate-able we may want to setup either a trigger/view for keeping this up to date
    DB_QUERY_ADD_REG_FILE_METADATA = "INSERT INTO RegularFileMetadata (size) VALUES (%(size)s)"
    DB_QUERY_ADD_REG_FILE = (
        "INSERT INTO HardLinks "
        "(fileID, fileContentID) "
        "VALUES (%(fid)s, %(file_content_id)s)"
    )
    DB_QUERY_DELETE_ALL_FILE_CONTENT = (
        "DELETE FROM FileContents "
        "WHERE fileContentID = (SELECT fileContentID FROM HardLinks WHERE fileID = %(fid)s)"
    )
    DB_QUERY_DEL_REG_FILE = (
        DB_QUERY_DELETE_ALL_FILE_CONTENT,
        "DELETE FROM HardLinks WHERE fileID = %(fid)s",
        "DELETE FROM RegularFileMetadata WHERE fileContentID = (SELECT fileContentID FROM HardLinks WHERE fileID=%(fid)s)",
    )
    DB_QUERY_ADD_HARDLINK = (
        "INSERT INTO HardLinks "
        "SELECT %(link_fid)s AS fileID, "
        "(SELECT fileContentID FROM fileID = %(orig_fid)s)"
    )

    DB_QUERY_COUNT_HARDLINKS = (
        "SELECT COUNT(fileID) AS hardLinkCount FROM HardLinks "
        "WHERE fileContentID = (SELECT fileContentID FROM HardLinks WHERE fileID = %(fid)s)"
    )

    DB_QUERY_DEL_HARDLINK = (
        "DELETE FROM HardLinks WHERE fileID = %(fid)s"
    )

    DB_QUERY_ADD_FILE_CONTENT = (
        # Allow this command to replace existing lines
        "REPLACE INTO FileContents "
        "SELECT fileContentID, %(line_no)s AS lineNumber, %(line_content)s AS lineContent "
        "FROM HardLinks WHERE fileID=%(fid)s"
    )
    DB_QUERY_GET_LAST_LINE = (
        "SELECT lineNumber, lineContent "
        "FROM FileContents INNER JOIN RegularFileMetadata USING (fileContentID) "
        "INNER JOIN HardLinks USING (fileContentID) "
        "WHERE fileID = %(fid)s AND "
        "NOT EXISTS ("
        "SELECT * "
        "FROM (FileContents AS B) INNER JOIN (RegularFileMetadata AS C) USING (fileContentID) "
        "INNER JOIN (HardLinks AS D) USING (fileContentID) "
        "WHERE B.lineNumber > FileContents.lineNumber AND "
        "D.fileID = HardLinks.fileID"
        ")"
    )
    DB_QUERY_CHECK_FOR_BANG = (
        "SELECT fileID "
        "FROM FileContents INNER JOIN HardLinks USING (fileContentID) "
        "WHERE lineNumber = 1 AND fileID = %(fid)s AND lineContent LIKE '#!rdbsh%\\n'"
    )
    DB_QUERY_GET_FILE_CONTENT = (
        "SELECT lineNumber, lineContent "
        "FROM FileContents INNER JOIN HardLinks USING (fileContentID) "
        "WHERE fileID = %(fid)s ORDER BY lineNumber"
    )
    DB_QUERY_FIND_IN_FILE_CONTENT = (
        "SELECT lineNumber, lineContent "
        "FROM FileContents INNER JOIN HardLinks USING (fileContentID) "
        "WHERE fileID = %(fid)s AND REGEXP_LIKE(lineContent, %(pattern)s, 'c') "
        "ORDER BY lineNumber"
    )

    DB_QUERY_GET_PROP = "SELECT {prop} FROM RegularFileMetadata INNER JOIN HardLinks USING (fileContentID) WHERE fileID = %(fid)s"
    DB_QUERY_SET_PROP = "UPDATE RegularFileMetadata SET {prop}=%(value)s WHERE fileContentID = (SELECT fileContentID FROM HardLinks WHERE fileID=%(fid)s)"
    DB_QUERY_INCREMENT_PROP = "UPDATE RegularFileMetadata SET {prop} = {prop} + %(value)s WHERE fileContentID = (SELECT fileContentID FROM HardLinks WHERE fileID=%(fid)s)"

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

    DB_QUERY_GET_SUBDIRECTORIES = (
        "SELECT fileID "
        "FROM ParentDirectory INNER JOIN Files USING (fileID) "
        "INNER JOIN Directories USING (fileID) "
        "WHERE parentDirectoryFileID = %(fid)s"
    )

    DB_QUERY_GET_PROP = "SELECT {prop} FROM Directories WHERE fileID = %(fid)s"
    DB_QUERY_SET_PROP = "UPDATE Directories SET {prop}=%(value)s WHERE fileID = %(fid)s"

    DB_QUERY_GET_CHILDREN = (
        "SELECT fileID "
        "FROM ParentDirectory INNER JOIN Files USING (fileID) "
        "WHERE parentDirectoryFileID = %(fid)s"
    )
    DB_QUERY_GET_CHILDREN_LIKE = (
        "SELECT fileID "
        "FROM ParentDirectory INNER JOIN Files USING (fileID) "
        "WHERE parentDirectoryFileID = %(fid)s AND fileName LIKE %(pattern)s"
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
        self.connection.sql_mode = [*self.connection.sql_mode.split(","), SQLMode.NO_AUTO_VALUE_ON_ZERO]
        self.cursor = None
        self.use_raw = False
    
    def __enter__(self):
        # self.cursor = MySQLCursorNamedTuple(self.connection)
        params = dict(named_tuple=True) if not self.use_raw else dict(raw=True)
        self.cursor = self.connection.cursor(**params)
    
    def __exit__(self, type, value, traceback):
        if self.cursor:
            self.cursor.close()
        self.cursor = None
        self.use_raw = False

    def _execute_queries(self, queries_enum, params, format_params=None):
        format_params = format_params or {}
        if not isinstance(queries_enum.value, tuple):
            queries = (queries_enum.value,)
        else:
            queries = queries_enum.value
        for query in queries:
            try:
                formatted_query = query.format(**format_params)
                self.cursor.execute(formatted_query, params)
            except Exception:
                print(">>>", query, params, format_params)
                raise
    """
    User/Group Creation
    """
    def add_user(self, uid, user_name):
        user_params = {"uid": uid, "user_name": user_name}
        format_params = {"use_uid": "%(uid)s" if uid is not None else "NULL"}
        with self:
            # Add to group
            self._execute_queries(FSUserQuery.DB_QUERY_ADD_USER, user_params, format_params=format_params)
            self.connection.commit()
            uid = self.cursor.lastrowid
        return uid

    def add_group(self, gid, group_name):
        group_params = {"gid": gid, "group_name": group_name}
        format_params = {"use_gid": "%(gid)s" if gid is not None else "NULL"}
        with self:
            self._execute_queries(FSUserQuery.DB_QUERY_ADD_GROUP, group_params, format_params)
            self.connection.commit()
            gid = self.cursor.lastrowid
        return gid

    def add_membership(self, user_entity, group_entity):
        membership_params = {"uid": user_entity.uid, "gid": group_entity.gid}
        with self:
            # Add to group
            self._execute_queries(FSUserQuery.DB_QUERY_ADD_GROUP_MEMBERSHIP, membership_params)
            self.connection.commit()

    def revoke_membership(self, user_entity, group_entity):
        membership_params = {"uid": user_entity.uid, "gid": group_entity.gid}
        with self:
            # Remove from group
            self._execute_queries(FSUserQuery.DB_QUERY_REVOKE_GROUP_MEMBERSHIP, membership_params)
            self.connection.commit()

    def get_user(self, uid_or_user_name):
        with self:
            self._execute_queries(FSUserQuery.DB_QUERY_GET_USER_ID_BY_PROP, {
                "prop_value": uid_or_user_name,
            }, format_params={"prop": "userID" if isinstance(uid_or_user_name, int) else "userName"})

            uid = self.cursor.fetchone()
            return uid[0] if uid else None

    def get_group(self, gid_or_group_name):
        with self:
            self._execute_queries(FSUserQuery.DB_QUERY_GET_GROUP_ID_BY_PROP, {
                "prop_value": gid_or_group_name,
            }, format_params={"prop": "groupID"  if isinstance(gid_or_group_name, int) else "groupName"})
            gid = self.cursor.fetchone()
            return gid[0] if gid else None


    """
    User Helper
    """
    def get_groups(self, user_entity):
        with self:
            self._execute_queries(FSUserQuery.DB_QUERY_GET_ALL_GROUPS, {"uid": user_entity.uid})
            groups = [gid for (gid,) in self.cursor]
        for gid in groups:
            yield Group(self, gid=gid)

    def check_group_membership(self, user_entity, group_entity):
        with self:
            self._execute_queries(FSUserQuery.DB_QUERY_CHECK_GROUP_MEMBERSHIP, {
                "uid": user_entity.uid,
                "gid": group_entity.gid
            })
            return bool(self.cursor.fetchone())


    """
    File helper
    """
    def get_type(self, file_entity):
        params = {"fid": file_entity.fid if isinstance(file_entity, File) else file_entity}
        format_params = {"prop": "fileID"}
        with self:
            self._execute_queries(FSDirectoryQuery.DB_QUERY_GET_PROP, params, format_params)
            if self.cursor.fetchone():
                return Directory
            self._execute_queries(FSRegularFileQuery.DB_QUERY_GET_PROP, params, format_params)
            if self.cursor.fetchone():
                return RegularFile
            self._execute_queries(FSSymbolicLinkQuery.DB_QUERY_GET_PROP, params, format_params)
            if self.cursor.fetchone():
                return SymbolicLink
            self._execute_queries(FSGenericFileQuery.DB_QUERY_GET_PROP, params, format_params)
            if self.cursor.fetchone():
                return File
        return None

    def find_file_in_dir(self, parent_dir, filename):
        params = {"fid": parent_dir.fid if isinstance(parent_dir, Directory) else parent_dir, "pattern": filename}
        with self:
            self._execute_queries(FSDirectoryQuery.DB_QUERY_GET_CHILDREN_LIKE, params)
            file_info = self.cursor.fetchone()
            return file_info.fileID if file_info else None

    def _resolve_relative_path(self, path):
        ctx_path = PurePosixPath("/")
        path = PurePosixPath(path)
        if path.parts and path.parts[0] == "~":
            ctx_path = PurePosixPath(shell_context.HOME)
        else:
            ctx_path = PurePosixPath(shell_context.PWD)

        assert ctx_path.anchor
        # if path starts with /, will ignore ctx_path automatically
        return ctx_path.joinpath(path)
        
    def find_file(self, path, resolve_link=False):
        path = self._resolve_relative_path(path)
        if PurePosixPath(path) == PurePosixPath("/"):
            self._verify_root()
            return FSDatabase.ROOTDIR_ID
        parent = self.find_file(path.parent, resolve_link=True)
        if parent is None:
            return None

        parent_type = self.get_type(parent)
        if parent_type is not Directory:
            if parent_type is None:
                raise ValueError(f"Malformed path. '{path.parent}' does not exist")
            raise ValueError(f"Malformed path. Path element '{path.parent}' resolved to type '{parent_type}'")

        if path.name == "..":
            if parent == FSDatabase.ROOTDIR_ID:
                return FSDatabase.ROOTDIR_ID
            return parent_type(self, parent).get_parent_directory().fid or FSDatabase.ROOTDIR_ID

        fid = self.find_file_in_dir(parent, path.name)

        while resolve_link and self.get_type(fid) is SymbolicLink:
            fid = self.resolve_link(SymbolicLink(self, fid)).fid
        return fid

    def resolve_link(self, link_entity):
        fid = self.find_file(link_entity.linked_path)
        if fid is None:
            return None
        return File(self, fid)

    """
    Creation/Deletion
    """
    def _verify_root(self):
        User(self, uid=FSDatabase.ROOTUSER_ID, user_name="root", create_if_missing=True)
        if self.get_type(FSDatabase.ROOTDIR_ID) is None:
            root_entity = File(self , self.add_file(PurePosixPath("/")))
            self.add_directory(root_entity)
        User(self, uid=FSDatabase.NOBODYUSER_ID, user_name="nobody", create_if_missing=True)

    def add_file(self, path):
        author, group = None, None
        try:
            author = User(self, uid=shell_context.USER)
            group = next(author.get_groups())
        except (MissingUserError): 
            author = User(self, uid=FSDatabase.ROOTUSER_ID)
            group = next(author.get_groups())

        path = self._resolve_relative_path(path)
        params = {"name": path.name, "author": author.uid, "group": group.gid}
        format_params = {}
        if path != PurePosixPath("/"):
            parent_id = self.find_file(path.parent, resolve_link=True)
            if parent_id is None or self.get_type(parent_id) is not Directory:
                raise ValueError("Invalid path for file")
            params["parent_fid"] = parent_id
            format_params["use_fid"] = "NULL"
        else:
            format_params["use_fid"] = "%(fid)s"
            params["fid"] = FSDatabase.ROOTDIR_ID

        with self:
            # Create file
            self._execute_queries(FSGenericFileQuery.DB_QUERY_ADD_FILE, params, format_params)
            if "fid" not in params:
                params["fid"] = self.cursor.lastrowid
            # Add to folder
            if "parent_fid" in params:
                self._execute_queries(FSDirectoryQuery.DB_QUERY_ADD_CHILD_FILE, params)
            self.connection.commit()
        return params["fid"]

    def add_directory(self, entity):
        params = {"fid": entity.fid}
        entity.permissions = FSGenericFileQuery.DEFAULT_DIRECTORY_PERMISSIONS.value
        with self:
            # Add to group
            self._execute_queries(FSDirectoryQuery.DB_QUERY_ADD_DIRECTORY, params)
            self.connection.commit()

    def add_regular_file(self, entity, contents):
        params = {"fid": entity.fid}
        with self:
            if isinstance(contents, str):
                contents = contents.splitlines(keepends=True)
            if not contents:
                contents.append("")
            params["size"] = sum(map(len, contents))
            # Add to group
            self._execute_queries(FSRegularFileQuery.DB_QUERY_ADD_REG_FILE_METADATA, params)
            params["file_content_id"] = self.cursor.lastrowid
            self._execute_queries(FSRegularFileQuery.DB_QUERY_ADD_REG_FILE, params)
            for line_no, content in enumerate(contents, 1):
                content_params = {"line_no": line_no, "line_content": content}
                content_params.update(params)
                self._execute_queries(FSRegularFileQuery.DB_QUERY_ADD_FILE_CONTENT, content_params)
            self.connection.commit()

    def add_symbolic_link(self, entity, linked_path):
        params = {"fid": entity.fid, "path": str(linked_path)}
        with self:
            # Add to group
            self._execute_queries(FSSymbolicLinkQuery.DB_QUERY_ADD_SYMBOLIC_LINK, params)
            self.connection.commit()

    def remove(self, entity):
        file_query_map = {
            Directory: FSDirectoryQuery.DB_QUERY_DEL_DIRECTORY,
            RegularFile: FSRegularFileQuery.DB_QUERY_DEL_REG_FILE,
            SymbolicLink: FSSymbolicLinkQuery.DB_QUERY_DEL_SYMBOLIC_LINK,
        }
        with self:
            if isinstance(entity, User):
                self._execute_queries(FSUserQuery.DB_QUERY_DEL_USER, {"uid": entity.uid})
            elif isinstance(entity, Group):
                self._execute_queries(FSUserQuery.DB_QUERY_DEL_GROUP, {"gid": entity.gid})
            elif isinstance(entity, File):
                self._execute_queries(file_query_map[type(entity)], {"fid": entity.fid})
                self._execute_queries(FSGenericFileQuery.DB_QUERY_DEL_FILE, {"fid": entity.fid})
            self.connection.commit()

    def remove_hardlink(self, file_entity):
        with self:
            self._execute_queries(FSRegularFileQuery.DB_QUERY_DEL_HARDLINK, {"fid": file_entity.fid})
            self.connection.commit()

    """
    Getters and Setters
    """

    def get_full_name(self, entity):
        full_name = entity.name
        parent = self.get_parent_dir(entity)
        grandparent = self.get_parent_dir(parent) if parent else None

        while parent and grandparent:
            full_name = f"{parent.name}/{full_name}"
            parent = grandparent
            grandparent = self.get_parent_dir(parent)
        
        return f"/{full_name}"

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
            name = self.cursor.fetchone()
            return name[0] if name else None

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
                }, format_params={"prop": "fileName"})
            self.connection.commit()

    def get_owner(self, file_entity):
        uid = None
        with self:
            self._execute_queries(FSGenericFileQuery.DB_QUERY_GET_PROP, {
                "fid": file_entity.fid,
            }, format_params={"prop": "ownerID"})
            owner_id = self.cursor.fetchone()
            uid = owner_id[0] if owner_id else None
        return User(self, uid=uid) if uid is not None else None

    def set_owner(self, file_entity, new_owner):
        with self:
            self._execute_queries(FSGenericFileQuery.DB_QUERY_SET_PROP, {
                "fid": file_entity.fid,
                "value": new_owner.uid
            }, format_params={"prop": "ownerID"})
            self.connection.commit()

    def get_group_owner(self, file_entity):
        gid = None
        with self:
            self._execute_queries(FSGenericFileQuery.DB_QUERY_GET_PROP, {
                "fid": file_entity.fid,
            }, format_params={"prop": "groupOwnerID"})
            owner_id = self.cursor.fetchone()
            gid = owner_id[0] if owner_id else None
        return Group(self, gid=gid) if gid is not None else None

    def set_group_owner(self, file_entity, new_owner):
        with self:
            self._execute_queries(FSGenericFileQuery.DB_QUERY_SET_PROP, {
                "fid": file_entity.fid,
                "value": new_owner.gid
            }, format_params={"prop": "groupOwnerID"})
            self.connection.commit()

    def get_permissions(self, file_entity):
        self.use_raw = True
        with self:
            self._execute_queries(FSGenericFileQuery.DB_QUERY_GET_PROP, {
                "fid": file_entity.fid,
            }, format_params={"prop": "permissionBits"})
            perms = self.cursor.fetchone()
            return PermissionBits(perms[0]) if perms else None

    def set_permissions(self, file_entity, permission_bits):
        with self:
            self._execute_queries(FSGenericFileQuery.DB_QUERY_SET_PROP, {
                "fid": file_entity.fid,
                "value": PermissionBits.as_bytes(permission_bits)
            }, format_params={"prop": "permissionBits"})
            self.connection.commit()

    def get_created_date(self, file_entity):
        with self:
            self._execute_queries(FSGenericFileQuery.DB_QUERY_GET_PROP, {
                "fid": file_entity.fid,
            }, format_params={"prop": "dateCreated"})
            date_created = self.cursor.fetchone()
            return date_created[0] if date_created else None

    def get_author(self, file_entity):
        with self:
            self._execute_queries(FSGenericFileQuery.DB_QUERY_GET_PROP, {
                "fid": file_entity.fid,
            }, format_params={"prop": "authorID"})
            author = self.cursor.fetchone()
            return User(self, uid=author[0]) if author else None

    def get_modified_date(self, file_entity):
        query_map = {
            File: FSGenericFileQuery,
            Directory: FSDirectoryQuery,
            RegularFile: FSRegularFileQuery,
            SymbolicLink: FSSymbolicLinkQuery,
        }
        query_type = query_map[type(file_entity)]
        with self:
            self._execute_queries(query_type.DB_QUERY_GET_PROP, {
                "fid": file_entity.fid,
            }, format_params={"prop": "dateModified"})
            date_modified = self.cursor.fetchone()
            return date_modified[0] if date_modified else None

    def update_modified_date(self, file_entity):
        query_map = {
            File: FSGenericFileQuery,
            Directory: FSDirectoryQuery,
            RegularFile: FSRegularFileQuery,
            SymbolicLink: FSSymbolicLinkQuery,
        }
        query_type = query_map[type(file_entity)]
        with self:
            self._execute_queries(query_type.DB_QUERY_SET_PROP, {
                "fid": file_entity.fid,
                "value": datetime.now()
            }, format_params={"prop": "dateModified",})
            self.connection.commit()

    def get_accessed_date(self, file_entity):
        query_map = {
            File: FSGenericFileQuery,
            Directory: FSDirectoryQuery,
            RegularFile: FSRegularFileQuery,
            SymbolicLink: FSSymbolicLinkQuery,
        }
        query_type = query_map[type(file_entity)]
        with self:
            self._execute_queries(query_type.DB_QUERY_GET_PROP, {
                "fid": file_entity.fid,
            }, format_params={"prop": "dateLastOpened"})
            date_accessed = self.cursor.fetchone()
            return date_accessed[0] if date_accessed else None

    def update_accessed_date(self, file_entity):
        query_map = {
            File: FSGenericFileQuery,
            Directory: FSDirectoryQuery,
            RegularFile: FSRegularFileQuery,
            SymbolicLink: FSSymbolicLinkQuery,
        }
        query_type = query_map[type(file_entity)]
        with self:
            self._execute_queries(query_type.DB_QUERY_SET_PROP, {
                "fid": file_entity.fid,
                "value": datetime.now()
            }, format_params={"prop": "dateLastOpened"})
            self.connection.commit()

    def get_parent_dir(self, file_entity):
        with self:
            self._execute_queries(FSGenericFileQuery.DB_QUERY_GET_PARENT_DIR, {
                "fid": file_entity.fid
            })
            parent_fid = self.cursor.fetchone()
            return Directory(self, parent_fid[0]) if parent_fid else None

    def set_parent_dir(self, file_entity, parent_dir):
        with self:
            self._execute_queries(FSDirectoryQuery.DB_QUERY_MOVE_CHILD_FILE, {
                "fid": file_entity.fid,
                "parent_fid": parent_dir.fid
            })
            self.connection.commit()

    def get_linked_path(self, link_entity):
        with self:
            self._execute_queries(FSSymbolicLinkQuery.DB_QUERY_GET_PROP, {
                "fid": link_entity.fid,
            }, format_params={"prop": "linkToFullPath"})
            link_path = self.cursor.fetchone()
            return link_path[0] if link_path else None

    def set_linked_path(self, link_entity, new_path):
        with self:
            self._execute_queries(FSSymbolicLinkQuery.DB_QUERY_SET_PROP, {
                "fid": link_entity.fid,
                "value": new_path,
            }, format_params={"prop": "linkToFullPath"})
            self.connection.commit()

    def get_size(self, file_entity):
        if file_entity.type is not RegularFile:
            return 0
        with self:
            self._execute_queries(FSRegularFileQuery.DB_QUERY_GET_PROP, {
                "fid": file_entity.fid,
            }, format_params={"prop": "size"})
            size = self.cursor.fetchone()
            return size[0] if size else None

    """
    Operations on file
    """
    def get_children(self, directory_entity):
        params = {"fid": directory_entity.fid}
        files = []
        with self:
            self._execute_queries(FSDirectoryQuery.DB_QUERY_GET_CHILDREN, params)
            files = [fid for (fid,) in self.cursor]
        for fid in files:
            yield File(self, fid)

    def get_children_like(self, directory_entity, pattern, search_subdirs=False):
        params = {"fid": directory_entity.fid, "pattern": pattern}
        files = []
        with self:
            self._execute_queries(FSDirectoryQuery.DB_QUERY_GET_CHILDREN_LIKE, params)
            files = [fid for (fid,) in self.cursor]
        for fid in files:
            yield File(self, fid)
        if search_subdirs:
            subdirs = []
            with self:
                self._execute_queries(FSDirectoryQuery.DB_QUERY_GET_SUBDIRECTORIES, params)
                subdirs = [fid for (fid,) in self.cursor]
            for subdir in subdirs:
                yield from self.get_children_like(Directory(self, subdir), pattern)

    def write_content(self, file_entity, new_content):
        params = {"fid": file_entity.fid}
        with self:
            self._execute_queries(FSRegularFileQuery.DB_QUERY_DELETE_ALL_FILE_CONTENT, params)
            contents = new_content
            if isinstance(contents, str):
                contents = contents.splitlines(keepends=True)
            if not contents:
                contents.append("")
            self._execute_queries(FSRegularFileQuery.DB_QUERY_SET_PROP, {
                "fid": file_entity.fid,
                "value": sum(map(len, contents)),
            }, format_params={"prop": "size"})
            for line_no, content in enumerate(contents, 1):
                content_params = {"line_no": line_no, "line_content": content}
                content_params.update(params)
                self._execute_queries(FSRegularFileQuery.DB_QUERY_ADD_FILE_CONTENT, content_params)
            self.connection.commit()

    def append_content(self, file_entity, new_content):
        params = {"fid": file_entity.fid}
        with self:
            self._execute_queries(FSRegularFileQuery.DB_QUERY_GET_LAST_LINE, params)
            start_length, start_contents = 1, ""
            last_line = self.cursor.fetchone()
            start_length, start_contents = last_line if last_line else (start_length, start_contents)
            contents = new_content
            if isinstance(contents, str):
                contents = contents.splitlines(keepends=True)
            if not contents:
                contents.append("")
            if start_contents.endswith("\n"):
                contents.insert(0, start_contents)
            else:
                contents[0] = start_contents + contents[0]
            self._execute_queries(FSRegularFileQuery.DB_QUERY_INCREMENT_PROP, {
                "fid": file_entity.fid,
                "value": sum(map(len, contents)),
            }, format_params={"prop": "size"})
            for line_no, content in enumerate(contents, start_length):
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

    def check_if_utility(self, file_entity):
        with self:
            self._execute_queries(FSRegularFileQuery.DB_QUERY_CHECK_FOR_BANG, {
                "fid": file_entity.fid
            })
            found = self.cursor.fetchone()
            return bool(found)

    def find_in_file(self, file_entity, pattern):
        with self:
            self._execute_queries(FSRegularFileQuery.DB_QUERY_FIND_IN_FILE_CONTENT, {
                "fid": file_entity.fid,
                "pattern": pattern
            })
            for line_no, line_content in self.cursor:
                yield line_no, line_content

    def count_hardlinks(self, file_entity):
        params = {"fid": file_entity.fid}
        with self:
            self._execute_queries(FSRegularFileQuery.DB_QUERY_COUNT_HARDLINKS, params)
            num_hardlinks = self.cursor.fetchone()
            return num_hardlinks[0] if num_hardlinks else None


    def add_hardlink(self, file_entity, path):
        hardlink_file = File(self, path, create_if_missing=True)
        params = {"orig_fid": file_entity.fid, "link_fid": hardlink_file.fid}
        with self:
            self._execute_queries(FSRegularFileQuery.DB_QUERY_ADD_HARDLINK, params)
            self.connection.commit()


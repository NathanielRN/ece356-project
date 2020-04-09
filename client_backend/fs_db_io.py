"""Filesystem IO

Manages communication with the DB to perform IO
"""
import shell_context

from enum import Enum

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

class FSGenericFileQuery(Enum):
    DEFAULT_FILE_PERMISSIONS = 0b110110110
    DEFAULT_DIRECTORY_PERMISSIONS = 0b111101101
    DB_QUERY_ADD_FILE = (
        "INSERT INTO Files "
        "(fileName, dateCreated, permissionBits, groupOwnerID, authorID, ownerID) "
        "VALUES (%(file_name)s, %(data_created)s, %(permission_bits)s, %(group_owner)s, %(author)s, %(author)s"
    )
    DB_QUERY_DEL_FILE = "DELETE FROM Files WHERE fileID = %(fid)s"


class FSDatabase:
    def __init__(self, db_configs):
        self.connection = MySQLConnection.connect(**db_configs)
        self.cursor = None
    
    def __enter__(self):
        self.cursor = MySQLCursorNamedTuple(self.connection)
    
    def __exit__(self):
        self.cursor.close()
        self.cursor = None

    def add_user(self, uid, user_name):
        with self:
            self.cursor.execute(DB_QUERY_ADD_USER, {
                "uid": uid,
                "user_name": user_name
            })
            self.connection.commit()

    def add_group(self, gid, group_name):
        with self:
            self.cursor.execute(DB_QUERY_ADD_GROUP, {
                "gid": gid,
                "group_name": group_name
            })
            self.connection.commit()

    def get_name(self, entity):
        with self:
            self.cursor.execute(DB_QUERY_ADD_GROUP, {
                "gid": gid,
                "group_name": group_name
            })
            self.connection.commit()

    def set_name(self, entity):
        with self:
            self.cursor.execute(DB_QUERY_ADD_GROUP, {
                "gid": gid,
                "group_name": group_name
            })
            self.connection.commit()
s

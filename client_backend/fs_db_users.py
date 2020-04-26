"""
Documenation LOL
"""
class MissingUserError(ValueError):
    pass

class UserExistsError(ValueError):
    pass

class User:
    def __init__(self, fs_db, uid=None, user_name=None, create_if_missing=False):
        if user_name is None and uid is None:
            raise ValueError("Must specify user name or ID")
        if create_if_missing and user_name is None:
            raise ValueError("Cannot create user without name")
        self.fs_db = fs_db
        self.uid = None
        if uid is not None:
            self.uid = self.fs_db.get_user(uid)
        if user_name is not None:
            new_uid = self.fs_db.get_user(user_name)
            if not self._exists():
                self.uid = new_uid
            if new_uid is not None and uid is not None:
                if create_if_missing and new_uid != uid:
                    if self._exists():
                        raise UserExistsError(
                            f"User ID {self.uid} already exists with name {self.name}. "
                            f"Attempted to create User(id={uid}) with name {user_name}"
                        )
        if not self._exists() and create_if_missing:
            self.uid = self.fs_db.add_user(uid, user_name)
            group = None
            try:
                group = Group(self.fs_db, gid=self.uid)
            except MissingGroupError:
                group = Group(self.fs_db, gid=self.uid, group_name=user_name, create_if_missing=True)
            # Bypass membership check
            self.fs_db.add_membership(self, group)

        if not self._exists():
            raise MissingUserError(f"No user matching uid={uid}")

    def _exists(self):
        return self.uid is not None

    @property
    def name(self):
        return self.fs_db.get_name(self)

    @name.setter
    def name(self):
        self.fs_db.set_name(self)

    def add_to_group(self, group):
        if not self.has_group(group):
            self.fs_db.add_membership(self, group)

    def get_groups(self):
        yield from self.fs_db.get_groups(self)

    def has_group(self, group):
        return self.fs_db.check_group_membership(self, group)

    def leave_group(self, group):
        # NOTE: Should probably check if user is part of 2+ groups
        self.fs_db.revoke_membership(group, self)

    def __eq__(self, other):
        if not isinstance(other, type(self)):
            return False
        return self.uid == other.uid

    def __ne__(self, other):
        return not (self == other)

class MissingGroupError(ValueError):
    pass

class GroupExistsError(ValueError):
    pass

class Group:
    def __init__(self, fs_db, gid=None, group_name=None, create_if_missing=False):
        if group_name is None and gid is None:
            raise ValueError("Must specify group name or ID")
        if create_if_missing and group_name is None:
            raise ValueError("Cannot create group without name")
        self.fs_db = fs_db
        self.gid = None
        if gid is not None:
            self.gid = self.fs_db.get_group(gid)
        if group_name is not None:
            new_gid = self.fs_db.get_group(group_name)
            if not self._exists():
                self.gid = new_gid
            if new_gid is not None and gid is not None:
                if create_if_missing and new_gid != gid:
                    if self._exists():
                        raise GroupExistsError(
                            f"Group ID {self.gid} already exists with name {self.name}. "
                            f"Attempted to create Group(id={gid}) with name {group_name}"
                        )
        if not self._exists() and create_if_missing:
            self.gid = self.fs_db.add_group(gid, group_name)
        if not self._exists():
            raise MissingGroupError(f"No group matching gid={gid}")

    def _exists(self):
        return self.gid is not None

    @property
    def name(self):
        return self.fs_db.get_name(self)

    @name.setter
    def name(self):
        self.fs_db.set_name(self)

    def add_user(self, user):
        user.add_to_group(self)

    def remove_user(self, user):
        user.leave_group(self)

    def __eq__(self, other):
        if not isinstance(other, type(self)):
            return False
        return self.gid == other.gid

    def __ne__(self, other):
        return not (self == other)
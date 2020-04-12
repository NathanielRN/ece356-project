class User:
    def __init__(self, fs_db, uid, create_if_missing=False, user_name=None):
        if create_if_missing and user_name is None:
            raise ValueError("Cannot create user without name")
        self.fs_db = fs_db
        self.uid = self.fs_db.get_user(uid)
        if not self._exists() and create_if_missing:
            self.uid = self.fs_db.add_user(uid, user_name)
        if not self._exists():
            raise ValueError(f"No user matching uid={uid}")

    def _exists(self):
        return self.uid is not None

    @property
    def name(self):
        return self.fs_db.get_name(self)

    @name.setter
    def name(self):
        self.fs_db.set_name(self)

    def add_to_group(self, group):
        self.fs_db.add_membership(self, group)

    # No passwords or default shell settings yet

class Group:
    def __init__(self, fs_db, gid, create_if_missing=False, group_name=None):
        if create_if_missing and group_name is None:
            raise ValueError("Cannot create group without name")
        self.fs_db = fs_db
        self.gid = self.fs_db.get_group(gid)
        if not self._exists() and create_if_missing:
            self.gid = self.fs_db.add_group(gid, group_name)
        if not self._exists():
            raise ValueError(f"No group matching gid={gid}")

    def _exists(self):
        return self.gid is not None

    @property
    def name(self):
        return self.fs_db.get_name(self)

    @name.setter
    def name(self):
        self.fs_db.set_name(self)

    def remove_user(self, user):
        self.fs_db.revoke_membership(self, user)
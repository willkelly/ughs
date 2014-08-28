import sqlite3

class BaseStorageBackend(object):
    def get_user(self, userid):
        raise NotImplemented

    def get_users_for_group(self, groupid):
        raise NotImplemented

    def store_group(self, groupid, users):
        raise NotImplemented

    def delete_group(self, groupid):
        raise NotImplemented

    def delete_user(self, userid):
        raise NotImplemented

    def store_user(self, user):
        raise NotImplemented

    def user_exists(self, userid):
        user = self.get_user(userid)
        return user is not None

    def group_exists(self, groupid):
        raise NotImplemented

class InMemoryStorageBackend(BaseStorageBackend):
    def __init__(self):
        self.users = {}
        self.groups = {}

    def get_user(self, userid):
        return self.users.get(userid, None)

    def get_users_for_group(self, groupid):
        if self.group_exists(groupid):
            return [user for userid, user in self.users.iteritems()
                    if groupid in user['groups']]

    def store_group(self, groupid, users):
        for userid in self.groups.get(groupid, []):
            if userid not in users:
                idx = self.users[userid]['groups'].index(user)
                if idx != -1:
                    del self.users[userid]['groups'][idx]
        for userid in users:
            if groupid not in self.users[userid]['groups']:
                self.users[userid]['groups'].append(groupid)
        self.groups[groupid] = users

    def delete_group(self, groupid):
        for userid, user in self.users.iteritems():
            user['groups'] = [group for group in user['groups']
                              if group != groupid]
        del self.groups[groupid]

    def delete_user(self, userid):
        for group in self.users[userid]['groups']:
            self.groups[group] = [user for user in self.groups[group]
                                  if self.users[userid] != userid]
        del self.users[userid]

    def store_user(self, user):
        for groupid, group in self.groups.iteritems():
            if groupid in user['groups']:
                if not user['userid'] in group:
                    group.append(user['userid'])
            else:
                idx = group.index(user['userid'])
                if idx != -1:
                    del group[idx]
        self.users[user['userid']] = user

    def user_exists(self, userid):
        return userid in self.users

    def group_exists(self, groupid):
        return groupid in self.groups

class SQLiteBackend(BaseStorageBackend):
    def _query_db(self, query, args=(), one=False):
        cur = self.db.execute(query, args)
        rv = cur.fetchall()
        cur.close()
        return (rv[0] if rv else None) if one else rv

    def _create_schema(self):
        schema = """
create table users (
        userid text,
        first_name text,
        last_name text);
create table user_group (
        user_ref integer,
        group_ref integer,
        foreign key(user_ref) references users(rowid),
        foreign key (group_ref) references groups(rowid));
create table groups (
        name text);
"""
        # if empty database, we'll load a schema.  This should
        # probably be smart but will not be.
        cursor = self.db.cursor()
        cursor.execute("""select count(name) as tables
                          from sqlite_master where type='table'""")
        if cursor.fetchone()["tables"] == 0:
            for query in schema.split(";"):
                cursor.execute(query)
        self.db.commit()
        cursor.close()

    def __init__(self, database_path):
        def dict_factory(cursor, row):
            d = {}
            for idx, col in enumerate(cursor.description):
                d[col[0]] = row[idx]
            return d
        self.db = sqlite3.connect(database_path)
        self.db.row_factory = dict_factory

    def get_user(self, userid):
        user = self._query_db("""
select users.userid, users.first_name, users.last_name
from users where userid = ?""", args=(userid), one=True)
        if user is None:
            return user
        groups = [group['name'] for group in self._query_db("""
select name from group
"""
    def get_users_for_group(self, groupid):
        raise NotImplemented

    def store_group(self, groupid, users):
        raise NotImplemented

    def delete_group(self, groupid):
        raise NotImplemented

    def delete_user(self, userid):
        raise NotImplemented

    def store_user(self, user):
        raise NotImplemented

    def user_exists(self, userid):
        user = self.get_user(userid)
        return user is not None

    def group_exists(self, groupid):
        raise NotImplemented

StorageBackend = InMemoryStorageBackend

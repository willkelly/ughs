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
                try:
                    idx = self.users[userid]['groups'].index(user)
                    del self.users[userid]['groups'][idx]
                except ValueError:
                    pass
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
                try:
                    idx = group.index(user['userid'])
                    del group[idx]
                except ValueError:
                    pass
        self.users[user['userid']] = user

    def user_exists(self, userid):
        return userid in self.users

    def group_exists(self, groupid):
        return groupid in self.groups

StorageBackend = InMemoryStorageBackend

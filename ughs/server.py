
from flask import Flask, request, Response, g
import json

app = Flask("ughs")

class StorageBackend(object):
    def __init__(self):
       self.users = {}
       self.groups = {}
        
    def get_user(self, userid):
        return self.users.get(userid, None)
    
    def get_users_for_group(self, groupid):
        if self.group_exists(groupid):
            return [user for userid, user in self.users.iteritems() if groupid in user['groups']]

    def store_group(self, groupid, users):
        for userid in self.groups.get(groupid, []):
            if not userid in users:
                idx = self.users[userid]['groups'].index(user)
                if idx != -1:
                    del self.users[userid]['groups'][idx]
        for userid in users:
            if not groupid in self.users[userid]['groups']:
                self.users[userid]['groups'].append(groupid)
        self.groups[groupid] = users

    def delete_group(self):
        for user in self.users:
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

storage = StorageBackend()


@app.route('/users/<userid>', methods=['GET', 'POST', 'PUT', 'DELETE'])
def user_handler(userid):
    if request.method == "GET":
        # assume json no matter what, because that's how we're rolling.
        return show_user(userid)
    elif request.method == "POST":
        return add_user(request.get_json(force=True), userid)
    elif request.method == "PUT":
        return modify_user(request.get_json(force=True), userid)
    elif request.method == "DELETE":
        return delete_user(userid)
    return format_error("resource not found"), 404


@app.route('/groups/<groupid>', methods=['GET', 'POST', 'PUT', 'DELETE'])
def group_handler(groupid):
    if request.method == "GET":
        return get_users(groupid)
    elif request.method == "POST":
        return add_group(groupid)
    elif request.method == "PUT":
        return modify_group(groupid, request.get_json(force=True))
    elif request.method == "DELETE":
        return delete_group(groupid)
    return format_error("resource not found"), 404

def get_users(groupid):
    users = storage.get_users_for_group(groupid)
    if users is None:
        return format_error("Group '%s' does not exist." % groupid), 404
    return Response(json.dumps(users), status=200, mimetype='application/json')


def add_group(groupid):
    if storage.group_exists(groupid):
        return Response(format_error("Group '%s' already exists" % groupid), status=403)
    storage.store_group(groupid, [])
    return Response(status=201)


def modify_group(groupid, users):
    users, msg = validate_group(users)
    if users is None:
        return Response(format_error(msg), status=400, mimetype='application/json')
    storage.store_group(groupid, users)
    return Response(status=204)

def show_user(userid):
    user = storage.get_user(userid)
    if user is None:
        return format_error("User not found"), 404
    return Response(json.dumps(user), status=200, mimetype='application/json')


def delete_user(userid):
    if storage.user_exists(userid):
            storage.delete_user(userid)
            return Response(status=204)
    return format_error("User not found"), 404


def add_user(user, userid):
    msg = validate_user(user, userid)
    if msg is not None:
        return format_error("Invalid user: %s" % msg), 400
    if storage.user_exists(userid):
        return format_error("User '%s' already exists." % userid), 403
    storage.store_user(user)
    return Response(status=201)


def modify_user(user, userid):
    msg = validate_user(user, userid)
    if msg is not None:
        return format_error("Invalid user: %s" % msg), 403
    if not storage.user_exists(userid):
        return format_error("User '%s' not found" % userid), 404
    storage.store_user(user)
    return Response(status=204)


def format_error(msg):
    return json.dumps({"error": msg})


def validate_user(user, userid=None):
    # user should be a json object, parsed into a dictionary
    if not isinstance(user, dict):
        print user, type(user)
        return "User entry is not a json object"

    # the user should include all of the keys we expect in a user
    required_fields = ["first_name", "last_name", "userid", "groups"]
    valid, value = has_expected_keys(user, required_fields)
    if not valid:
        return "User record missing expected key '%s'" % (value)

    # the user should not include any other fields.
    valid, value = has_expected_keys(required_fields, user)
    if not valid:
        return "Unexpected field: '%s'." % value
    
    # groups should be a json array, parsed into a list.
    if not isinstance(user["groups"], list):
        return 'user["groups"] should be a json array'

    # all groups should be strings
    valid, value = map_all(user["groups"], is_string)
    if not valid:
        return "Group name '%s' is not a string." % (value)
    
    # all groups assigned to the user must already exist.
    valid, value = map_all(user["groups"], storage.group_exists)
    if not valid:
        return "Group '%s' does not exist." % (value)

    # if a userid is provided, userid should match the user record
    if user['userid'] != userid:
        return "Userid '%s' does not match uri's userid '%s'" % (
            user['userid'], userid)
    return None


def is_string(s):
    return isinstance(s, basestring)


def validate_group(users):
    # users should be a json array of strings, parsed as a list of strings
    if not isinstance(users, list):
        return None, "Users entry is not a json array."

    # users should all be strings
    valid, value = map_all(users, is_string)
    if not valid:
        return None, "User names must be strings.  Received: '%s'" % value

    # users should all exist
    valid, value = map_all(users, storage.user_exists)
    if not valid:
        return None, "User '%s' does not exist." % (value)
    return users, None


def has_expected_keys(d, expected_keys):
    return map_all(expected_keys, lambda k: k in d)


def map_all(items, function):
    # one possible combination of 'map' and 'all'.  runs function on
    # each element of items returns True, None if function(element)
    # returns True on all items or False, item on the first item for
    # which function(item) is not true.  This helps us give better
    # error reporting on user input.
    for item in items:
        if function(item) == False:
            return False, item
    return True, None


if __name__ == "__main__":
    app.debug = True
    app.run(host='0.0.0.0')

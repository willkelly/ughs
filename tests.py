#!/usr/bin/python

import unittest
import ughs
import json

valid_user = {
    "first_name": "Joe",
    "last_name": "Smith",
    "userid": "jsmith",
    "groups": []}


def new_user(userid, groups=[], first_name="Some", last_name="User"):
    return dict(userid=userid,
                groups=groups,
                first_name=first_name,
                last_name=last_name)


def user_equals(u1, u2):
    # we're not guaranteed a stable 'groups' order, so == doesn't work
    safe_keys = ["first_name", "last_name", "userid"]
    for key in safe_keys:
        if u1[key] != u2[key]:
            return False
    if sorted(u1["groups"]) != sorted(u2["groups"]):
        return False
    return True

valid_group = []


class UghsTestCase(unittest.TestCase):
    def setUp(self):
        self.app = ughs.app.test_client()
        ughs.app.config['TESTING'] = True

    def test_000_get_nonexistent_user(self):
        rv = self.app.get("/users/nonexistent")
        assert(rv.status_code == 404)

    def test_001_create_user(self):
        rv = self.app.post("/users/%s" % valid_user['userid'],
                           data=json.dumps(valid_user))
        assert(rv.status_code == 201)

    def test_001a_get_user(self):
        rv = self.app.get("/users/%s" % valid_user['userid'])
        assert(rv.status_code == 200)
        assert(rv.headers["content-type"] == "application/json")
        assert(user_equals(valid_user, json.loads(rv.data)))

    def test_002_create_user_already_exists(self):
        rv = self.app.post("/users/%s" % (valid_user['userid']),
                           data=json.dumps(valid_user))
        assert(rv.status_code == 403)
        assert(rv.headers["content-type"] == "application/json")

    def test_003_create_user_userid_doesnt_match(self):
        rv = self.app.post("/users/not_jsmith", data=json.dumps(valid_user))
        assert(rv.status_code == 400)
        assert(rv.headers["content-type"] == "application/json")

    def test_004_create_user_nonexistent_group(self):
        valid_user['groups'] = ['admins']
        rv = self.app.post("/users/jsmith", data=json.dumps(valid_user))
        assert(rv.status_code == 400)
        assert(rv.headers["content-type"] == "application/json")

    def test_005_create_group(self):
        rv = self.app.post("/groups/admins", data=json.dumps(valid_group))
        assert(rv.status_code == 201)
        rv = self.app.get("/groups/admins")

    def test_005a_get_nonexistent_group(self):
        rv = self.app.get("/groups/nonexistent")
        assert(rv.status_code == 404)
        assert(rv.headers["content-type"] == "application/json")

    def test_005b_get_empty_group(self):
        rv = self.app.get("/groups/admins")
        assert(rv.status_code == 404)
        assert(rv.headers["content-type"] == "application/json")

    def test_006_create_group_already_exists(self):
        rv = self.app.post("/groups/admins", data=json.dumps(valid_group))
        assert(rv.status_code == 403)
        assert(rv.headers["content-type"] == "application/json")

    def test_007_update_group(self):
        rv = self.app.put("/groups/admins",
                          data=json.dumps([valid_user['userid']]))
        assert(rv.status_code == 204)
        rv = self.app.get("/users/%s" % valid_user['userid'])
        user = json.loads(rv.data)
        assert("admins" in user['groups'])
        rv = self.app.get("/groups/admins")
        assert(rv.status_code == 200)
        users = json.loads(rv.data)
        assert(valid_user['userid'] in users)

    def test_008_update_user_userid(self):
        bad_user = new_user("notjsmith")
        rv = self.app.put("/users/%s" % (valid_user['userid']),
                          data=json.dumps(bad_user))
        assert(rv.status_code == 400)
        assert(rv.headers["content-type"] == "application/json")
        rv = self.app.get("/users/%s" % valid_user['userid'])
        user = json.loads(rv.data)
        assert(user_equals(user, valid_user))

    def test_099_delete_group(self):
        rv = self.app.get("/users/%s" % valid_user['userid'])
        user = json.loads(rv.data)
        assert("admins" in user["groups"])
        rv = self.app.delete("/groups/admins")
        assert(rv.status_code == 204)
        rv = self.app.get("/users/%s" % (valid_user['userid']))
        user = json.loads(rv.data)
        assert("admins" not in user["groups"])
        rv = self.app.get("/groups/admins")
        assert(rv.status_code == 404)
        assert(rv.headers["content-type"] == "application/json")

    def test_101_delete_user(self):
        rv = self.app.delete("/users/%s" % (valid_user['userid']))
        assert(rv.status_code == 204)
        rv = self.app.get("/users/%s" % (valid_user['userid']))
        assert(rv.status_code == 404)
        assert(rv.headers["content-type"] == "application/json")

    def test_102_delete_nonexistent_user(self):
        rv = self.app.delete("/users/nonexistent")
        assert(rv.status_code == 404)
        assert(rv.headers["content-type"] == "application/json")

    def test_103_delete_nonexistent_group(self):
        rv = self.app.delete("/groups/nonexistent")
        assert(rv.status_code == 404)
        assert(rv.headers["content-type"] == "application/json")

if __name__ == "__main__":
    unittest.main()

#!/usr/bin/python

import unittest
import ughs
import json
valid_user = {
    "first_name": "Joe",
    "last_name": "Smith",
    "userid": "jsmith",
    "groups": []}

class UghsTestCase(unittest.TestCase):
    def setUp(self):
        self.app = ughs.app.test_client()
        ughs.app.config['TESTING'] = True

    def test_create_user(self):
        rv = self.app.post("/users/jsmith", data=json.dumps(valid_user))
        assert(rv.status_code == 201)

        
if __name__ == "__main__":
    unittest.main()

"""
This module implements test controllers functionality.

License: GNU General Public License (GPL) v3.0 or later.
This program is free software: you can redistribute it and/or modify it
under the terms of the GNU General Public License as published by the
Free Software Foundation, either version 3 of the License, or (at your option) any later version.

Author: Philippe Fajeau
"""



import pytest
from flask import url_for


"""
- Sample test case


import json

# yield mock data you want
@pytest.fixture()
def mock_user():
    yield {
        "name": "John Smith",
        "id": 1
    }


# add below decorator if you want to run tests in given class sequentially
@pytest.mark.incremental
class TestUser(object):
    def test_add_user(self, client, mock_user):
        rv = client.post(url_for("add_user"), json=mock_user)
        data = json.loads(rv.data)
        # check for http status code
        assert rv.status_code == 200
        # check for specific attributes in json response
        assert data["status"] == "success"
        
    def test_remove_user(self, client, mock_user):
        rv = client.post(url_for("remove_user"), json={"id": mock_user.id})
        data = json.loads(rv.data)
        # check for http status code
        assert rv.status_code == 200
        # check for specific attributes in json response
        assert data["status"] == "success"
"""

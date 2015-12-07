#!/usr/bin/env python
"""
Copyright (C) 2013-2015  Christian & Christian  <hello@pssst.name>

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program. If not, see <http://www.gnu.org/licenses/>.
"""
import io
import os
import random
import string
import sys


from pssst import Pssst


try:
    import pytest
except ImportError:
    sys.exit("Requires pytest (https://pytest.org)")


def setup_module(module):
    """
    Setup file list for tests.

    Parameters
    ----------
    param module : string
        The module name.

    """
    global files

    files = []


def teardown_module(module):
    """
    Remove all files generated from tests.

    Parameters
    ----------
    param module : string
        The module name.

    """
    global files

    for file in files:
        if os.path.exists(file):
                os.remove(file)


def createUser(length=16):
    """
    Returns a random username and password.

    Parameters
    ----------
    param length : int, optional (default is 16)
        Length of the username and password in characters.

    Returns
    -------
    tuple
        A random username and password.

    """
    global files

    pool = string.ascii_lowercase + string.digits
    username = "".join([random.choice(pool) for x in range(length)])
    password = "".join([random.choice(pool) for x in range(length)])

    files.append(os.path.join(os.path.expanduser("~"), ".pssst." + username))

    return (username, password)


class TestName:
    """
    Tests name parsing with the test cases:

    * User name parse maximum
    * User name parse minimum
    * User name is invalid

    Methods
    -------
    test_name_maximum()
        Tests if a maximum name is parsed correctly.
    test_name_minimum()
        Tests if a minimum name is parsed correctly.
    test_name_invalid()
        Tests if a name is invalid.

    """
    def test_name_maximum(self):
        """
        Tests if name is parsed correctly.

        """
        name = Pssst.Name(" pssst.UserName:Pa55w0rd! ")

        assert name.user == "username"
        assert name.password == "Pa55w0rd!"
        assert str(name) == "pssst.username"

    def test_name_minimum(self):
        """
        Tests if name is parsed correctly.

        """
        name = Pssst.Name("me")

        assert name.user == "me"
        assert name.password == None
        assert str(name) == "pssst.me"

    def test_name_invalid(self):
        """
        Tests if name is invalid.

        """
        with pytest.raises(Exception) as ex:
            Pssst.Name("Invalid.User.Name")

        assert str(ex.value) == "User name invalid"


class TestKeyStorage:
    """
    Tests key storage with the test cases:

    * Key list

    Methods
    -------
    test_key_list()
        Tests if file is created correctly.

    """
    def test_key_list(self):
        """
        Tests if file is created correctly.

        """
        username1, password1 = createUser()
        username2, password2 = createUser()

        pssst1 = Pssst(username1, password1)
        pssst1.create()

        pssst2 = Pssst(username2, password2)
        pssst2.create()

        pssst1.push([username1], "Hello World !")
        pssst1.push([username2], "Hello World !")

        keys = ["id_api", username1, username2]

        assert sorted(pssst1.keys.list()) == sorted(keys)


class TestCrypto:
    """
    Tests crypto methods with this test cases:

    * Verification failed, user not found
    * Verification failed, signature invalid
    * Verification failed, signature wrong

    Methods
    -------
    test_request_verify_user_not_found()
        Tests if request user is not found.
    test_request_verify_signature_invalid()
        Tests if request signature is invalid.
    test_request_verify_signature_wrong()
        Tests if request signature is wrong.

    """
    def test_request_verify_user_not_found(self):
        """
        Tests if request user is not found.

        """
        with pytest.raises(Exception) as ex:
            pssst = Pssst(*createUser())
            pssst.pull()

        assert str(ex.value) == "Verification failed"

    def test_request_verify_signature_invalid(self):
        """
        Tests if request signature is invalid.

        """
        original = Pssst._Key.sign

        with pytest.raises(Exception) as ex:
            Pssst._Key.sign = lambda self, data: ("!", b"!")

            pssst = Pssst(*createUser())
            pssst.create()
            pssst.pull()

        Pssst._Key.sign = original

        assert str(ex.value) == "Verification failed"

    def test_request_verify_signature_wrong(self):
        """
        Tests if request verification signature is correct.

        """
        original = Pssst._Key.sign

        with pytest.raises(Exception) as ex:
            Pssst._Key.sign = lambda self, data: original(self, "Test")

            pssst = Pssst(*createUser())
            pssst.create()
            pssst.pull()

        Pssst._Key.sign = original

        assert str(ex.value) == "Verification failed"


class TestUser:
    """
    Tests user commands with this test cases:

    * User create
    * User create failed, already exists
    * User delete
    * User delete, user was deleted
    * User find
    * User find failed, user was deleted
    * User find failed, user not found
    * User name invalid

    Methods
    -------
    test_create_user()
        Tests if an user can be created.
    test_create_user_already_exists()
        Tests if an user already exists.
    test_delete_user()
        Tests if an user can be deleted.
    test_delete_user_was_deleted()
        Tests if an user was deleted.
    test_find_user()
        Tests if an user public can be found.
    test_find_user_was_deleted()
        Tests if an user was deleted.
    test_find_user_not_found()
        Tests if an user is not found.
    test_user_name_invalid()
        Tests if an user name is invalid.

    """
    def test_create_user(self):
        """
        Tests if an user can be created.

        """
        pssst = Pssst(*createUser())
        pssst.create()

    def test_create_user_already_exists(self):
        """
        Tests if an user already exists.

        """
        with pytest.raises(Exception) as ex:
            pssst = Pssst(*createUser())
            pssst.create()
            pssst.create()

        assert str(ex.value) == "User already exists"

    def test_delete_user(self):
        """
        Tests if an user can be deleted.

        """
        pssst = Pssst(*createUser())
        pssst.create()
        pssst.delete()

    def test_delete_user_was_deleted(self):
        """
        Tests if an user was deleted.

        """
        with pytest.raises(Exception) as ex:
            pssst = Pssst(*createUser())
            pssst.create()
            pssst.delete()
            pssst.pull()

        assert str(ex.value) == "User was deleted"

    def test_find_user(self):
        """
        Tests if an user public key can be found.

        """
        username, password = createUser()
        pssst = Pssst(username, password)
        pssst.create()
        pssst.find(username)

    def test_find_user_was_deleted(self):
        """
        Tests if an user was deleted.

        """
        with pytest.raises(Exception) as ex:
            username, password = createUser()
            pssst = Pssst(username, password)
            pssst.create()
            pssst.delete()

            pssst = Pssst(*createUser())
            pssst.find(username)

        assert str(ex.value) == "User was deleted"

    def test_find_user_not_found(self):
        """
        Tests if an user is not found.

        """
        with pytest.raises(Exception) as ex:
            pssst = Pssst(*createUser())
            pssst.find("usernotfound")

        assert str(ex.value) == "User not found"

    def test_user_name_invalid(self):
        """
        Tests if an user name is invalid.

        """
        with pytest.raises(Exception) as ex:
            pssst = Pssst(*createUser())
            pssst.find("test !")

        assert str(ex.value) == "User name invalid"


class TestPssst:
    """
    Tests client with this test cases:

    * Push self
    * Push single user
    * Push multi users
    * Push failed, user name invalid
    * Pull empty
    * Password wrong

    Methods
    -------
    test_push_self()
        Tests if a message could be pushed to sender.
    test_push_single_user()
        Tests if a message could be pushed to one receiver.
    test_push_multi_users()
        Tests if a message could be pushed to many receivers.
    test_push_user_name_invalid()
        Tests if user name is invalid.
    test_push_pull_empty()
        Tests if box is empty.
    test_pull_empty()
        Tests if box is empty.
    test_password_wrong()
        Tests if a password is wrong.

    """
    def test_push_self(self):
        """
        Tests if a message could be pushed to sender.

        """
        username, password = createUser()
        message = b"Echo"

        pssst = Pssst(username, password)
        pssst.create()
        pssst.push([username], message)

        assert pssst.pull() == message

    def test_push_single_user(self):
        """
        Tests if a message could be pushed to one receiver.

        """
        username1, password1 = createUser()
        username2, password2 = createUser()
        message = b"Hello World!"

        pssst1 = Pssst(username1, password1)
        pssst1.create()

        pssst2 = Pssst(username2, password2)
        pssst2.create()
        pssst2.push([username1], message)

        assert pssst1.pull() == message

    def test_push_multi_users(self):
        """
        Tests if a message could be pushed to many receivers.

        """
        message = b"Hello World!"

        users = [createUser() for i in range(5)]
        names = [username for username, password in users]

        for user in users:
            Pssst(*user).create()

        pssst = Pssst(*createUser())
        pssst.create()
        pssst.push(names, message)

        for user in users:
            pssst = Pssst(*user)

            assert pssst.pull() == message

    def test_push_user_name_invalid(self):
        """
        Tests if user name is invalid.

        """
        with pytest.raises(Exception) as ex:
            pssst = Pssst(*createUser())
            pssst.push(["test !"], "test")

        assert str(ex.value) == "User name invalid"

    def test_push_pull_empty(self):
        """
        Tests if box is empty.

        """
        username, password = createUser()
        message = b"Hello World!"

        pssst = Pssst(username, password)
        pssst.create()
        pssst.push([username], message)
        pssst.pull()

        assert pssst.pull() == None

    def test_pull_empty(self):
        """
        Tests if box is empty.

        """
        pssst = Pssst(*createUser())
        pssst.create()

        assert pssst.pull() == None

    def test_password_wrong(self):
        """
        Tests if a password is wrong.

        """
        with pytest.raises(Exception) as ex:
            username, password = createUser()
            Pssst(username, "foobar")
            Pssst(username, "xxxxxx")

        assert str(ex.value) == "Password wrong"


class TestFuzzy:
    """
    Tests with fuzzy data.

    Methods
    -------
    test_fuzzy()
        Tests if fuzzy data is returned correctly.

    """
    def test_fuzzy(self):
        """
        Tests if fuzzy data is returned correctly.

        Notes
        -----
        The data will be generated with random content in sizes from zero
        bytes up to 8 kilobytes.

        """
        for size in [2 ** n for n in range(0, 13)]:
            username, password = createUser()
            blob = os.urandom(size)
            pssst = Pssst(username, password)
            pssst.create()
            pssst.push([username], blob)

            assert blob == pssst.pull()


def main(*args):
    """
    Starts unit testing.

    Parameters
    ----------
    param args : tuple of strings, optional
        Arguments passed to py.test.

    """
    return pytest.main(list(args))


if __name__ == "__main__":
    sys.exit(main(*sys.argv))

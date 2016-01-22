#!/usr/bin/env python
"""
Copyright (C) 2013-2015  Christian & Christian <hello@pssst.name>
Copyright (C) 2015-2016  Christian Uhsat <christian@uhsat.de>

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


def create_profile(length=16):
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


class TestPssstName:
    """
    Tests Pssst name parsing with the test cases:

    * User name parse minimum
    * User name parse maximum
    * User name is invalid

    Methods
    -------
    test_name_minimum()
        Tests if a minimum name is parsed correctly.
    test_name_maximum()
        Tests if a maximum name is parsed correctly.
    test_name_invalid()
        Tests if a name is invalid.

    """
    def test_name_minimum(self):
        """
        Tests if name is parsed correctly.

        """
        name = Pssst.Name("me")

        assert name.profile == ("me", None, None)
        assert str(name) == "pssst.me"

    def test_name_maximum(self):
        """
        Tests if name is parsed correctly.

        """
        name = Pssst.Name(" pssst.Test:Pa55w0rd!@http://server.org:8080 ")

        assert name.profile == ("test", "Pa55w0rd!", "http://server.org:8080")
        assert str(name) == "pssst.test"

    def test_name_invalid(self):
        """
        Tests if name is invalid.

        """
        with pytest.raises(Exception) as ex:
            Pssst.Name("Invalid.User.Name")

        assert str(ex.value) == "User name invalid"


class TestPsssstKey:
    """
    Tests Pssst key methods with this test cases:

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
            pssst = Pssst(*create_profile())
            pssst.pull()

        assert str(ex.value) == "Verification failed"

    def test_request_verify_signature_invalid(self):
        """
        Tests if request signature is invalid.

        """
        original = Pssst._Key.sign

        with pytest.raises(Exception) as ex:
            Pssst._Key.sign = lambda self, data: ("!", b"!")

            pssst = Pssst(*create_profile())
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

            pssst = Pssst(*create_profile())
            pssst.create()
            pssst.pull()

        Pssst._Key.sign = original

        assert str(ex.value) == "Verification failed"


class TestPsssstKeyStorage:
    """
    Tests Pssst key storage with the test cases:

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
        username1, password1 = create_profile()
        username2, password2 = create_profile()

        pssst1 = Pssst(username1, password1)
        pssst1.create()

        pssst2 = Pssst(username2, password2)
        pssst2.create()

        pssst1.push(username1, "Hello World !")
        pssst1.push(username2, "Hello World !")

        keys = ["id_rsa", username1, username2]

        assert sorted(pssst1.keys.list()) == sorted(keys)


class TestPssst:
    """
    Tests Pssst user commands with this test cases:

    * User create
    * User create failed, already exists
    * User delete
    * User delete, user was deleted
    * User find
    * User find failed, user was deleted
    * User find failed, user not found
    * User push self
    * User push user
    * User pull empty before
    * User pull empty after
    * Password wrong

    Methods
    -------
    test_create_profile()
        Tests if an user can be created.
    test_create_profile_already_exists()
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
    test_push_self()
        Tests if a message could be pushed to sender.
    test_push_user()
        Tests if a message could be pushed to receiver.
    test_pull_empty_before()
        Tests if an user box is empty before pulling.
    test_pull_empty_after()
        Tests if an user box is empty after pulling.
    test_password_wrong()
        Tests if a password is wrong.

    """
    def test_create_profile(self):
        """
        Tests if an user can be created.

        """
        pssst = Pssst(*create_profile())
        pssst.create()

    def test_create_profile_already_exists(self):
        """
        Tests if an user already exists.

        """
        with pytest.raises(Exception) as ex:
            pssst = Pssst(*create_profile())
            pssst.create()
            pssst.create()

        assert str(ex.value) == "User already exists"

    def test_delete_user(self):
        """
        Tests if an user can be deleted.

        """
        pssst = Pssst(*create_profile())
        pssst.create()
        pssst.delete()

    def test_delete_user_was_deleted(self):
        """
        Tests if an user was deleted.

        """
        with pytest.raises(Exception) as ex:
            pssst = Pssst(*create_profile())
            pssst.create()
            pssst.delete()
            pssst.pull()

        assert str(ex.value) == "User was deleted"

    def test_find_user(self):
        """
        Tests if an user public key can be found.

        """
        username, password = create_profile()
        pssst = Pssst(username, password)
        pssst.create()
        pssst.find(username)

    def test_find_user_was_deleted(self):
        """
        Tests if an user was deleted.

        """
        with pytest.raises(Exception) as ex:
            username, password = create_profile()
            pssst = Pssst(username, password)
            pssst.create()
            pssst.delete()

            pssst = Pssst(*create_profile())
            pssst.find(username)

        assert str(ex.value) == "User was deleted"

    def test_find_user_not_found(self):
        """
        Tests if an user is not found.

        """
        with pytest.raises(Exception) as ex:
            pssst = Pssst(*create_profile())
            pssst.find("usernotfound")

        assert str(ex.value) == "User not found"

    def test_push_self(self):
        """
        Tests if a message could be pushed to sender.

        """
        username, password = create_profile()
        message = b"Echo"

        pssst = Pssst(username, password)
        pssst.create()
        pssst.push(username, message)

        assert pssst.pull() == message

    def test_push_user(self):
        """
        Tests if a message could be pushed to receiver.

        """
        username1, password1 = create_profile()
        username2, password2 = create_profile()
        message = b"Hello World!"

        pssst1 = Pssst(username1, password1)
        pssst1.create()

        pssst2 = Pssst(username2, password2)
        pssst2.push(username1, message)

        assert pssst1.pull() == message

    def test_pull_empty_before(self):
        """
        Tests if an user box is empty before pulling.

        """
        pssst = Pssst(*create_profile())
        pssst.create()

        assert pssst.pull() == None

    def test_push_empty_after(self):
        """
        Tests if an user box is empty after pulling.

        """
        username, password = create_profile()
        message = b"Hello World!"

        pssst = Pssst(username, password)
        pssst.create()
        pssst.push(username, message)
        pssst.pull()

        assert pssst.pull() == None

    def test_password_wrong(self):
        """
        Tests if a password is wrong.

        """
        with pytest.raises(Exception) as ex:
            username, password = create_profile()
            Pssst(username, "right")
            Pssst(username, "wrong")

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
        bytes up to 1 megabyte.

        """
        for size in [2 ** n for n in range(0, 20)]:
            username, password = create_profile()
            blob = os.urandom(size)
            pssst = Pssst(username, password)
            pssst.create()
            pssst.push(username, blob)

            assert blob == pssst.pull()


def main(*args):
    """
    Starts unit testing.

    Parameters
    ----------
    param args : tuple of strings, optional
        Arguments passed to pytest.

    """
    return pytest.main(list(args))


if __name__ == "__main__":
    sys.exit(main(*sys.argv))

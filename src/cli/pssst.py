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
import base64
import io
import json
import os
import re
import sys
import time

from getpass import getpass
from zipfile import ZipFile


try:
    from requests import request
    from requests.exceptions import ConnectionError, Timeout
except ImportError:
    sys.exit("Requires Requests (https://github.com/kennethreitz/requests)")


try:
    from Crypto import Random
    from Crypto.Cipher import AES, PKCS1_OAEP
    from Crypto.Hash import HMAC, SHA256
    from Crypto.PublicKey import RSA
    from Crypto.Signature import PKCS1_v1_5
    from Crypto.Util.py3compat import bchr, bord, tobytes
except ImportError:
    sys.exit("Requires PyCrypto (https://github.com/dlitz/pycrypto)")


__all__, __version__ = ["Pssst"], "2.7.0"


def _encode(data): # Utility shortcut
    return base64.b64encode(data).decode("utf-8")


def _decode(data): # Utility shortcut
    return base64.b64decode(data.encode("utf-8"))


class Pssst:
    """
    Pssst API low level communication class.

    Methods
    -------
    create()
        Creates an user.
    delete()
        Deletes an user.
    find(user)
        Returns the public key of an user.
    pull()
        Pulls a message from the box.
    push(receivers, data)
        Pushes a message into the box.

    """
    class Name:
        """
        Canonical name parser.

        """
        def __init__(self, user, password=None, server=None):
            """
            Initializes the instance with the parsed name.

            Parameters
            ----------
            param user : string
                User name (full or partial).
            param password : string, optional (default is None)
                User private key password.
            param server : string, optional (default is None)
                Server address.

            """
            user = user.strip()

            if not re.match("^(pssst\.)?\w{2,63}(:\S+)?(@\S+)?$", user):
                raise Exception("User name invalid")

            if user.startswith("pssst."):
                user = user[6:]

            if "@" in user and not server:
                user, server = user.split("@", 1)

            if ":" in user and not password:
                user, password = user.split(":", 1)

            self.user = user.lower()
            self.hash = SHA256.new(repr(self).encode("ascii")).hexdigest()
            self.profile = (self.user, password, server)

        def __repr__(self):
            """
            Returns the full name in canonical notation.

            """
            return str("pssst.%s" % self.user)


    class _Key:
        """
        Internal key class providing cryptographic methods.

        Methods
        -------
        private(password)
            Returns the users private key (PEM format).
        public()
            Returns the users public key (PEM format).
        encrypt(data)
            Returns the encrypted data and nonce.
        decrypt(data, nonce)
            Returns the decrypted data.
        verify(data, timestamp, signature)
            Returns if data could be verified with timestamp and signature.
        sign(data)
            Returns the data timestamp and signature.

        Notes
        -----
        This class is not meant to be called externally.

        """
        RSA_SIZE, NONCE_SIZE, GRACE_TIME = 2048, 32 + AES.block_size, 30

        def __init__(self, key=None, password=None):
            try:
                if key:
                    self.key = RSA.importKey(key, password)
                else:
                    self.key = RSA.generate(Pssst._Key.RSA_SIZE)

            except (IndexError, TypeError, ValueError) as ex:
                raise Exception("Password wrong")

        def _epoch(self):
            return int(round(time.time()))

        def private(self, password):
            return self.key.exportKey("PEM", password, 8).decode("ascii")

        def public(self):
            return self.key.publickey().exportKey("PEM").decode("ascii")

        def encrypt(self, data):
            nonce = Random.get_random_bytes(Pssst._Key.NONCE_SIZE)
            size = AES.block_size - (len(data) % AES.block_size)
            data = tobytes(data) + (bchr(size) * size)

            data = AES.new(nonce[:32], AES.MODE_CBC, nonce[32:]).encrypt(data)
            nonce = PKCS1_OAEP.new(self.key).encrypt(nonce)

            return (data, nonce)

        def decrypt(self, data, nonce):
            nonce = PKCS1_OAEP.new(self.key).decrypt(nonce)
            data = AES.new(nonce[:32], AES.MODE_CBC, nonce[32:]).decrypt(data)

            return data[:-bord(data[-1])]

        def verify(self, data, timestamp, signature):
            current, data = self._epoch(), data.encode("utf-8")

            hmac = HMAC.new(str(timestamp).encode("ascii"), data, SHA256)
            hmac = SHA256.new(hmac.digest())

            if abs(timestamp - current) <= Pssst._Key.GRACE_TIME:
                return PKCS1_v1_5.new(self.key).verify(hmac, signature)
            else:
                return False

        def sign(self, data):
            current, data = self._epoch(), data.encode("utf-8")

            hmac = HMAC.new(str(current).encode("ascii"), data, SHA256)
            hmac = SHA256.new(hmac.digest())

            signature = PKCS1_v1_5.new(self.key).sign(hmac)

            return (current, signature)


    class _KeyStorage:
        """
        Internal storage class for public and private keys.

        Methods
        -------
        delete()
            Deletes the users key storage.
        list()
            Returns an alphabetical list of all key entries.
        load(entry)
            Returns a key.
        save(entry, key)
            Saves a key.

        Notes
        -----
        This class is not meant to be called externally.

        """
        def __init__(self, api, user, password):
            self.scheme = "%s"
            self.user = user
            self.file = os.path.join(os.path.expanduser("~"), repr(self))

            if os.path.exists(self.file):
                self.key = Pssst._Key(self.load("id_rsa"), password)
            else:
                self.key = Pssst._Key()
                self.save("id_rsa", self.key.private(password))

            self.scheme = re.sub("^(?i)https?://(.+)", "\g<1>/%s.pub", api)

        def __repr__(self):
            return ".pssst." + self.user

        def __bool__(self):
            return self.__nonzero__()

        def __nonzero__(self):
            return os.path.exists(self.file)

        def _has_api(self):
            return "id_rsa" in self.list()

        def _set_api(self, key):
            if key:
                self.save("id_rsa", key)

            self.api = Pssst._Key(self.load("id_rsa"))

        def delete(self):
            os.remove(self.file)

        def list(self):
            with ZipFile(self.file, "r") as file:
                keys = []

                # Filter out APIs
                for key in file.namelist():
                    if key.startswith(self.scheme.rsplit("/")[0]):
                        keys.append(re.sub("^.+/(.+)\.pub$", "\g<1>", key))

                return keys

        def load(self, entry):
            with ZipFile(self.file, "r") as file:
                return file.read(self.scheme % entry)

        def save(self, entry, key):
            with ZipFile(self.file, "a") as file:
                file.writestr(self.scheme % entry, key)


    def __init__(self, username, password, server=None):
        """
        Initializes the instance with an user object.

        Parameters
        ----------
        param username : string
            User name.
        param password : string
            User private key password.
        param server : string, optional (default is None)
            Server address.

        Raises
        ------
        Exception
            Because the password is required.

        Notes
        -----
        If the environment variable 'PSSST' exists, it will be used as the API
        address and port. If a server is given, it will override the API.

        """
        API = "http://localhost:62221"

        if not password:
            raise Exception("Password required")

        if not server:
            server = os.environ.get("PSSST", API)

        self.api = server
        self.name = Pssst.Name(username)
        self.keys = Pssst._KeyStorage(self.api, self.name.user, password)

        # Cache server public key
        key = None if self.keys._has_api() else self.__request_url("key")

        self.keys._set_api(key)

    def __repr__(self):
        """
        Returns the client identifier.

        Returns
        -------
        string
            The client identifier.

        """
        return "Pssst CLI " + __version__

    def __request_api(self, method, path, data=None):
        """
        Returns the result of an API request (signed and verified).

        Parameters
        ----------
        param method : string
            Request method.
        param path : string
            Request path.
        param data : JSON, optional (default is None)
            Request data.

        Returns
        -------
        string
            The response body.

        Raises
        ------
        Exception
            Because the user was deleted.
        Exception
            Because the signature is missing.
        Exception
            Because the signature is corrupt.
        Exception
            Because the verification has failed.

        Notes
        -----
        Please see __init__ method.

        """
        if not self.keys:
            raise Exception("User was deleted")

        body = str(json.dumps(data, separators=(",", ":"))) if data else ""

        timestamp, signature = self.keys.key.sign(body)

        response = request(method, "%s/2/%s" % (self.api, path), data=body,
            headers={
                "x-pssst-hash": "%s; %s" % (timestamp, _encode(signature)),
                "content-type": "application/json" if data else "text/plain",
                "user-agent": repr(self)
            }
        )

        mime = response.headers.get("content-type", "text/plain")
        head = response.headers.get("x-pssst-hash")
        body = response.text

        if not re.match("^[0-9]+; ?[A-Za-z0-9\+/]+=*$", head):
            raise Exception("Verification failed")

        timestamp, signature = head.split(";", 1)
        timestamp, signature = int(timestamp), _decode(signature)

        if not self.keys.api.verify(body, timestamp, signature):
            raise Exception("Verification failed")

        if response.status_code not in [200, 204]:
            raise Exception(body)

        if mime.startswith("application/json"):
            body = response.json()

        return body

    def __request_url(self, path):
        """
        Returns the result of an URL request (without any checks).

        Parameters
        ----------
        param path : string
            Requested path.

        Returns
        -------
        string
            The response body.

        Raises
        ------
        ConnectionError
            Because the file was not found.

        Notes
        -----
        Please see __init__ method.

        """
        response = request("GET", "%s/%s" % (self.api, path),
            headers={
                "user-agent": repr(self)
            }
        )

        if response.status_code != 200:
            raise ConnectionError("Not Found")

        return response.text

    def create(self):
        """
        Creates an user.

        """
        body = {"key": self.keys.key.public()}

        self.__request_api("POST", self.name.hash, body)

    def delete(self):
        """
        Deletes an user.

        Notes
        -----
        If the user was deleted, the object can not be used any further and
        any API call will result in an error. The key storage is also deleted.

        """
        self.__request_api("DELETE", self.name.hash)
        self.keys.delete()

    def find(self, user):
        """
        Returns the public key of an user.

        Parameters
        ----------
        param user : string
            The user name.

        Returns
        -------
        string
            PEM formatted public key.

        """
        return self.__request_api("GET", Pssst.Name(user).hash + "/key")

    def pull(self):
        """
        Pulls a message from the box.

        Returns
        -------
        byte string or None
            The message data, None if empty.

        """
        data = self.__request_api("GET", self.name.hash)

        if data:
            nonce = _decode(data["nonce"])
            data = _decode(data["data"])

            return self.keys.key.decrypt(data, nonce)

    def push(self, user, data):
        """
        Pushes a message into a box.

        Parameters
        ----------
        param user : string
            The user name.
        param data : byte string
            The message data.

        """
        name = Pssst.Name(user)

        # Cache user public key
        if name.user not in self.keys.list():
            self.keys.save(name.user, self.find(name.user))

        body, nonce = Pssst._Key(self.keys.load(name.user)).encrypt(data)
        body = {
            "nonce": _encode(nonce),
            "data": _encode(body)
        }

        self.__request_api("PUT", name.hash, body)


def usage(text, *args):
    """
    Prints the usage colored.

    Parameters
    ----------
    param text : string
        Usage text to print.
    param args: list of strings
        Usage parameters.

    Notes
    -----
    Color is only used on POSIX compatible systems.

    """
    for line in (text % args).split("\n")[1:-1]:
        line = line[4:]

        if os.name in ["posix"]:

            # Color description
            if re.match("^.* version \d+\.\d+\.\d+$", line):
                line = line.replace("version", "version\x1B[34;1m")
                line = "\x1B[39;1m%s\x1B[0m" % line

            # Color list titles
            elif re.match("^[A-Za-z ]+:$", line):
                line = "\x1B[34m%s\x1B[0m" % line

            # Color list points
            elif re.match("^  (-.|[a-z]+)", line):
                line = line.replace("   ", "   \x1B[37;0m")
                line = "\x1B[34;1m%s\x1B[0m" % line

        print(line)


def main(script, command="--help", username=None, receiver=None, *message):
    """
          __________                  ___
         /  ____   /_________________/  /__
        /  /___/  / ____/ ____/ ____/  ___/
       /  _______/___  /___  /___  /  /__
      /__/      /_____/_____/_____/_____/

      CLI version %s

    Usage:
      %s [option|command] [-|username:password@server] [receiver message...]

    Options:
      -h, --help      Shows the usage
      -l, --license   Shows the license
      -v, --version   Shows the version

    Available commands:
      create   Create an user
      delete   Delete an user
      pull     Pull a message
      push     Push a message

    Report bugs to <christian@uhsat.de>
    """
    try:
        profile = os.path.join(os.path.expanduser("~"), ".pssst")

        if username == "-" and os.path.exists(profile):
            username = io.open(profile).read()

        if username:
            user, password, server = Pssst.Name(username).profile

            if not password:
                password = getpass("Password (hidden): ")

            pssst = Pssst(user, password, server)

        if command in ("/?", "-h", "--help", "help"):
            usage(main.__doc__, __version__, os.path.basename(script))

        elif command in ("-l", "--license"):
            print(__doc__.strip())

        elif command in ("-v", "--version"):
            print("Pssst CLI " + __version__)

        elif command in ("--create", "create") and username:
            pssst.create()
            print("Created %s" % pssst.name)

        elif command in ("--delete", "delete") and username:
            pssst.delete()
            print("Deleted %s" % pssst.name)

        elif command in ("--pull", "pull") and username:
            data = pssst.pull()

            if data:
                print(data.decode("utf-8"))

        elif command in ("--push", "push") and username and receiver:
            pssst.push(receiver, " ".join(message))
            print("Message send")

        else:
            print("Unknown command or username not given: " + command)
            print("Please use --help for help on usage.")
            return 2 # Incorrect usage

    except KeyboardInterrupt:
        print("exit")

    except ConnectionError:
        return "Error: API connection failed"

    except Timeout:
        return "Error: API connection timeout"

    except Exception as ex:
        return "Error: %s" % ex


if __name__ == "__main__":
    sys.exit(main(*sys.argv))

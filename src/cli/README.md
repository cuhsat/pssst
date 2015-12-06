CLI
===
Pssst command line interface.

Usage
-----
```
$ pssst [option|command] [username:password] [receiver message...]
```

Start
-----
Just run the `pssst.py` script to start the CLI:

```
$ pssst.py
```

All user specific data is stored as zip files named `.pssst.<user>` in the
users home directory.

If the file `.pssst` exists in the users home directory, its contents will be
used as the default username and password.

If the environment variable `PSSST` exists, it will be used as the API address
and port.

```
$ export PSSST=http://localhost:62421
```

Install
-------
At least [required](pssst.pip):

* Python 2.7.3
* Requests 2.0.1
* PyCrypto 2.6.1

> If you use Python 2.7 the pyASN1, pyOpenSSL and ndg-httpsclient packages are
> also required for verified HTTPS connections.

----
Please use the `--help` option to show further help.

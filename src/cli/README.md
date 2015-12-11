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

> The server address can be set via the `PSSST` environment variable.
> All user specific data is stored as zip files named `.pssst.<user>` in the
> users home directory. If a user profile file named `.pssst` exists in the
> users home directory, its contents will be used as the default username and
> password if you use `-` as username.

Install
-------
[Required](pssst.pip) at least:

* Python 2.7 / 3.3
* Requests 2.0
* PyCrypto 2.6

> If you use Python 2.7 the pyASN1, pyOpenSSL and ndg-httpsclient
> packages are also required for verified HTTPS connections.

----
Please use the `--help` option for further help.
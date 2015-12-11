CLI
===
Pssst command line interface. [Requirements](pssst.pip)

Usage
-----
```
$ pssst [option|command] [username:password] [receiver message...]
```

The server address must be set via the `PSSST` environment variable.

Files
-----
All user specific data is stored in zip files named `~/.pssst.<user>`.
If a user profile file named `~/.pssst` exists, its contents will be 
used for the username and password if you use the `-` user alias.

----
Please use the `--help` option for further help.

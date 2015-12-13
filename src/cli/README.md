Pssst CLI
=========
All user specific data is stored in zip files named `~/.pssst.<user>`.
If also a user profile file named `~/.pssst` exists, its contents will
be used for username and password if you use the `-` user alias.

Usage
-----
```
$ pssst [option|command] [username:password|-] [receiver message...]
```

The server address must be set via the `PSSST` environment variable.

----
[Requirements](pssst.pip) | 
Please use the `--help` option for further help.

CLI
===
If an user profile file named `.pssst` exists, the path to this file can be 
used instead of the username and password as a shortcut. All generated files
will be stored in the users home directory.

Usage
-----
```
$ pssst [option|command] [~|username:password@server] [receiver message...]
```

The server address must be specified with the user name or set via the `PSSST`
environment variable.

----
[Requirements](../src/cli/pssst.pip) | Please use the `--help` option for 
further help.

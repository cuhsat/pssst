CLI
===
If the user profile file `~/.pssst` exists, its contents will be used by
the `-` user shortcut as username and password. All generated files will
be stored in the users home directory.

Usage
-----
```
$ pssst [option|command] [-|username:password] [receiver message...]
```

The server address must be set via the `PSSST` environment variable.

----
[Requirements](../src/cli/pssst.pip) | Please use the `--help` option for 
further help.
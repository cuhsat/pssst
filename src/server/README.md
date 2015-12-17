Server
======
If you are using Heroku, the server can easily be deployed using this custom
[buildpack](https://github.com/cuhsat/heroku-buildpack-pssst) by clicking
[here](https://heroku.com/deploy?template=https://github.com/cuhsat/pssst).

> Please note, that (for now) this server was designed to be run only by one
> Heroku *dyno* per app. Every time the *dyno* restarts, the private key will
> be generated anew.

Usage
-----
```
$ npm start [option]
```

The default server port is `62421` and can be changed via `config.json`.

----
[Required](package.json) | Please use the `--help` option for further help.
Server
======
If you are using Heroku, the server can easily be deployed using this custom
[buildpack](https://github.com/cuhsat/heroku-buildpack-pssst) by clicking
[here](https://heroku.com/deploy?template=https://github.com/cuhsat/pssst).

> Please note, if running on Heroku, the servers private key must be set via
> the `PSSST_KEY` config variable as Base64 encoded string. If not, the key
> will be generated each time the *Dyno* restarts.

Usage
-----
```
$ npm start [option]
```

The default server port is `62421` and can be changed via `config.json`.

----
[Requirements](../src/server/package.json) | Please use the `--help` option 
for further help.
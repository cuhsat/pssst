![Pssst](http://www.gravatar.org/avatar/2aae9030772d5b59240388522f91468f?s=96)

Pssst ![](https://travis-ci.org/cuhsat/pssst.svg)
=====
Pssst is a simple and secure way to exchange information. We do not provide
services by our self, but we provide you with the tools to start your own
service. These tools build upon open-source software and use strong end-to-end
encryption.

```
$ pssst push me you "Hello"
```

Pssst comes as a [CLI](src/cli) and [Server](src/server) and can easily 
be deployed to [Heroku](https://www.heroku.com) using this custom 
[Buildpack](https://github.com/cuhsat/heroku-buildpack-pssst).

API
---
Our full [API](/doc/api.md) specification can be found under `doc`.

CVE
---
No security advisories or bugs are known as of today.

License
-------
Released under the terms of the [GPLv3](LICENSE) license.

----
Based on [Pssst](https://github.com/pssst/pssst) by Christian & Christian.

API
===
Our REST API is based on HTTP and designed to be lean and mean. All messages
will be stored protocol agnostic. You can also add more fields to the HTTP
body. The only field required by the server is `head.user`. All clients are
requested to send an unique `user-agent` header per implementation.

> A [RAML](http://raml.org) specification of the [API](api.raml) is available
> under `doc/api.raml`.

Constraints
-----------
### User Names

All user names are specified by this format:

`pssst.<user>`

All user names must be between 2 and 63 characters long and must only contain
of the lowercase letters a-z and numbers. The service prefix `pssst.` can be
omitted, but should be specified for clarity reasons.

### User Limit

Every user has a fix limit of `1 MB` overall buffered data. This includes all
user specific data, such as the public key and messages. The size of a message
is not limited separately. Only messages not yet pulled by the user will count
to this limit.

Cryptography
------------
### Encoding

All data are encoded in UTF-8 and exchanged in either JSON or plain text
format with HTTPS requests / responses. Please refer to the mime type in the
HTTP `content-type` header to decide which format is returned. Server errors
will always be returned in plain text. Line endings must only consists of a
`Line Feed` character.

### Encryption

Encryption of the message `nonce` and `body` is done in the following steps:

1. Generate cyptographically secure 48 random bytes as message code.
2. Encrypt the data with AES-256 (CBC mode, PKCS#7 padding) using the first 32
   bytes from the message code as key and the last 16 bytes as IV.
3. Encrypt the message code with PKCS#1 OAEP and the receivers public key.

Please be aware:

> The message code is called _nonce_ for a reason. Never use it twice.

RSA keys are requiered to be 2048 bit strong and encoded in PEM / PKCS#8.

### Decryption

Decryption of the received `nonce` and `body` is done in the following steps:

1. Decrypt the nonce with PKCS#1 OAEP and the receivers private key.
2. Decrypt the data with AES-256 (CBC mode, PKCS#7 padding) using the first 32
   bytes from the decrypted message code as key and the last 16 bytes as IV.

All encrypted data is exchanged as JSON object in the request / response body
within `head` and `body` fields. The `head.nonce` and `body` fields are both
encoded in standard Base64 with padding and omitted line breaks.

### Authentication

Authentication for client and server is done via the HTTP `content-hash`
header. This header must be set for all client API request, except `find`.
The format of this header is specified as:

`content-hash: <timestamp>; <signature>`

Where `timestamp` is the EPOCH without decimals of the request / response
and `signature` the calculated and signed hash of the HTTP body encoded in
standard Base64 with padding. Calculation of the hash is done in the following
steps:

1. Create a SHA-256 HMAC of the HTTP body with the timestamp string as key.
2. Create a SHA-256 hash of the resulting HMAC one more time.
3. Sign the resulting hash with the senders private key using PKCS#1 v1.5.

To verify a request / response, calculate its hash as described above in the
steps 1 and 2. And verify it with the senders public key using PKCS#1 v1.5.

The grace period for requests / responses to be verified is 30 seconds. Which
derives to -30 or +30 seconds from the actual EPOCH at the time of
processing.

For further information about the used cryptographical methods, please consult
the RFCs listed in the appendix.

Independent Actions
-------------------
List of implemented actions:

* Get server version
* Get server key

All server action must never be signed. Only required HTTP headers are listed.

### Version

Returns the servers protocol version.

#### Request

```
GET / HTTP/1.1
host: <api>
user-agent: <app>
```

#### Response

```
HTTP/1.1 200 OK
content-type: text/plain
content-hash: <timestamp>; <signature>

Pssst <version>
```

### Key

Returns the servers public key in PEM format.

#### Request

```
GET /time HTTP/1.1
host: <api>
user-agent: <app>
```

#### Response

```
HTTP/1.1 200 OK
content-type: text/plain
content-hash: <timestamp>; <signature>

<key>
```

User Specific Actions
---------------------
List of implemented actions:

* Create user
* Delete user
* Find user key
* Pull a message
* Push a message

All user actions, except `find`, must be signed with the senders private key.
Only required HTTP headers are listed.

### Create

Creates a new user with the given public key. The given key must be in PEM
format.

#### Request

```
POST /1/<user> HTTP/1.1
host: <api>
user-agent: <app>
content-type: application/json
content-hash: <timestamp>; <signature>

{"key":"<key>"}
```

#### Response

```
HTTP/1.1 200 OK
content-type: text/plain
content-hash: <timestamp>; <signature>

User created
```

### Delete

Deletes the user. All messages of the user will also be deleted. Messages
pushed by the user will not be affected. The name of this user will be locked
and can not be used afterwards for by other users.

#### Request

```
DELETE /1/<user> HTTP/1.1
host: <api>
user-agent: <app>
content-hash: <timestamp>; <signature>
```

#### Response

```
HTTP/1.1 200 OK
content-type: text/plain
content-hash: <timestamp>; <signature>

User disabled
```

### Find

Returns the users public key in PEM format.

#### Request

```
GET /1/<user>/key HTTP/1.1
host: <api>
user-agent: <app>
```

#### Response

```
HTTP/1.1 200 OK
content-type: text/plain
content-hash: <timestamp>; <signature>

<key>
```

### Pull

Returns the next message from the users box. Messages will be pulled in order
from first to last.

#### Request

```
GET /1/<user>/ HTTP/1.1
host: <api>
user-agent: <app>
content-hash: <timestamp>; <signature>
```

#### Response

```
HTTP/1.1 200 OK
content-type: application/json
content-hash: <timestamp>; <signature>

{"head":{"nonce":"<nonce>"},"body":"<data>"}
```

### Push

Pushes a message into the users box. The sender will be authenticated with the
`head.user` field.

#### Request

```
PUT /1/<user>/ HTTP/1.1
host: <api>
user-agent: <app>
content-type: application/json
content-hash: <timestamp>; <signature>

{"head":{"nonce":"<nonce>","user":"<sender>"},"body":"<data>"}
```

#### Response

```
HTTP/1.1 200 OK
content-type: text/plain
content-hash: <timestamp>; <signature>

Message pushed
```

Appendix
--------
* [RFC 2313 (PKCS#1)](https://tools.ietf.org/html/rfc2313)
* [RFC 2315 (PKCS#7)](https://tools.ietf.org/html/rfc2315)
* [RFC 5208 (PKCS#8)](https://tools.ietf.org/html/rfc5208)

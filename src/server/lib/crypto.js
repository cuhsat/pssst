/**
 * Copyright (C) 2013-2015  Christian & Christian  <hello@pssst.name>
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program. If not, see <http://www.gnu.org/licenses/>.
 *
 *
 *
 * Cryptographical functions for signing and verifying data.
 */
module.exports = function Crypto() {
  var fs = require('fs');
  var rsa = require('node-rsa');
  var crypto = require('crypto');

  var GRACE = 30;
  var FORMAT = 'base64';

  var RSA_SIZE = 2048;
  var RSA_HASH = 'sha256';
  var RSA_FORMAT = 'pkcs1';
  var RSA_SCHEME = 'pkcs1-sha256';

  var ID_RSA = __dirname + '/../id_rsa';
  var ID_PUB = __dirname + '/../id_rsa.pub';

  // Heroku support
  if (process.env.PSSST_KEY) {
    var key = new rsa(new Buffer(process.env.PSSST_KEY, 'base64'));
  } else if (fs.existsSync(ID_RSA)) {
    var key = new rsa(fs.readFileSync(ID_RSA), RSA_FORMAT, RSA_SCHEME);
  } else {
    var key = new rsa({b: RSA_SIZE});

    fs.writeFileSync(ID_RSA, key.exportKey('private'));
    fs.writeFileSync(ID_PUB, key.exportKey('public'));
  }

  if (!key.isPrivate()){
    throw new Error('Key has no private part');
  }

  if (!key.isPublic()) {
    throw new Error('Key has no public part');
  }

  if (key.getKeySize() < RSA_SIZE) {
    throw new Error('Key size too small');
  }

  /**
   * Returns the current timestamp (EPOCH).
   *
   * @return {Number} the timestamp
   */
  function getTimestamp() {
    return Number((new Date()).getTime() / 1000).toFixed(0);
  }

  /**
   * Returns the data HMAC.
   *
   * @param {Object} the data
   * @param {Number} timestamp
   * @return {Object} timestamp and signature
   */
  function createHMAC(data, timestamp) {
    var hmac, timestamp = timestamp || getTimestamp();

    hmac = crypto.createHmac(RSA_HASH, timestamp.toString());
    hmac.update(data.toString());

    return {
      timestamp: timestamp,
      signature: hmac.digest(FORMAT)
    };
  };

  /**
   * Returns the data signature.
   *
   * @param {Object} the data
   * @return {Object} timestamp and signature
   */
  this.sign = function sign(data) {
    if (data instanceof Object) {
      data = JSON.stringify(data);
    }

    var hmac = createHMAC(data);

    return {
      timestamp: hmac.timestamp,
      signature: key.sign(hmac.signature, FORMAT, FORMAT)
    };
  };

  /**
   * Returns if data could be verified.
   *
   * @param {Object} the data
   * @param {Object} the data HMAC
   * @param {String} public key (PEM format)
   * @return {Boolean} true if verified
   */
  this.verify = function verify(data, hmac, pem) {
    if (data instanceof Object) {
      data = JSON.stringify(data);
    }

    var timestamp = parseInt(hmac.timestamp, 10);
    var signature = hmac.signature;

    // Assert the timestamp is in grace time
    if (Math.abs(timestamp - getTimestamp()) > GRACE) {
      return false;
    }

    var hmac = createHMAC(data, timestamp);

    try {
      return new rsa(pem).verify(hmac.signature, signature, FORMAT, FORMAT);
    } catch (err) {
      return false; // OpenSSL error
    }
  };

  // Key files
  this.id_rsa = ID_RSA;
  this.id_pub = ID_PUB;

  return this;
}()

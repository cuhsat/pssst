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
 * HTTP server with authentication.
 *
 * @param {Object} config object
 * @param {Function} callback
 */
module.exports = function Server(config, callback) {
  var fs = require('fs');
  var util = require('util');
  var parser = require('body-parser');
  var express = require('express');

  var info = require('../package.json');
  var debug = require('./debug.js');
  var redis = require('./redis.js');
  var pssst = require('./pssst.js');
  var crypto = require('./crypto.js');

  var HEADER = 'x-pssst-hash';

  var server, port = Number(process.env.PORT || config.port);

  /**
   * Returns the new header.
   *
   * @param {Object} signature
   * @return {String} the header
   */
  function buildHeader(signature) {
    return util.format('%s; %s', signature.timestamp, signature.signature);
  }

  /**
   * Returns the parsed signature.
   *
   * @param {String} the header
   * @return {Object} signature
   */
  function parseHeader(header) {
    var token = header.split(';', 2);

    return {
      timestamp: token[0].trim(),
      signature: token[1].trim()
    };
  }

  /**
   * Adds authentication to HTTP(S) requests/responses.
   *
   * @param {Object} database wrapper
   * @param {Object} request
   * @param {Object} response
   * @param {Object} next handler
   */
  function auth(db, req, res, next) {
    if (JSON.stringify(req.body) === '{}') {
      req.body = '';
    }

    /**
     * Verifies a HTTP(S) request.
     *
     * @param {String} hashed user name or public key
     * @param {Function} callback
     */
    req.verify = function verify(hash, callback) {
      function verify(key) {
        var header = req.headers[HEADER];

        // Assert a public key exists
        if (!key) {
          return res.sign(404, 'Verification failed');
        }

        // Assert the signature format is valid
        if (!new RegExp('^[0-9]+; ?[A-Za-z0-9\+/]+=*$').test(header)) {
          return res.sign(400, 'Verification failed');
        }

        // Assert the signature of the body is valid
        if (!crypto.verify(req.body, parseHeader(header), key)) {
          return res.sign(401, 'Verification failed');
        }

        callback();
      }

      // Load public key from database if not given
      if (hash.indexOf('PUBLIC KEY') < 0) {
        db.get(hash, function get(err, val) {
          if (!err) {
            verify(val ? val.key : null);
          } else {
            res.error(err);
          }
        });
      } else {
        verify(hash);
      }
    };

    /**
     * Sends a signed HTTP(S) response.
     *
     * @param {String} response status
     * @param {String} response body
     * @return {Boolean} always true
     */
    res.sign = function sign(status, body) {
      body = body || '';

      res.setHeader(HEADER, buildHeader(crypto.sign(body)));
      res.status(status).send(body);

      return true;
    };

    /**
     * Sends a signed HTTP(S) error.
     *
     * @param {Object} error or exception
     * @return {Boolean} always true
     */
    res.error = function error(err) {
      console.error(err.stack || err);

      // Don't leak information
      if (config.debug > 0) {
        return res.sign(500, String(err));
      } else {
        return res.sign(500);
      }
    }

    next();
  }

  app = express();
  app.set('json spaces', 0);
  app.use(parser.json());

  redis(config.db, function redis(err, db) {
    if (!err) {
      var level = Number(process.env.PSSST_DEBUG || config.debug);

      // Debug hook
      app.use(function hook(req, res, next) {
        debug(level, req, res, next);
      });

      // Error hook
      app.use(function hook(err, req, res, next) {
        if (res.error) {
          res.error(err);
        } else {
          console.error(err.stack || err);
        }
      });

      // Authentication hook
      app.use(function (req, res, next) {
        auth(db, req, res, next);
      });

      // Add routes
      pssst(app, db);

      // Return server public key
      app.get('/key', function key(req, res) {
        res.sign(200, crypto.key);
      });

      // Return server version
      app.get('/', function index(req, res) {
        res.sign(200, "Pssst " + info['version']);
      });

      // Return file not found
      app.get('*', function other(req, res) {
        res.sign(404, 'Not found');
      });

      server = app.listen(port);
      server.on('error', function error(err) {
        if (err.code != 'EADDRINUSE') {
          console.error(err.stack || err);
        }
      });

      callback(null, server);
    } else {
      callback(err);
    }
  });
}

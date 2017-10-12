/**
 * Copyright (C) 2013-2015  Christian & Christian <hello@pssst.name>
 * Copyright (C) 2015-2017  Christian Uhsat <christian@uhsat.de>
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
 * Pssst app.
 *
 * @param {Object} express app
 * @param {Object} database wrapper
 */
module.exports = function Pssst(app, db) {
  var LIMIT = 1024 * 1024; // 1 MB

  /**
   * Pssst API (version 2).
   */
  var api = {
    /**
     * Handles a request and returns a response.
     *
     * @param {Object} request
     * @param {Object} response
     * @param {Function} callback
     * @param {Mixed} authentication
     */
    request: function request(req, res, callback, auth) {

      // Assert the hashed user name is valid
      if (!new RegExp('^[a-z0-9]{64}$').test(req.params.hash)) {
        return res.sign(400, 'Hash invalid');
      }

      // Bypass sender verification (for key requests only)
      if (auth === false) {
        req.verify = function pass(unused, callback) {
          callback();
        };
      }

      // Authenticate user of this request
      req.verify(auth || req.params.hash, function verify() {
        db.get(req.params.hash, function get(err, user) {
          if (err) {
            return res.error(err);
          }

          // Assert the user exists
          if (user === null && req.method !== 'POST') {
            return res.sign(404, 'User not found');
          }

          // Assert the user is not deleted
          if (user !== null && user.key === null) {
            return res.sign(410, 'User was deleted');
          }

          callback(user);
        });
      });
    },

    /**
     * Persists an user and returns a response.
     *
     * @param {Object} request
     * @param {Object} response
     * @param {Object} user
     * @param {String} response body
     */
    respond: function respond(req, res, user, body) {
      db.set(req.params.hash, user, function set(err) {
        if (err) {
          return res.error(err);
        } else if (body) {
          return res.sign(200, body);
        } else {
          return res.sign(204);
        }
      })
    }
  };

  /**
   * Creates an new user with the given key.
   *
   * @summary signed request
   * @summary signed response
   */
  app.post('/2/:hash', function create(req, res) {
    api.request(req, res, function request(user) {

      // Assert the user does not already exist
      if (user !== null) {
        return res.sign(409, 'User already exists');
      }

      // Assert the given key is a public key
      if (req.body.key.indexOf('PUBLIC KEY') < 0) {
        return res.sign(400, 'User key invalid');
      }

      // User object
      user = {
        key: req.body.key,
        box: []
      };

      return api.respond(req, res, user, 'User created');
    }, req.body.key);
  });

  /**
   * Deletes an existing user (disables only).
   *
   * @summary signed request
   * @summary signed response
   */
  app.delete('/2/:hash', function disable(req, res) {
    api.request(req, res, function request(user) {
      user.key = user.box = null;

      return api.respond(req, res, user, 'User deleted');
    });
  });

  /**
   * Returns the public key of an user (non persisting).
   *
   * @summary normal request
   * @summary signed response
   */
  app.get('/2/:hash/key', function key(req, res) {
    api.request(req, res, function request(user) {
      return res.sign(200, user.key);
    }, false);
  });

  /**
   * Pushes a new message into the box.
   *
   * @summary signed request
   * @summary signed response
   */
  app.put('/2/:hash/box', function push(req, res) {
    api.request(req, res, function request(user) {

      // Assert the user is within the limit
      if (JSON.stringify(user).length >= LIMIT) {
        return res.sign(413, 'User reached limit');
      }

      user.box.push(req.body);

      return api.respond(req, res, user, 'Message send');
    }, false);
  });

  /**
   * Pulls all messages from the box.
   *
   * @summary signed request
   * @summary signed response
   */
  app.get('/2/:hash/box', function pull(req, res) {
    api.request(req, res, function request(user) {
      var box = user.box.splice(0, user.box.length);

      return api.respond(req, res, user, box);
    });
  });

  return this;
}

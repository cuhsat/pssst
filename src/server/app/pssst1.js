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
 * Pssst app.
 *
 * @param {Object} express app
 * @param {Object} database wrapper
 * @param {Object} app config
 */
module.exports = function Pssst(app, db, config) {

  // Use config default values if not found
  var allow = config.allow || '.*';
  var quota = config.quota || 536870912; // 512 MB

  /**
   * Pssst API (version 1).
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

      // Assert the user name is valid (error 400)
      if (!new RegExp('^[a-z0-9]{2,63}$').test(req.params.user)) {
        return res.sign(400, 'User name invalid');
      }

      // Bypass sender verification (for key requests only)
      if (auth === false) {
        req.verify = function pass(unused, callback) {
          callback();
        };
      }

      // Verify sender authentication for this request
      req.verify(auth || req.params.user, function verify() {
        db.get(req.params.user, function get(err, user) {

          // Database error
          if (err) {
            return res.error(err);
          }

          // Assert the user object exists (error 404)
          if (user === null && req.method !== 'POST') {
            return res.sign(404, 'User not found');
          }

          // Assert the user is not deleted (error 410)
          if (user !== null && user.key === null) {
            return res.sign(410, 'User was deleted');
          }

          // Handle request
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
      db.set(req.params.user, user, function set(err) {
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
   * Creates an new user with the given public key.
   *
   * Authentication:
   *
   *   Signed request
   *   Signed response
   */
  app.post('/1/:user', function create(req, res) {
    api.request(req, res, function request(user) {

      // Assert the user name is allowed (error 403)
      if (!new RegExp(allow).test(req.params.user)) {
        return res.sign(403, 'User name not allowed');
      }

      // Assert the user does not already exist (error 409)
      if (user !== null) {
        return res.sign(409, 'User already exists');
      }

      // Assert the given key is a public key (error 400)
      if (req.body.key.indexOf('PUBLIC KEY') < 0) {
        return res.sign(400, 'User key invalid');
      }

      // New user object
      user = {
        key: req.body.key,
        max: quota,
        box: []
      };

      return api.respond(req, res, user, 'User created');
    }, req.body.key);
  });

  /**
   * Disables an existing user.
   *
   * Authentication:
   *
   *   Signed request
   *   Signed response
   */
  app.delete('/1/:user', function disable(req, res) {
    api.request(req, res, function request(user) {

      // Zeroing all data, so the user exists but is invalidated
      user.key = user.max = user.box = null;

      return api.respond(req, res, user, 'User deleted');
    });
  });

  /**
   * Returns the public key of an user (non persisting).
   *
   * Authentication:
   *
   *   No verification
   *   Signed response
   */
  app.get('/1/:user/key', function key(req, res) {
    api.request(req, res, function request(user) {
      return res.sign(200, user.key);
    }, false);
  });

  /**
   * Pushes a new message into the box.
   *
   * Authentication:
   *
   *   Signed request by sender
   *   Signed response
   */
  app.put('/1/:user', function push(req, res) {
    api.request(req, res, function request(user) {

      // Assert the user is within its quota (error 413)
      if (JSON.stringify(user).length >= user.max) {
        return res.sign(413, 'User reached quota');
      }

      // Add request timestamp to message
      req.body.head.time = req.timestamp;

      // Push message onto the box
      user.box.push(req.body);

      return api.respond(req, res, user, 'Message send');
    }, req.body.head.user);
  });

  /**
   * Pulls a message from the box.
   *
   * Authentication:
   *
   *   Signed request
   *   Signed response
   */
  app.get('/1/:user', function pull(req, res) {
    api.request(req, res, function request(user) {
      var message = user.box.shift();

      return api.respond(req, res, user, message);
    });
  });

  // Return instance
  return this;
}

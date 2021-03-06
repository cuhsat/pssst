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
 * Simple Redis wrapper with Heroku support.
 *
 * @param {Object} source
 * @param {Function} callback
 */
module.exports = function Redis(source, callback) {
  var url = require('url');
  var redis = require('redis');

  // Heroku support
  if (process.env.REDIS_URL) {
    var client = redis.createClient(process.env.REDIS_URL);
  } else {
    var client = redis.createClient(source);
  }

  // Client error
  client.on('error', function error(err) {
    console.error(err.stack || err);
  });

  // Client ready
  client.on('ready', function ready(err) {
    return callback(err, {
      /**
       * Gets the value of a key (Redis GET).
       *
       * @param {String} the key
       * @param {Function} callback
       */
      get: function get(key, callback) {
        client.GET(key, function get(err, val) {
          callback(err, JSON.parse(val));
        });
      },

      /**
       * Sets the value of a key (Redis SET).
       *
       * @param {String} the key
       * @param {Object} the value
       * @param {Function} callback
       */
      set: function set(key, val, callback) {
        client.SET(key, JSON.stringify(val, null, 0), function set(err) {
          callback(err);
        });
      }
    });
  });
}

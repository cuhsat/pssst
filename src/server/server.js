#!/usr/bin/env node
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
 * Start script. Available config values:
 *
 *   Pssst
 *
 *   port  = server port
 *   debug = server debug level (0 to 3)
 *
 *   Redis
 *
 *   source = database socket or port
 *   number = database number
 *
 * @return {Number} exit code
 */
try {
  var fs = require('fs');

  if (process.argv.length <= 2) {
    var CONFIG = __dirname + '/config.json';

    // Create default config
    if (!fs.existsSync(CONFIG)) {
      fs.writeFileSync(CONFIG, JSON.stringify({
        "port": 62421,
        "debug": 0,
        "db": {
          "source": 6379,
          "number": 0
        }
      }, null, 2));
    }

    var server = require('./lib/index.js');
    var config = require('./config.json');

    server(config, function ready(err, server) {
      if (err) {
        console.error(err.stack || err);
      } else {

        // Handle error events
        process.on('uncaughtException', function error(err) {
          server.close(function close() {
            console.error(err.stack || err);
            process.exit(1);
          });
        });

        // Handle exit events
        process.on('SIGTERM', function exit() {
          server.close(function close() {
            console.log('Exit');
            process.exit(0);
          });
        });

        console.log('Ready');
      }
    });
  } else {
    switch (process.argv[2].toLowerCase()) {

      // Print license
      case '-l':
      case '--license':
        var info = require('./package.json');
        console.log('Licensed under', info['license']);
        process.exit(0);

      // Print version
      case '-v':
      case '--version':
        var info = require('./package.json');
        console.log('Pssst', info['version']);
        process.exit(0);

      // Print usage
      default:
        console.log([
          'Usage: node server [option]',
          '',
          '  -h --help      Shows usage',
          '  -l --license   Shows license',
          '  -v --version   Shows version',
          '',
          'Report bugs to <christian@uhsat.de>'
        ].join('\n'));
        process.exit(2);
    }
  }
} catch (err) {
  console.error(err.stack || err);
  process.exit(1);
}

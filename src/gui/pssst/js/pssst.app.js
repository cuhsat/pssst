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
 * You should have received a copy of the GNU General Public License
 * along with this program. If not, see <http://www.gnu.org/licenses/>.
 *
 *
 *
 * Pssst app.
 *
 * @param {Object} pssst api
 */
define(['js/pssst.api.js'], function (api) {
  moment.locale(window.navigator.language);

  /**
   * Pssst app class.
   *
   * @param {String} security token
   * @return {Object} app instance
   */
  return function (token) {

    // Current user
    var user = null;

    // Uses the local proxy server
    api = api(token);

    /**
     * Pssst app instance.
     */
    var app = {
      /**
       * Calls the API.
       *
       * @param {String} the method
       * @param {Object} the parameters
       * @param {Function} callback
       */
      call: function call(method, params, callback) {
        api.call(method, params, function call(err, val) {
          if (!err) {
            callback(val);
          } else {

            // Unlock login dialog
            if (method === 'setup') {
              $('#user-create span').removeClass('fa-spin fa-spinner');
              $('#user-create span').addClass('fa-user');
              $('#login-dialog button').prop('disabled', false);
            }

            // Shake login dialog
            if (method === 'login') {
              callback(null);
            }

            // General error handling
            alert(err);
          }
        });
      },

      /**
       * Creates the Pssst instance.
       */
      login: function login() {
        var username = $.trim($('#username').val());
        var password = $.trim($('#password').val());

        // Check if credentials are present
        if (username && password) {
          $('#login-dialog').removeClass('animated shake');

          // Login user
          app.call('login', [username, password], function call(data) {
            if (data) {
              user = data;
              $('#login-dialog').modal('hide');
              $('#login-dialog button').prop('disabled', false);
              $('#user').text('pssst.' + user);
              document.title = 'Pssst | ' + user;
            } else {
              $('#login-dialog').addClass('animated shake');
            }
          });
        }
      },

      /**
       * Clears the Pssst instance and reloads (clears all user data).
       */
      logout: function logout() {
        app.call('logout', null, function () {
          clearInterval(id);
          location.reload();
        });
      },

      /**
       * Shows the proxy version.
       */
      showVersion: function showVersion() {
        app.call('version', null, function call(data) {
          $('.version').text(data);
        });
      },

      /**
       * Creates an new user and logs in.
       */
      createUser: function createUser() {
        var username = $.trim($('#username').val());
        var password = $.trim($('#password').val());

        // Check if credentials are present
        if (username && password) {

          // Lock login dialog while processing
          $('#login-dialog button').prop('disabled', true);
          $('#user-create span').removeClass('fa-user');
          $('#user-create span').addClass('fa-spin fa-spinner');

          app.call('setup', [username, password], function call() {
            app.login();
          });
        }
      },

      /**
       * Deletes an user and logs out.
       */
      deleteUser: function deleteUser() {
        app.call('delete', null, function call() {
          app.logout();
        });
      },

      /**
       * Pulls all new messages from the box.
       */
      pullMessages: function pullMessages() {
        app.call('pull', function call(messages) {
          messages.forEach(function(data) {
            $('#box').append(Mustache.render(
              '<article class="panel panel-default">'
            + '  <div class="panel-body">'
            + '    {{#text}}'
            + '      {{.}}<br>'
            + '    {{/text}}'
            + '    <small class="text-muted">'
            + '      <span class="fa fa-clock-o"></span> {{user}}, {{time}}'
            + '    </small>'
            + '  </div>'
            + '</article>'
            , {
              text: data[2].split('\n'),
              user: data[0],
              time: moment.unix(data[1]).format('L LTS') // Use local time
            }));

            // Bind event to reply message
            $('#box article:last-child').click(function() {
              $('#receiver').val(data[0]);
              $('#write-dialog').modal('show');
            });

            // Scroll to the last message
            $('html,body').animate({scrollTop: $(document).height()}, 'slow');
          });
        });
      },

      /**
       * Pushes a new message into the box.
       */
      pushMessage: function pushMessage() {
        var receiver = $.trim($('#receiver').val());
        var message = $.trim($('#message').val());

        if (receiver && message) {
          app.call('push', [[receiver], message], function call(data) {
            $('#receiver').val('');
            $('#message').val('');
          });
        }
      }
    };


    // Show the current version
    app.showVersion();

    // Set message pull interval
    var id = setInterval(function task() {
      if (user) app.pullMessages();
    }, 2000);

    // Add the security token to all anchor links
    $('body').on('click', 'a', function(event) {
      if ($(this).attr('href') === '') {
        $(this).attr('href', '#' + token);
      }
    });

    // Setup dialogs to be static
    $('.modal').modal({
      backdrop: 'static',
      keyboard: false,
      show: false
    })

    // Always focus first input field
    $('.modal').on('shown.bs.modal', function() {
      $(this).find('[autofocus]:first').focus();
    })

    // Always click the primary button if return is pressed
    $('.modal').on('keypress', function(e) {
      if (e.which === 13) {
        var button = $(this).find('.btn-primary:first');

        // Ignore the return key for message text
        if (button.attr('id') !== 'push-message') {
          button.click();
        }
      }
    });

    // Bind events to all buttons
    $('#user-login').click(app.login);
    $('#user-logout').click(app.logout);
    $('#user-create').click(app.createUser);
    $('#user-delete').click(app.deleteUser);
    $('#push-message').click(app.pushMessage);

    // Show login dialog at first
    $('#login-dialog').modal('show');

    // Return instance
    return this;
  };
});

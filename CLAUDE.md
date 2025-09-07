Latest Errors:

❯ python app.py
 * Serving Flask app 'app'
 * Debug mode: on
WARNING: This is a development server. Do not use it in a production deployment. Use a production WSGI server instead.
 * Running on all addresses (0.0.0.0)
 * Running on http://127.0.0.1:5005
 * Running on http://192.168.1.126:5005
Press CTRL+C to quit
 * Restarting with stat
 * Debugger is active!
 * Debugger PIN: 137-196-519
/home/parteek/Documents/personalWebApp/app.py:19: DeprecationWarning: The default date adapter is deprecated as of Python 3.12; see the sqlite3 documentation for suggested replacement recipes
  cursor.execute('''
/home/parteek/Documents/personalWebApp/app.py:65: DeprecationWarning: The default date adapter is deprecated as of Python 3.12; see the sqlite3 documentation for suggested replacement recipes
  cursor.execute('''
/home/parteek/Documents/personalWebApp/app.py:106: DeprecationWarning: The default date adapter is deprecated as of Python 3.12; see the sqlite3 documentation for suggested replacement recipes
  cursor.execute('''
192.168.1.126 - - [06/Sep/2025 18:28:18] "GET / HTTP/1.1" 200 -
/home/parteek/Documents/personalWebApp/app.py:536: DeprecationWarning: The default date adapter is deprecated as of Python 3.12; see the sqlite3 documentation for suggested replacement recipes
  cursor.execute('''
/home/parteek/Documents/personalWebApp/app.py:559: DeprecationWarning: The default date adapter is deprecated as of Python 3.12; see the sqlite3 documentation for suggested replacement recipes
  cursor.execute('''
192.168.1.126 - - [06/Sep/2025 18:28:18] "GET /api/analytics HTTP/1.1" 200 -
/home/parteek/Documents/personalWebApp/app.py:284: DeprecationWarning: The default date adapter is deprecated as of Python 3.12; see the sqlite3 documentation for suggested replacement recipes
  cursor.execute('''
/home/parteek/Documents/personalWebApp/app.py:291: DeprecationWarning: The default date adapter is deprecated as of Python 3.12; see the sqlite3 documentation for suggested replacement recipes
  cursor.execute('''
/home/parteek/Documents/personalWebApp/app.py:298: DeprecationWarning: The default date adapter is deprecated as of Python 3.12; see the sqlite3 documentation for suggested replacement recipes
  cursor.execute('''
/home/parteek/Documents/personalWebApp/app.py:305: DeprecationWarning: The default date adapter is deprecated as of Python 3.12; see the sqlite3 documentation for suggested replacement recipes
  cursor.execute('''
/home/parteek/Documents/personalWebApp/app.py:327: DeprecationWarning: The default date adapter is deprecated as of Python 3.12; see the sqlite3 documentation for suggested replacement recipes
  cursor.execute('''
/home/parteek/Documents/personalWebApp/app.py:338: DeprecationWarning: The default date adapter is deprecated as of Python 3.12; see the sqlite3 documentation for suggested replacement recipes
  cursor.execute('''
192.168.1.126 - - [06/Sep/2025 18:28:20] "GET /analytics HTTP/1.1" 500 -
Traceback (most recent call last):
  File "/home/parteek/Documents/personalWebApp/virtualEnv/lib/python3.13/site-packages/flask/app.py", line 1536, in __call__
    return self.wsgi_app(environ, start_response)
           ~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/parteek/Documents/personalWebApp/virtualEnv/lib/python3.13/site-packages/flask/app.py", line 1514, in wsgi_app
    response = self.handle_exception(e)
  File "/home/parteek/Documents/personalWebApp/virtualEnv/lib/python3.13/site-packages/flask/app.py", line 1511, in wsgi_app
    response = self.full_dispatch_request()
  File "/home/parteek/Documents/personalWebApp/virtualEnv/lib/python3.13/site-packages/flask/app.py", line 919, in full_dispatch_request
    rv = self.handle_user_exception(e)
  File "/home/parteek/Documents/personalWebApp/virtualEnv/lib/python3.13/site-packages/flask/app.py", line 917, in full_dispatch_request
    rv = self.dispatch_request()
  File "/home/parteek/Documents/personalWebApp/virtualEnv/lib/python3.13/site-packages/flask/app.py", line 902, in dispatch_request
    return self.ensure_sync(self.view_functions[rule.endpoint])(**view_args)  # type: ignore[no-any-return]
           ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^
  File "/home/parteek/Documents/personalWebApp/app.py", line 351, in analytics
    return render_template('analytics.html',
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/parteek/Documents/personalWebApp/virtualEnv/lib/python3.13/site-packages/flask/templating.py", line 149, in render_template
    template = app.jinja_env.get_or_select_template(template_name_or_list)
  File "/home/parteek/Documents/personalWebApp/virtualEnv/lib/python3.13/site-packages/jinja2/environment.py", line 1087, in get_or_select_template
    return self.get_template(template_name_or_list, parent, globals)
           ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/parteek/Documents/personalWebApp/virtualEnv/lib/python3.13/site-packages/jinja2/environment.py", line 1016, in get_template
    return self._load_template(name, globals)
           ~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^
  File "/home/parteek/Documents/personalWebApp/virtualEnv/lib/python3.13/site-packages/jinja2/environment.py", line 975, in _load_template
    template = self.loader.load(self, name, self.make_globals(globals))
  File "/home/parteek/Documents/personalWebApp/virtualEnv/lib/python3.13/site-packages/jinja2/loaders.py", line 138, in load
    code = environment.compile(source, name, filename)
  File "/home/parteek/Documents/personalWebApp/virtualEnv/lib/python3.13/site-packages/jinja2/environment.py", line 771, in compile
    self.handle_exception(source=source_hint)
    ~~~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^
  File "/home/parteek/Documents/personalWebApp/virtualEnv/lib/python3.13/site-packages/jinja2/environment.py", line 942, in handle_exception
    raise rewrite_traceback_stack(source=source)
  File "/home/parteek/Documents/personalWebApp/templates/analytics.html", line 172, in template
    const weeklyData = {{ weekly_trends | tojsonfilter | safe }};
    ^^^^^^^^^^^^^^^^^^^^^^^^^
jinja2.exceptions.TemplateAssertionError: No filter named 'tojsonfilter'.
192.168.1.126 - - [06/Sep/2025 18:28:20] "GET /analytics?__debugger__=yes&cmd=resource&f=style.css HTTP/1.1" 304 -
192.168.1.126 - - [06/Sep/2025 18:28:20] "GET /analytics?__debugger__=yes&cmd=resource&f=debugger.js HTTP/1.1" 304 -
192.168.1.126 - - [06/Sep/2025 18:28:22] "GET /portfolio HTTP/1.1" 500 -
Traceback (most recent call last):
  File "/home/parteek/Documents/personalWebApp/virtualEnv/lib/python3.13/site-packages/flask/app.py", line 1536, in __call__
    return self.wsgi_app(environ, start_response)
           ~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/parteek/Documents/personalWebApp/virtualEnv/lib/python3.13/site-packages/flask/app.py", line 1514, in wsgi_app
    response = self.handle_exception(e)
  File "/home/parteek/Documents/personalWebApp/virtualEnv/lib/python3.13/site-packages/flask/app.py", line 1511, in wsgi_app
    response = self.full_dispatch_request()
  File "/home/parteek/Documents/personalWebApp/virtualEnv/lib/python3.13/site-packages/flask/app.py", line 919, in full_dispatch_request
    rv = self.handle_user_exception(e)
  File "/home/parteek/Documents/personalWebApp/virtualEnv/lib/python3.13/site-packages/flask/app.py", line 917, in full_dispatch_request
    rv = self.dispatch_request()
  File "/home/parteek/Documents/personalWebApp/virtualEnv/lib/python3.13/site-packages/flask/app.py", line 902, in dispatch_request
    return self.ensure_sync(self.view_functions[rule.endpoint])(**view_args)  # type: ignore[no-any-return]
           ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^
  File "/home/parteek/Documents/personalWebApp/app.py", line 451, in portfolio
    return render_template('portfolio.html',
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/parteek/Documents/personalWebApp/virtualEnv/lib/python3.13/site-packages/flask/templating.py", line 150, in render_template
    return _render(app, template, context)
  File "/home/parteek/Documents/personalWebApp/virtualEnv/lib/python3.13/site-packages/flask/templating.py", line 131, in _render
    rv = template.render(context)
  File "/home/parteek/Documents/personalWebApp/virtualEnv/lib/python3.13/site-packages/jinja2/environment.py", line 1295, in render
    self.environment.handle_exception()
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~^^
  File "/home/parteek/Documents/personalWebApp/virtualEnv/lib/python3.13/site-packages/jinja2/environment.py", line 942, in handle_exception
    raise rewrite_traceback_stack(source=source)
  File "/home/parteek/Documents/personalWebApp/templates/portfolio.html", line 1, in top-level template code
    {% extends "base.html" %}
  File "/home/parteek/Documents/personalWebApp/templates/base.html", line 78, in top-level template code
    {% block scripts %}{% endblock %}
    ^^^^^^^^^^^^^^^^^^^^^
  File "/home/parteek/Documents/personalWebApp/templates/portfolio.html", line 251, in block 'scripts'
    const performanceData = {{ performance_history | tojsonfilter | safe }};
    ^^^^^^^^^^^^^^^^^^^^^^^^^
jinja2.exceptions.TemplateRuntimeError: No filter named 'tojsonfilter' found.
192.168.1.126 - - [06/Sep/2025 18:28:22] "GET /portfolio?__debugger__=yes&cmd=resource&f=style.css HTTP/1.1" 304 -
192.168.1.126 - - [06/Sep/2025 18:28:22] "GET /portfolio?__debugger__=yes&cmd=resource&f=debugger.js HTTP/1.1" 304 -
/home/parteek/Documents/personalWebApp/app.py:141: DeprecationWarning: The default date adapter is deprecated as of Python 3.12; see the sqlite3 documentation for suggested replacement recipes
  cursor.execute('SELECT * FROM personal_log WHERE date = ?', (today,))
192.168.1.126 - - [06/Sep/2025 18:28:24] "GET /personal HTTP/1.1" 200 -
/home/parteek/Documents/personalWebApp/app.py:194: DeprecationWarning: The default date adapter is deprecated as of Python 3.12; see the sqlite3 documentation for suggested replacement recipes
  cursor.execute('''
/home/parteek/Documents/personalWebApp/app.py:208: DeprecationWarning: The default date adapter is deprecated as of Python 3.12; see the sqlite3 documentation for suggested replacement recipes
  cursor.execute('''
192.168.1.126 - - [06/Sep/2025 18:28:25] "GET /spending HTTP/1.1" 200 -

Latest issues
❯ python app.py
 * Serving Flask app 'app'
 * Debug mode: on
WARNING: This is a development server. Do not use it in a production deployment. Use a production WSGI server instead.
 * Running on all addresses (0.0.0.0)
 * Running on http://127.0.0.1:5005
 * Running on http://192.168.1.126:5005
Press CTRL+C to quit
 * Restarting with stat
 * Debugger is active!
 * Debugger PIN: 777-599-872
/home/parteek/Documents/personalWebApp/app.py:300: DeprecationWarning: The default date adapter is deprecated as of Python 3.12; see the sqlite3 documentation for suggested replacement recipes
  cursor.execute('''
/home/parteek/Documents/personalWebApp/app.py:307: DeprecationWarning: The default date adapter is deprecated as of Python 3.12; see the sqlite3 documentation for suggested replacement recipes
  cursor.execute('''
/home/parteek/Documents/personalWebApp/app.py:314: DeprecationWarning: The default date adapter is deprecated as of Python 3.12; see the sqlite3 documentation for suggested replacement recipes
  cursor.execute('''
/home/parteek/Documents/personalWebApp/app.py:321: DeprecationWarning: The default date adapter is deprecated as of Python 3.12; see the sqlite3 documentation for suggested replacement recipes
  cursor.execute('''
/home/parteek/Documents/personalWebApp/app.py:343: DeprecationWarning: The default date adapter is deprecated as of Python 3.12; see the sqlite3 documentation for suggested replacement recipes
  cursor.execute('''
/home/parteek/Documents/personalWebApp/app.py:354: DeprecationWarning: The default date adapter is deprecated as of Python 3.12; see the sqlite3 documentation for suggested replacement recipes
  cursor.execute('''
192.168.1.126 - - [06/Sep/2025 20:16:59] "GET /analytics HTTP/1.1" 500 -
Traceback (most recent call last):
  File "/home/parteek/Documents/personalWebApp/virtualEnv/lib/python3.13/site-packages/flask/app.py", line 1536, in __call__
    return self.wsgi_app(environ, start_response)
           ~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/parteek/Documents/personalWebApp/virtualEnv/lib/python3.13/site-packages/flask/app.py", line 1514, in wsgi_app
    response = self.handle_exception(e)
  File "/home/parteek/Documents/personalWebApp/virtualEnv/lib/python3.13/site-packages/flask/app.py", line 1511, in wsgi_app
    response = self.full_dispatch_request()
  File "/home/parteek/Documents/personalWebApp/virtualEnv/lib/python3.13/site-packages/flask/app.py", line 919, in full_dispatch_request
    rv = self.handle_user_exception(e)
  File "/home/parteek/Documents/personalWebApp/virtualEnv/lib/python3.13/site-packages/flask/app.py", line 917, in full_dispatch_request
    rv = self.dispatch_request()
  File "/home/parteek/Documents/personalWebApp/virtualEnv/lib/python3.13/site-packages/flask/app.py", line 902, in dispatch_request
    return self.ensure_sync(self.view_functions[rule.endpoint])(**view_args)  # type: ignore[no-any-return]
           ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^
  File "/home/parteek/Documents/personalWebApp/app.py", line 367, in analytics
    return render_template('analytics.html',
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/parteek/Documents/personalWebApp/virtualEnv/lib/python3.13/site-packages/flask/templating.py", line 150, in render_template
    return _render(app, template, context)
  File "/home/parteek/Documents/personalWebApp/virtualEnv/lib/python3.13/site-packages/flask/templating.py", line 131, in _render
    rv = template.render(context)
  File "/home/parteek/Documents/personalWebApp/virtualEnv/lib/python3.13/site-packages/jinja2/environment.py", line 1295, in render
    self.environment.handle_exception()
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~^^
  File "/home/parteek/Documents/personalWebApp/virtualEnv/lib/python3.13/site-packages/jinja2/environment.py", line 942, in handle_exception
    raise rewrite_traceback_stack(source=source)
  File "/home/parteek/Documents/personalWebApp/templates/analytics.html", line 1, in top-level template code
    {% extends "base.html" %}
  File "/home/parteek/Documents/personalWebApp/templates/base.html", line 78, in top-level template code
    {% block scripts %}{% endblock %}
    ^^^^^^^^^^^^^^^^^^^^^
  File "/home/parteek/Documents/personalWebApp/templates/analytics.html", line 172, in block 'scripts'
    const weeklyData = {{ weekly_trends | tojsonfilter | safe }};
    ^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/parteek/Documents/personalWebApp/app.py", line 13, in to_json_filter
    return json.dumps(value)
           ~~~~~~~~~~^^^^^^^
  File "/usr/lib/python3.13/json/__init__.py", line 231, in dumps
    return _default_encoder.encode(obj)
           ~~~~~~~~~~~~~~~~~~~~~~~^^^^^
  File "/usr/lib/python3.13/json/encoder.py", line 200, in encode
    chunks = self.iterencode(o, _one_shot=True)
  File "/usr/lib/python3.13/json/encoder.py", line 261, in iterencode
    return _iterencode(o, 0)
  File "/usr/lib/python3.13/json/encoder.py", line 180, in default
    raise TypeError(f'Object of type {o.__class__.__name__} '
    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
TypeError: Object of type Row is not JSON serializable
192.168.1.126 - - [06/Sep/2025 20:16:59] "GET /analytics?__debugger__=yes&cmd=resource&f=debugger.js HTTP/1.1" 304 -
192.168.1.126 - - [06/Sep/2025 20:16:59] "GET /analytics?__debugger__=yes&cmd=resource&f=style.css HTTP/1.1" 304 -
192.168.1.126 - - [06/Sep/2025 20:17:01] "GET /analytics HTTP/1.1" 500 -
Traceback (most recent call last):
  File "/home/parteek/Documents/personalWebApp/virtualEnv/lib/python3.13/site-packages/flask/app.py", line 1536, in __call__
    return self.wsgi_app(environ, start_response)
           ~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/parteek/Documents/personalWebApp/virtualEnv/lib/python3.13/site-packages/flask/app.py", line 1514, in wsgi_app
    response = self.handle_exception(e)
  File "/home/parteek/Documents/personalWebApp/virtualEnv/lib/python3.13/site-packages/flask/app.py", line 1511, in wsgi_app
    response = self.full_dispatch_request()
  File "/home/parteek/Documents/personalWebApp/virtualEnv/lib/python3.13/site-packages/flask/app.py", line 919, in full_dispatch_request
    rv = self.handle_user_exception(e)
  File "/home/parteek/Documents/personalWebApp/virtualEnv/lib/python3.13/site-packages/flask/app.py", line 917, in full_dispatch_request
    rv = self.dispatch_request()
  File "/home/parteek/Documents/personalWebApp/virtualEnv/lib/python3.13/site-packages/flask/app.py", line 902, in dispatch_request
    return self.ensure_sync(self.view_functions[rule.endpoint])(**view_args)  # type: ignore[no-any-return]
           ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^
  File "/home/parteek/Documents/personalWebApp/app.py", line 367, in analytics
    return render_template('analytics.html',
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/parteek/Documents/personalWebApp/virtualEnv/lib/python3.13/site-packages/flask/templating.py", line 150, in render_template
    return _render(app, template, context)
  File "/home/parteek/Documents/personalWebApp/virtualEnv/lib/python3.13/site-packages/flask/templating.py", line 131, in _render
    rv = template.render(context)
  File "/home/parteek/Documents/personalWebApp/virtualEnv/lib/python3.13/site-packages/jinja2/environment.py", line 1295, in render
    self.environment.handle_exception()
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~^^
  File "/home/parteek/Documents/personalWebApp/virtualEnv/lib/python3.13/site-packages/jinja2/environment.py", line 942, in handle_exception
    raise rewrite_traceback_stack(source=source)
  File "/home/parteek/Documents/personalWebApp/templates/analytics.html", line 1, in top-level template code
    {% extends "base.html" %}
  File "/home/parteek/Documents/personalWebApp/templates/base.html", line 78, in top-level template code
    {% block scripts %}{% endblock %}
    ^^^^^^^^^^^^^^^^^^^^^
  File "/home/parteek/Documents/personalWebApp/templates/analytics.html", line 172, in block 'scripts'
    const weeklyData = {{ weekly_trends | tojsonfilter | safe }};
    ^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/parteek/Documents/personalWebApp/app.py", line 13, in to_json_filter
    return json.dumps(value)
           ~~~~~~~~~~^^^^^^^
  File "/usr/lib/python3.13/json/__init__.py", line 231, in dumps
    return _default_encoder.encode(obj)
           ~~~~~~~~~~~~~~~~~~~~~~~^^^^^
  File "/usr/lib/python3.13/json/encoder.py", line 200, in encode
    chunks = self.iterencode(o, _one_shot=True)
  File "/usr/lib/python3.13/json/encoder.py", line 261, in iterencode
    return _iterencode(o, 0)
  File "/usr/lib/python3.13/json/encoder.py", line 180, in default
    raise TypeError(f'Object of type {o.__class__.__name__} '
    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
TypeError: Object of type Row is not JSON serializable
192.168.1.126 - - [06/Sep/2025 20:17:01] "GET /analytics?__debugger__=yes&cmd=resource&f=style.css HTTP/1.1" 304 -
192.168.1.126 - - [06/Sep/2025 20:17:01] "GET /analytics?__debugger__=yes&cmd=resource&f=debugger.js HTTP/1.1" 304 -


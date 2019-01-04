import os
import re
import cgi
import json
from urllib.parse import parse_qs, urljoin

from http.client import responses as http_responses
from wsgiref.headers import Headers
from jinja2 import Environment, FileSystemLoader


class App:
    def __init__(self, templates=None):
        self.router = Router()
        if templates is None:
            templates = [os.path.join(os.path.abspath('.'), 'templates')]
        self.jinja2_environment = Environment(loader=FileSystemLoader(templates))

    def route(self, path=None, method='GET', callback=None):
        def decorator(callback_func):
            self.router.add(method, path, callback_func)
            return callback_func
        return decorator(callback) if callback else decorator

    def __call__(self, env, start_response):
        method = env['REQUEST_METHOD'].upper()
        path = env['PATH_INFO'] or '/'
        callback,  kwargs = self.router.match(method, path)

        response = callback(Request(env), **kwargs)
        print('==================================')
        print('==================================')
        print('status content:', response.status)
        print('status length:', len(response.status))
        print('headers_list content:', response.header_list)
        print('==================================')
        print('==================================')
        start_response(response.status, response.header_list)
        if isinstance(response, TemplateResponse):
            return [response.render_body(self.jinja2_environment)]
        return [response.body]


def http404(env, start_response):
    start_response('404 Not Found', [('Content-type', 'text/plain; charset=utf-8')])
    return [b'404 Not Found']


def http405(env, start_response):
    start_response('405 Method Not Allowed', [('Content-type', 'text/plain; charset=utf-8')])
    return [b'405 Method Not Allowed']


class Router:
    def __init__(self):
        self.routes = []

    def add(self, method, path, callback):
        self.routes.append({
            'method': method,
            'path': path,
            'path_compiled': re.compile(path),
            'callback': callback
        })

    def match(self, method, path):
        error_callback = http404
        for r in self.routes:
            matched = r['path_compiled'].match(path)
            if not matched:
                continue

            error_callback = http405
            url_vars = matched.groupdict()
            if method == r['method']:
                return r['callback'], url_vars
        return error_callback, {}


class Request:
    def __init__(self, environ):
        self.environ = environ
        self._body = None

    @property
    def path(self):
        return self.environ['PATH_INFO'] or '/'

    @property
    def method(self):
        return self.environ['REQUEST_METHOD'].upper()

    @property
    def body(self):
        if self._body is None:
            content_length = int(self.environ.get('CONTENT_LENGTH', 0))
            self.environ['wsgi.input'].read(content_length)
        return self._body

    @property
    def forms(self):
        form = cgi.FieldStrorage(
            fp=self.environ['wsgi.input'],
            envrion=self.envrion,
            keep_blank_values=True,
        )
        params = {k: form[k].value for k in form}
        return params

    @property
    def query(self):
        return parse_qs(self.environ['QUERY_STRING'])

    @property
    def text(self):
        return self.body.decode(self.charset)

    @property
    def json(self):
        return json.loads(self.body)


class Response:
    default_status = '200'
    default_charset = 'utf-8'
    default_content_type = 'text/html; charset=UTF-8'

    def __init__(self, body='', status=None, headers=None, charset=None):
        self._body = body
        self.status = status or self.default_status
        self.headers = Headers()
        self.charset = charset or self.default_charset

        if headers:
            for name, value in headers.items():
                self.headers.add_header(name, value)

    @property
    def status_code(self):
        return "%d %s" % (self.status, http_responses[self.status])

    @property
    def header_list(self):
        if 'Content-Type' not in self.headers:
            self.headers.add_header('Content-Type', self.default_content_type)
            return self.headers.items()

    @property
    def body(self):
        if isinstance(self._body, str):
            return [self._body.encode(self.charset)]
        return [self._body]


class JSONResponse(Response):
    default_content_type = 'text/json; charset=UTF-8'

    def __init__(self, dic, status=200, headers=None, charset=None, **dump_args):
        self.dic = dic
        self.json_dump_args = dump_args
        super.__init__(body='', status=status, headers=headers, charset=charset)

    @property
    def body(self):
        return [json.dumps(self.dic, **self.json_dump_args).encode(self.charset)]


class TemplateResponse(Response):
    default_content_type = 'text/html; charset=UTF-8'

    def __init__ (self, filename, status='200 OK', headers=None, charset='utf-8', **tpl_args):
        self.filename = filename
        self.tpl_args = tpl_args
        super().__init__(body='', status=status, hearders=headers, charset=charset)

    def render_body(self, jinja2_environment):
        template = jinja2_environment.get_template(self.filename)
        return template.render(**self.tpl_args).encode(self.charset)

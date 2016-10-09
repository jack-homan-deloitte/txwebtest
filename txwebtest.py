from cStringIO import StringIO
from twisted.internet import defer
from twisted.python.urlpath import URLPath
from twisted.web.server import Site, NOT_DONE_YET
from twisted.web.test.test_web import DummyRequest
from twisted.web.http_headers import Headers
from urlparse import parse_qs


class TestClient(object):
    def __init__(self, resource):
        self.site = Site(resource)

    def get(self, path_with_params, status=None):
        return self.request(path_with_params, method='GET', status=status)

    def post(self, path_with_params, content=None, content_type=None, status=None):
        return self.request(path_with_params, method='POST', content=content,
                content_type=content_type, status=status)

    def delete(self, path_with_params, status=None):
        return self.request(path_with_params, method='DELETE', status=status)

    def patch(self, path_with_params, content=None, content_type=None, status=None):
        return self.request(path_with_params, method='PATCH', content=content,
                content_type=content_type, status=None)

    def put(self, path_with_params, content=None, content_type=None, status=None):
        return self.request(path_with_params, method='PUT', content=content,
                content_type=content_type, status=status)

    def head(self, path_with_params, status=None):
        return self.request(path_with_params, method='HEAD', status=status)

    def options(self, path_with_params, status=None):
        return self.request(path_with_params, method='OPTIONS', status=status)

    @defer.inlineCallbacks
    def request(self, req_or_path_with_params, status=None, **request_kwargs):
        if isinstance(req_or_path_with_params, TestRequest):
            req = req_or_path_with_params
        else:
            path, params = self.parse_url(req_or_path_with_params)
            req = TestRequest(path, params=params, **request_kwargs)

        resp = yield self._handle_request(req)
        if status is not None:
            assert resp.status_code == status, resp.status_code
        defer.returnValue(resp)

    def _handle_request(self, request):
        ''' Resolves a test request. '''
        finished = request.notifyFinish()

        def extract_response(none):
            return TestResponse(request.responseCode or 200, request.responseHeaders,
                    ''.join(request.written))

        def _render(resource):
            result = resource.render(request)
            if isinstance(result, str):
                request.write(result)
                request.finish()
                return finished
            elif result is NOT_DONE_YET:
                return finished
            else:
                raise ValueError("Unexpected return value: %r" % (result,))

        resource_handler = self.site.getResourceFor(request)
        d = _render(resource_handler)
        d.addCallback(extract_response)
        return d

    def parse_url(self, path_with_params):
        parts = path_with_params.split('?')
        if len(parts) == 2:
            path, param_str = parts
            params = parse_qs(param_str)
        else:
            path, = parts
            params = {}
        return path, params


class TestRequest(DummyRequest):
    ''' DummyRequest just isn't good enough for klein. '''

    def __init__(self, path, method, content_type=None, params=None, content=None, headers=None):
        super(TestRequest, self).__init__(path.split('/'))
        self._finishedDeferreds = []
        self.requestHeaders = Headers(headers or {})

        for k, v in (headers or {}).items():
            self.responseHeaders.addRawHeader(k.lower(), v)
        self.method = method
        self.path = path
        self.code = None
        self.received_headers = {}
        self.uri = path
        self.redirect_url = None
        self.postpath = path.split('/')
        if not self.postpath[0]:
            self.postpath.pop(0)
        self.args = params or {}
        # To simulate a real request with query string params (the encoding is usually resulting in string literals)
        for k, v in self.args.items():
            # expecting "v" to always be of type "list"
            self.args[k] = [str(item) for item in v]
        self.content = StringIO(content or '')
        if content:
            self.content_type = content_type or 'application/x-www-form-urlencoded'
            if self.content_type == 'application/x-www-form-urlencoded':
                if isinstance(content, dict):
                    self.args.update(content)
                else:
                    self.args.update(parse_qs(content))
        else:
            self.content_type = None

    @property
    def sentLength(self):
        return sum(len(thing) for thing in self.written)

    def getClientIP(self):
        return "127.0.0.1"

    def getRequestHostname(self, *args, **kwargs):
        return 'localhost'

    def isSecure(self):
        return False

    def URLPath(self):
        return URLPath(path=self.path)  # FIXME: self.args


class TestResponse(object):
    def __init__(self, status_code, headers, body):
        self.status_code = status_code
        self.headers = headers
        self.body = body

    def get_header(self, header):
        values = self.headers.getRawHeaders(header.lower())
        if values:
            return values[0]
        return None

    @property
    def text(self):
        return self.body


try:
    # Klein uses zope to restrict what types it accepts, for some reason.
    from klein.interfaces import IKleinRequest
    from klein.app import KleinRequest
    from twisted.python.components import registerAdapter
    registerAdapter(KleinRequest, TestRequest, IKleinRequest)
except ImportError:
    pass

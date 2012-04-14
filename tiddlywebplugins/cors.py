"""
CORS handling for TiddlyWeb.
"""

from tiddlyweb.web.wsgi import EncodeUTF8

DEFAULT_EXPOSED_HEADERS = ['ETag']
DEFAULT_CORS_CACHE_AGE = '600'  # 10 minutes

class PreFlightCheck(object):
    """
    Handle incoming pre-flight OPTIONS requests.

    This middleware is only enabled if config['cors.enable_non_simple']
    is True. The default is False.

    When an OPTIONS request is made, the response will 404 if the route
    is not available. The methods header will only respond with those
    methods which are actually valid for the requested resource. Both of
    these things are done by called select() on the selector app.
    """
    def __init__(self, application):
        self.application = application

    def __call__(self, environ, start_response):

        if ('HTTP_ORIGIN' in environ
                and environ['REQUEST_METHOD'] == 'OPTIONS'):

            selector = environ['tiddlyweb.config']['selector']

            app, _, methods, _ = selector.select(
                    environ['PATH_INFO'], environ['REQUEST_METHOD'])

            if methods:  # There are methods on this route
                config = environ.get('tiddlyweb.config', {})

                allowed_origin = environ['HTTP_ORIGIN']
                exposed_headers = ', '.join(DEFAULT_EXPOSED_HEADERS)
                extra_headers = environ.get(
                        'HTTP_ACCESS_CONTROL_REQUEST_HEADERS', None) 
                if extra_headers:
                    exposed_headers = exposed_headers + ', %s' % extra_headers

                headers = [('Access-Control-Allow-Origin', allowed_origin),
                        ('Access-Control-Allow-Headers', exposed_headers)]

                if config.get('cors.allow_creds', False):
                    headers.append(('Access-Control-Allow-Credentials', 'true'))

                headers.append(('Access-Control-Max-Age',
                    DEFAULT_CORS_CACHE_AGE))

                headers.append(('Access-Control-Allow-Methods',
                    ', '.join(sorted(methods))))

                start_response('200 OK', headers)
                return []
            else:
                return app(environ, start_response)
        else:
            return self.application(environ, start_response)

class CORSResponse(object):
    """
    Send correct headers in response to a (non-preflight) request
    that provided a CORS 'Origin' header.

    By default if Origin was in the header, then

        Access-Control-Allow-Origin: *
        Access-Control-Expose-Headers: ETag

    are sent in the response.

    For the time being these responses are sent on any request
    method with any status code.

    Config settings allow more granular control:

    If 'cors.match_origin' is True, then the value of the Origin
    header will be the value of the Access-Control-Allow-Origin header.

    If 'cors.allow_creds' is True, then the
    Access-Control-Allow-Credentials header will be sent with a value
    of 'true', otherwise it will not be sent.

    If 'cors.exposed_headers' is set, its should be a list of strings
    representing header names which are appended to the default
    Access-Control-Expose-Headers: ETag
    """

    def __init__(self, application):
        self.application = application

    def __call__(self, environ, start_response):

        def replacement_start_response(status, headers, exc_info=None):

            config = environ.get('tiddlyweb.config', {})

            allowed_origin = '*'
            if config.get('cors.match_origin', False):
                allowed_origin = environ['HTTP_ORIGIN']

            exposed_headers = ', '.join(DEFAULT_EXPOSED_HEADERS
                    + config.get('cors.exposed_headers', []))

            headers.extend([('Access-Control-Allow-Origin', allowed_origin),
                    ('Access-Control-Expose-Headers', exposed_headers)])

            if config.get('cors.allow_creds', False):
                headers.append(('Access-Control-Allow-Credentials', 'true'))

            return start_response(status, headers, exc_info)

        if 'HTTP_ORIGIN' in environ and environ['REQUEST_METHOD'] != 'OPTIONS':
            return self.application(environ, replacement_start_response)
        else:
            return self.application(environ, start_response)


def init(config):
    if 'selector' in config:
        if config.get('cors.enable_non_simple', False):
            if PreFlightCheck not in config['server_request_filters']:
                config['server_request_filters'].append(PreFlightCheck)
        if CORSResponse not in config['server_response_filters']:
            config['server_response_filters'].insert(
                    config['server_response_filters']
                    .index(EncodeUTF8) + 1, CORSResponse)


import requests
from six.moves.urllib import parse

DEFAULT_PORT = 49153

class Transport(object):

    def __init__(self, host=None, port=None, root=None, fixed_root=False, default_timeout=10):
        if root and host:
            raise ValueError('cannot specify root as well as host')
        if root and '://' not in root:
            err = 'root must include protocol - e.g. "http://host:port/", not "%r"'
            raise ValueError(err % (root,))
        if port and not host:
            raise ValueError('cannot specify port without specifying host')
        if root:
            self.root = root
        elif host:
            self.root = 'http://%s:%s/' % (host, port or DEFAULT_PORT)
        elif fixed_root:
            raise ValueError('cannot fix root without any host / root values')
        else:
            self.root = None

        self.fixed_root = fixed_root

        self.session = requests.Session()

        # Needed otherwise requests will not be authenticated correctly.
        self.session.headers['User-Agent'] = 'SKY_skyplus'
        self.default_timeout = default_timeout

    def _url(self, resource):

        # Resources cannot be at a higher path than the route, so relative
        # resources will have their leading slashes removed.
        if resource.startswith('/'):
            resource = resource[1:]

        # Relative path.
        if '://' not in resource:
            if not self.root:
                raise ValueError('cannot resolve relative path without a root')
            return parse.urljoin(self.root, resource)

        # Absolute path.
        if not self.fixed_root:
            return resource

        # Parse the URL and reattach the root.
        parsed_url = parse.urlparse(resource)
        return parse.urljoin(self.root, resource)

    def get_resource(self, location, timeout=None, raw_resp=False):
        url = self._url(location)

        req = requests.Request('GET', url)
        req = self.session.prepare_request(req)
        resp = self.send_request(req, timeout=timeout)
        if not raw_resp:
            resp.raise_for_status()
        return resp

    def send_request(self, req, timeout=10):
        return self.session.send(req, timeout=timeout)

    def soap_request(self, location, schema, method, soapbody,
        timeout=None, raw_resp=False):
        url = self._url(location)

        # Quotes around the soap-action header is important - you will
        # get a 500 error otherwise. Same with the Content-Type - if
        # this is missing, a 500 response is returned.
        headers = {
            'SOAPACTION': '"{0}#{1}"'.format(schema, method),
            'Content-Type': 'text/xml; charset="utf-8"',
        }

        # XXX: Might need some encoding checks here.
        req = requests.Request('POST', url, headers=headers,
            data=soapbody)
        req = self.session.prepare_request(req)
        resp = self.send_request(req, timeout=timeout or self.default_timeout)
        if not raw_resp:
            resp.raise_for_status()
        return resp

    def __str__(self):
        return '<{0.__class__.__name__} for {0.root}>'.format(self)

    def __repr__(self):
        return '<{0.__class__.__name__}({0.root}) at {1}>'.format(
            self, hex(id(self))
        )

    ConnectionError = requests.exceptions.ConnectionError
    HTTPError = requests.exceptions.HTTPError
    Timeout = requests.exceptions.Timeout


import requests.exceptions

class Transport(object):

    def __init__(self, host, default_timeout=30):
        self.host = host
        
        import requests
        self.session = requests.Session()
        
        # Needed otherwise requests will not be authenticated correctly.
        self.session.headers['User-Agent'] = 'SKY_skyplus'
        self.default_timeout = default_timeout
        
    def __url(self, location):
        if '://' in location:
            return location
        if location.startswith('/'):
            location = location[1:]
        return 'http://{0}:49153/{1}'.format(self.host, location) 
        
    def get_resource(self, location, timeout=None, raw_resp=False):
        url = self.__url(location)
        
        import requests
        req = requests.Request('GET', url)
        req = self.session.prepare_request(req)
        resp = self.send_request(req, timeout=timeout)
        if not raw_resp:
            resp.raise_for_status()
        return resp
        
    def send_request(self, req, timeout=None):
        return self.session.send(req, timeout=timeout)
        
    def soap_request(self, location, schema, method, soapbody,
        timeout=None, raw_resp=False):
        url = self.__url(location)
        
        # Quotes around the soap-action header is important - you will
        # get a 500 error otherwise. Same with the Content-Type - if
        # this is missing, a 500 response is returned.
        headers = {
            'SOAPACTION': '"{0}#{1}"'.format(schema, method),
            'Content-Type': 'text/xml; charset="utf-8"',
        }

        # XXX: Might need some encoding checks here.
        import requests
        req = requests.Request('POST', url, headers=headers,
            data=soapbody)
        req = self.session.prepare_request(req)
        resp = self.send_request(req, timeout=timeout or self.default_timeout)
        if not raw_resp:
            resp.raise_for_status()
        return resp
        
    def __str__(self):
        return '<{0.__class__.__name__} for {0.host}>'.format(self)

    def __repr__(self):
        return '<{0.__class__.__name__}({0.host}) at {1}>'.format(
            self, hex(id(self))
        )
    
    ConnectionError = requests.exceptions.ConnectionError    
    HTTPError = requests.exceptions.HTTPError
    Timeout = requests.exceptions.Timeout
    

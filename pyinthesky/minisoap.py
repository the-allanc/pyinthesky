def soap_encode(elements):
    if not isinstance(elements, (tuple, list)):
        raise ValueError('must pass a sequence of Element objects')

    from .xmlutils import ElementTree as ET
    res = ET.Element('s:Envelope')
    res.attrib['xmlns:s'] = "http://schemas.xmlsoap.org/soap/envelope/"
    res.attrib['s:encodingStyle'] = "http://schemas.xmlsoap.org/soap/encoding/"
    body = ET.SubElement(res, 's:Body')
    for element in elements:
        body.append(element)
    return ET.ElementTree(res)


def soap_decode(etree):
    from functools import partial
    from .xmlutils import nstag
    tag = partial(nstag, etree)

    body = etree.find(tag('Body'))

    # Is there a SOAP fault here?
    fault = body.find(tag('Fault'))
    if fault is not None:
        faultcode = fault.find('faultcode').text
        faultstring = fault.find('faultstring').text

        # Which exception class? You can get strings like this:
        #   "s:Client.Authentication"
        #
        # So we drop the namespace qualifier and only pay attention to
        # the first element to determine the class type.
        faultcode = faultcode.split(':', 1)[-1]
        faulttype = faultcode.split('.', 1)[0]
        faultclass = {
            'Client': SoapClientError,
            'Server': SoapServerError,
        }.get(faulttype, SoapError)

        detail = fault.find('detail')
        raise faultclass(faultcode, faultstring, detail.getchildren())

    # Otherwise, it's just a normal response, and we want to return the
    # content.
    #
    # from .xmlutils import ElementTree as ET
    # ET.dump(body)
    return body.getchildren()


class SoapError(Exception):

    def __init__(self, code, message, details):
        Exception.__init__(self, '%s: %s' % (code, message))
        self.code = code
        self.message = message
        self.details = details


class SoapClientError(SoapError):
    pass


class SoapServerError(SoapError):
    pass

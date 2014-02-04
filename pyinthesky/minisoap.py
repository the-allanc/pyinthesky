def soap_request(schema, action, parameters):
    from xml.etree.ElementTree import ElementTree, Element, SubElement
    res = Element('s:Envelope')
    res.attrib['xmlns:s'] = "http://schemas.xmlsoap.org/soap/envelope/"
    res.attrib['s:encodingStyle'] = "http://schemas.xmlsoap.org/soap/encoding/"
    body = SubElement(res, 's:Body')
    mbody = SubElement(body, 'u:' + action)
    mbody.attrib['xmlns:u'] = schema
    for key, value in parameters.items():
        param = SubElement(mbody, key)
        if not isinstance(value, basestring):
            raise ValueError(
                'Value for parameter %s needs to be string type: %r'
                % (key, value))
        param.text = value
    return res

def soap_response(etree, action_name):
    from functools import partial
    from utils import simple_elements_dict, nstag, baretag
    tag = partial(nstag, etree)

    body = etree.find(tag('Body'))
    for respblock in body.getchildren():
        if respblock.tag.endswith(action_name + 'Response'):
            break
    else:
        raise RuntimeError, 'xxx'
        
    return simple_elements_dict(respblock)
        
    return {
        baretag(bodypart): simple_elements_dict(bodypart)
        for bodypart in respblock
    }

from .xmlutils import text_to_etree as _text_to_xml

def default_validator(service_type, key, value):
    from .validators import create_validator
    return create_validator(value, key)

class Connection(object):
    
    # XXX: Expose timeout argument.
    def __init__(self, host):
        from pyinthesky.transport import Transport
        self.transport = Transport(host)
        self.create_validator = default_validator
        
    def connect(self):
        from pyinthesky.miniupnp import parse_device_description
        resources = ['description0.xml', 'description2.xml']
        upnp_devices = []
        for resource in resources:
            res_resp = self.transport.get_resource(resource)
            resp_xml = _text_to_xml(res_resp.text)
            upnp_devices.append(parse_device_description(resp_xml))
        
        # Expose devices.
        self.devices = {}
        for upnp_device in upnp_devices:
            self.devices[upnp_device.devtype] = Device(self, upnp_device)
        
class Device(object):
    
    def __init__(self, connection, upnp_device):
        self.connection = connection
        self.upnp_device = upnp_device
        self.services = {
            s.name: Service(self, s)
            for s in upnp_device.services.values()
        }
        
    def __getattr__(self, name):
        return getattr(self.upnp_device, name)
        
    def __str__(self):
        return str(self.upnp_device)
        
    # XXX: Maybe not.
    def __repr__(self):
        return repr(self.upnp_device)
        
class Service(object):
    
    def __init__(self, device, upnp_service):
        self.device = device
        self.name = upnp_service.name
        self.upnp_service = upnp_service

    def __getattr__(self, name):
        return getattr(self.upnp_service, name)
        
    def connect(self):
        from pyinthesky.miniupnp import parse_service_description
        schema_resp = self.transport.get_resource(self.description_url)
        schema_xml = _text_to_xml(schema_resp.text)
        self.service_desc = parse_service_description(schema_xml)
        
        # Create validators for all value types (states).
        #
        # It's a map from statevar objects to validators.
        validators = {
            v: self.create_validator(self.upnp_service.servtype, k, v)
            for (k, v) in self.service_desc.states.items()
        }
        
        # And now create input and output validators for methods.
        from pyinthesky.validators import create_multivalidator
        self.methods = {}
        for name, action in self.service_desc.actions.items():
            in_vals = {k: validators[v] for (k, v) in action.parameters.items()}
            out_vals = {k: validators[v] for (k, v) in action.returns.items()}
            self.methods[name] = [
                create_multivalidator(in_vals, name),
                create_multivalidator(out_vals, name),
            ]
            
    def invoke(self, action_name, *args, **kwargs):
        
        from pyinthesky import minisoap, miniupnp, xmlutils
        
        # Find the action definition and get the argument order.
        in_valid, out_valid = self.methods[action_name]
        
        # Then take the positional arguments and normalise them to
        # keyword-only arguments.
        try:
            kw = xmlutils.args_to_kwargs(args, kwargs, in_valid.argument_order)
        except TypeError as te:
            raise TypeError(action + ' ' + te)
        
        # Next, validate and convert the arguments.
        try:
            kw_to_use = in_valid.output(kw)
        except in_valid.Invalid as e:
            raise ValueError(e)
        
        # Build a UPNP request, then bundle that into SOAP.
        schema = self.upnp_service.service_type
        upnp_req = miniupnp.encode_action_request(schema, action_name, kw_to_use)
        soap_req = minisoap.soap_encode([upnp_req])
        
        # Submit it to the control URL.
        respobj = self.transport.soap_request(
            self.upnp_service.control_url, schema, action_name,
            xmlutils.etree_to_text(soap_req), raw_resp=True
        )
        
        # Try to interpret it as a SOAP response - it may be an error
        # response too.
        try:
            resp_etree = xmlutils.text_to_etree(respobj.content)
        except xmlutils.ElementTree.ParseError:
            # Just raise the original HTTP error - but if there wasn't
            # one (curious), then raise an error complaining about the
            # inability to parse the XML.
            respobj.raise_for_status()
            raise
            
        # Decode the SOAP response.
        try:
            upnp_resp = minisoap.soap_decode(resp_etree)
        except minisoap.SoapError as se:
            # Check to see if it's a UPnPError wrapped inside a Soap error.
            ue = miniupnp.check_upnp_error(se)
            if ue is None:
                raise

            # Check to see if it specifically refers to a problem with
            # a given value.
            if not miniupnp.is_action_value_error(ue):
                raise ue
                
            ave = ActionValueError(ue.desc)
            ave.cause = ue
            raise ave

        # There should only be one response body.
        if len(upnp_resp) == 0:
            untyped_result = {}
        elif len(upnp_resp) == 1:
            untyped_result = miniupnp.decode_action_response(
                action_name, upnp_resp[0])
        else:
            raise RuntimeError('%s body parts inside UPnP response' % len(upnp_resp))
            
        # Break values out from their UPnP structure, and then convert
        # the value types appropriately.
        result = out_valid.input(untyped_result)
        
        # Return either the dictionary structure if populated, or None
        # if empty.
        return result or None

    @property
    def transport(self):
        return self.device.connection.transport
        
    @property
    def create_validator(self):
        return self.device.connection.create_validator

class ActionValueError(ValueError): pass

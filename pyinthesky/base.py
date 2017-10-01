from .xmlutils import text_to_etree as _text_to_xml
from six.moves import range
from six.moves.urllib.parse import urlparse
import six

from requests import Timeout
def locate(host=None, port=None, internal=True, timeout=5):
    if not (host or internal):
        raise ValueError('cannot make external connection with no explicit host given')
    if internal:
        return locate_by_ssdp(host=host, timeout=timeout)
    else:
        return locate_by_resource(host, port)


def locate_by_ssdp(service_types=None, host=None, timeout=5):
    from greyupnp.ssdp import search as ssdp_search

    if service_types is None:
        from pyinthesky import SERVICE_TYPES
        service_types = SERVICE_TYPES

    if not isinstance(service_types, dict):
        service_types = dict.fromkeys(service_types, True)

    # This is where we'll store discovery objects as they're returned.
    collected = set()
    searches = ssdp_search(tuple(service_types), timeout)

    def host_matches(discovery):
        urlobj = urlparse(discovery.location)
        return (not host) or host in (urlobj.netloc, urlobj.hostname)

    for (service_type, required) in service_types.items():

        # See if we've found the service type already.
        res = None

        for discovery in collected:
            if discovery.type == service_type and host_matches(discovery):
                res = discovery
                break

        # Otherwise, listen to incoming search results and see if that matches.
        if not res:
            for discovery in searches:
                collected.add(discovery)
                if discovery.type == service_type and host_matches(discovery):
                    res = discovery
                    break

        # Return a result if we found it...
        if res:
            yield res.location
            continue

        # Or complain if we didn't find it, yet need it...
        elif required:
            err = 'unable to find service of type "%s" within %s seconds'
            raise Timeout(err % (service_type, timeout))


# Iterate over this resource.
def locate_by_resource(host, port=None, timeout=5):
    from .transport import Transport
    t = Transport(host, port, default_timeout=timeout)

    # How many services do we need to find?
    from pyinthesky import SERVICE_TYPES as ST
    min_services = len([x for x in ST.values() if x])
    max_services = len(ST)

    # We look to find the first item.
    import time
    finish_by = time.time() + timeout
    counted = 0

    # Not sure if there's a maximum number for descriptions.
    for i in range(1000):
        loc = 'description%d.xml' % i
        now = time.time()
        if now > finish_by:
            err = 'couldn\'t find all the resources for host "%s"'
            raise t.Timeout(err % host)

        # Found a resource!
        r = t.get_resource(loc, raw_resp=True, timeout=finish_by-now)

        if r.status_code == 200:
            counted += 1
            last_loop_found = True
            yield r.url

            # Found as many resources as we know about, so just
            # return.
            if counted >= max_services:
                return

        elif r.status_code == 404:
            # If we didn't find a resource, then...
            #   * If we haven't found one before, then keep iterating
            #     until we find the first.
            #   * If we have found one before, then I guess that's
            #     as many as we can find - it's a problem if we
            #     have found at least the minimum number.
            #   * Although we normally have resources next to each
            #     other (orderwise), sometimes we have gaps (e.g.
            #     0,2 or, 0,1,3) so we allow single item gaps.
            if not counted:
                last_loop_found = False
                continue
            if last_loop_found:
                last_loop_found = False
                continue
            if counted < min_services:
                err = 'did not find enough resources for host "%s" (found %s, needed %s)'
                raise RuntimeError(err % (host, counted, min_services))
            else:
                return

        # No idea what to do in this case, we're not expecting it.
        else:
            r.raise_for_status()



def default_validator(service_type, key, value):
    from .validators import create_validator
    return create_validator(value, key)

class Connection(object):

    def __init__(self, resources, default_timeout=None):
        from pyinthesky.transport import Transport
        if isinstance(resources, six.string_types):
            raise ValueError('resources must be an iterator of strings, not a string type')

        self.resources = tuple(resources)
        if not self.resources:
            raise ValueError("at least one resource is needed")

        self.create_validator = default_validator

        # Look for a common root if we can.
        from pyinthesky.utils import common_url_prefix
        root = common_url_prefix(self.resources)
        fixed_root = bool(root)

        self.transport = Transport(root=root, fixed_root=fixed_root,
            default_timeout=default_timeout)

    def connect(self):
        from pyinthesky.miniupnp import parse_device_description
        upnp_devices = []
        for resource in self.resources:
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
            v: self.create_validator(self.upnp_service.servtype, k, v) # pylint: disable=not-callable
            for (k, v) in self.service_desc.states.items()
        }

        # And now create input and output validators for methods.
        from pyinthesky.validators import create_multivalidator
        from collections import OrderedDict as OD
        self.methods = {}
        for name, action in self.service_desc.actions.items():
            in_vals = OD((k, validators[v]) for (k, v) in action.parameters.items())
            out_vals = OD((k, validators[v]) for (k, v) in action.returns.items())
            self.methods[name] = [
                create_multivalidator(in_vals, name),
                create_multivalidator(out_vals, name),
            ]

    def invoke(self, action_name, *args, **kwargs):

        from pyinthesky import minisoap, miniupnp, utils, xmlutils

        # Find the action definition and get the argument order.
        in_valid, out_valid = self.methods[action_name]

        # Then take the positional arguments and normalise them to
        # keyword-only arguments.
        try:
            kw = utils.args_to_kwargs(args, kwargs, in_valid.argument_order)
        except TypeError as te:
            raise TypeError('{} [{}]'.format(te, action_name))

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
            resp_etree = xmlutils.text_to_etree(respobj.text)
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
                raise ue  # pylint: disable=raising-bad-type

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

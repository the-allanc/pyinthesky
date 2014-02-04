# Found this resource really helpful:
#  http://www.upnp-hacks.org/upnp.html

#
#
# Service Description code.
#
#

def parse_service_description(etree):
    from functools import partial
    from utils import nstag
    tag = partial(nstag, etree)

    #
    # Step 1: Process service state types.
    #    
    sst = etree.find(tag('serviceStateTable'))
    
    states = {}
    for statevar in sst.iter(tag('stateVariable')):
        name = statevar.find(tag('name')).text
        datatype = statevar.find(tag('dataType')).text
        
        # I'm considering a blank default value tag to be the same as
        # not having one at all. Perhaps that will need to change.
        default_value = getattr(statevar.find(tag('defaultValue')), 'text', '') or None
        
        allowed_values = min_value = max_value = None

        # Handle string types.        
        if datatype == 'string':
            pytype = unicode
            
            # Check for restricted allowed values.
            allowvals = statevar.find(tag('allowedValueList'))
            if allowvals is not None:
                allowed_values = [v.text for v in allowvals]
                
        # Handle integer types.
        elif datatype in ['ui2', 'ui4', 'i4']:
            pytype = int
            if default_value is not None:
                default_value = int(default_value)
                
            # Although we may or may not have defined minimum and
            # maximum values, we start off using the limits as defined
            # by the integer byte size.
            min_value, max_value = {
                'ui2': (0, 256 ** 2 - 1),
                'ui4': (0, 256 ** 4 - 1),
                'i4': (- 256 ** 4, 256 ** 4 - 1),
            }[datatype]
            
            # Look for explicit limits given.
            allowrange = statevar.find(tag('allowedValueRange'))
            if allowrange is not None:
                min_value = int(allowrange.find(tag('minimum')).text)
                max_value = int(allowrange.find(tag('maximum')).text)
            
        else:
            # XXX: May want to change this in future to be more tolerant.
            raise RuntimeError('Invalid data type: %s' % (datatype))
            
        svarobj = StateVariable(name, datatype, pytype)
        svarobj.send_events = statevar.get('sendEvents') == 'yes'
        svarobj.xml = statevar
        
        for varname in ['allowed_values', 'default_value',
            'min_value', 'max_value']:
            if vars()[varname] is not None:
                setattr(svarobj, varname, vars()[varname])

        states[name] = svarobj
        
    #
    # Step 2: Process actions.
    #
    from collections import OrderedDict
    acts = etree.find(tag('actionList'))
    
    actions = {}
    for action in acts.iter(tag('action')):
        argument_list = action.find(tag('argumentList'))
        if argument_list is None:
            argument_list = []
        
        in_args, out_args = OrderedDict(), OrderedDict()
        
        for argument in argument_list:
            direction = argument.find(tag('direction')).text
            argdict = {'in': in_args, 'out': out_args}[direction]
            argname = argument.find(tag('name')).text
            statevar = states[argument.find(tag('relatedStateVariable')).text]
            argdict[argname] = statevar
            
        action = Action(name=action.find(tag('name')).text,
            parameters=in_args, returns=out_args)
    
        actions[action.name] = action
        
    return ServiceControl(actions, states)
    
class StateVariable(object):
    
    allowed_values = None
    default_value = None
    min_value = None
    max_value = None
    
    def __init__(self, name, datatype, pytype):
        self.name = name
        self.datatype = datatype
        self.pytype = pytype
        
    def __str__(self):
        return '<StateVariable for {0.name} ({0.pytype.__name__})>'.format(self)
        
    def __repr__(self):
        return '<StateVariable(name="{0.name}", datatype="{0.datatype}">'.format(self)

class Action(object):
    
    def __init__(self, name, parameters, returns):
        self.name = name
        self.parameters = parameters
        self.returns = returns
            
    def __str__(self):
        return '<Action for {0.name}({1})>'.format(self, ', '.join(self.parameters.keys()))

    def __repr__(self):
        return '<Action(name="{0.name}")">'.format(self)

class ServiceControl(object):
    
    def __init__(self, actions, states):
        self.actions = actions
        self.states = states

#
#
# Device description code.
#
#
def parse_device_description(etree):
    from functools import partial
    from utils import simple_elements_dict, nstag
    tag = partial(nstag, etree)
    
    device_element = etree.find(tag('device'))
    device_attrs = simple_elements_dict(device_element)
    
    services_element = device_element.find(tag('serviceList'))
    services_attrs = []
    for serv_element in services_element.iter(tag('service')):
        services_attrs.append(simple_elements_dict(serv_element))
        
    url_base = getattr(etree.find(tag('URLBase')), 'text', None)
    
    # First, we create the services.
    services = [Service(sa_dict, url_base) for sa_dict in services_attrs]
    service_dict = {s.name: s for s in services}
    
    # Now we create the device object.
    device = Device(device_attrs, service_dict, url_base)
    return device

class Service(object):
    
    def __init__(self, attrs, url_base=None):
        from urlparse import urlparse, urljoin
        self.attributes = attrs
        
        # We present some friendlier attribute information via these
        # names.
        self.service_id = attrs['serviceId']
        self.service_type = attrs['serviceType']
        self.description_url = urljoin(url_base, attrs['SCPDURL'])
        self.control_url = urljoin(url_base, attrs['controlURL'])
        self.events_url = urljoin(url_base, attrs['eventSubURL'])
        
        # We give our service a more readable name and type.
        self.name = self.service_id.split(':')[-1]
        self.servtype = self.service_type.split(':')[-2]
        
        # Our location for the service will be based on the control
        # URL.
        location = urlparse(self.control_url)
        self._location = location.hostname
        if location.port:
            self._location += ':%s' % location.port
        
    def __str__(self):
        return '<Service "{0.name}" for {0._location}>'.format(self)
        
    def __repr__(self):
        return ('<pyinthesky.miniupnp.Service(name="{0.name}", '
            'servtype="{0.servtype}") at "{0._location}">').format(self)

class Device(object):
    
    def __init__(self, attrs, services, url_base):
        self.attributes = attrs
        self.services = services
        
        # More accessible attributes here.
        self.model_name = attrs['modelName']
        self.model_number = attrs['modelNumber']
        self.friendlyname = attrs['friendlyName']
        self.device_type = attrs['deviceType']
        
        # Easier to read information.
        self.devtype = self.device_type.split(':')[-2]
        assert attrs['UDN'].startswith('uuid:')
        self.uuid = attrs['UDN'][5:]
        
    def __str__(self):
        return '<Device "{0.devtype}" ({0.model_name})>'.format(self)
        
    def __repr__(self):
        attrs = []
        attrs.append('devtype="{0.devtype}"')
        attrs.append('model_name="{0.model_name}"')
        attrs.append('model_number="{0.model_number}"')
        attrs.append('uuid="{0.uuid}"')
        
        return '<pyinthesky.miniupnp.Device(' + \
            (', '.join(attrs)).format(self) + ')'

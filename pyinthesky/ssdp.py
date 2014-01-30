from formencode.validators import Invalid

def parse(etree):
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
            if allowvals:
                allowed_values = [v.text for v in allowvals]
                
        # Handle integer types.
        elif datatype in ['ui2', 'ui4', 'i4']:
            pytype = int
            if default_value is not None:
                default_value = int(default_value)
                
            # Although we may or may not have defined minimum and
            # maximum values, we start off using the limits as defined
            # by the integer bit size.
            min_value = {'ui2': 0, 'ui4': 0, 'i4': -16}[datatype]
            max_value = {'ui2': 3, 'ui4': 15, 'i4': 15}[datatype]
            
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
        argument_list = action.find(tag('argumentList')) or []
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
        
    return Service(actions, states)
    
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
        return '<StateVariable(name="{0.name}", type="{0.datatype}">'.format(self)

class Action(object):
    
    def __init__(self, name, parameters, returns):
        self.name = name
        self.parameters = parameters
        self.returns = returns
            
    def __str__(self):
        return '<Action for {0.name}({1})>'.format(self, ', '.join(self.parameters.keys()))

    def __repr__(self):
        return '<Action(name="{0.name}")">'.format(self)

class Service(object):
	
	def __init__(self, actions, states):
		self.actions = actions
		self.states = states


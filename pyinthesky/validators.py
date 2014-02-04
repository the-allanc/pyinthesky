from formencode.api import Invalid
from formencode.validators import Wrapper
_unicode_out = Wrapper(convert_from_python=unicode)
del Wrapper

class Validator(object):
    
    def __init__(self, validator, wrapper=_unicode_out):
        self._identifier = validator
        if wrapper is not None:
            from formencode.compound import Pipe
            validator = Pipe(wrapper, validator)
        self.validator = validator
        
    def input(self, value):
        return self.validator.to_python(value)
        
    def output(self, value):
        return self.validator.from_python(value)
        
    def __str__(self):
        return '<Validator (%s)>' % self._identifier
        
    def __repr__(self):
        return '<Validator (%r)>' % self._identifier
        
def create_validator(objdesc, varname):
    args, kw = [], {}
    
    from formencode.validators import ConfirmType, OneOf, Int 
    if objdesc.pytype is unicode:
        if objdesc.allowed_values:
            vc = OneOf
            args = [objdesc.allowed_values]
        else:
            vc = ConfirmType
            kw = {'subclass': basestring}
    elif objdesc.pytype is int:
        vc = Int
        kw = dict(min=objdesc.min_value, max=objdesc.max_value)
    else:
        raise ValueError('cannot create validator for %s' % objdesc.pytype)
        
    if objdesc.default_value is not None:
        kw['if_missing'] = objdesc.default_value

    v = vc(*args, **kw)
    return Validator(v)

def create_multivalidator(validator_dict, varname):
    from formencode.schema import NoDefault, Schema
    
    defaults = {}
    identifiers = {}
    
    s = Schema()        
    for varname, validator in validator_dict.items():
        s.add_field(varname, validator.validator)
        identifiers[varname] = validator._identifier
        
        # if_missing values don't get picked up for "from_python", so we
        # create a custom wrapper to present those defaults.
        if validator.validator.if_missing is not NoDefault:
            defaults[varname] = validator.validator.if_missing
            
    def include_defaults(value):
        d = defaults.copy()
        d.update(value)
        return d
        
    from formencode.validators import Wrapper
    v = Validator(s, Wrapper(convert_from_python=include_defaults))
    v.arg_order = validator_dict.keys()
    v._identifier = identifiers
    return v

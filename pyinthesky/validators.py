from formencode.api import Invalid
from formencode.validators import Wrapper
_unicode_out = Wrapper(convert_from_python=unicode)
del Wrapper

class Validator(object):
    
    def __init__(self, validator, ident_string, output_wrapper=None):
        self.in_validator = validator
        self.out_validator = validator
        self.ident = ident_string
        
        if output_wrapper is not None:
            from formencode.compound import Pipe
            self.out_validator = Pipe(validator, output_wrapper)
        
    def input(self, value):
        return self.in_validator.to_python(value)
        
    def output(self, value):
        return self.out_validator.to_python(value)

    Invalid = Invalid
        
    def __str__(self):
        return '<Validator(%s)>' % self.ident
        
    def __repr__(self):
        return '<Validator(%s) at %s>' % (self.ident, hex(id(self)))
        
def create_validator(objdesc, varname):
    args, kw = [], {}
    
    from formencode.validators import ConfirmType, OneOf, Int 
    if objdesc.pytype is unicode:
        if objdesc.allowed_values:
            vc = OneOf
            args = [objdesc.allowed_values]
            ident = 'enum text'
        else:
            vc = ConfirmType
            kw = {'subclass': basestring}
            ident = 'text'
    elif objdesc.pytype is int:
        vc = Int
        kw = dict(min=objdesc.min_value, max=objdesc.max_value)
        ident = 'int' if objdesc.max_value is None else 'int-range'
    else:
        raise ValueError('cannot create validator for %s' % objdesc.pytype)
        
    if objdesc.default_value is not None:
        kw['if_missing'] = objdesc.default_value
        ident += ' with default'

    v = vc(*args, **kw)
    return Validator(v, ident, output_wrapper=_unicode_out)

def create_multivalidator(validator_dict, varname):
    
    identifiers = []
    
    def _dict_values_to_unicode(value):
        return dict((k, unicode(v)) for (k, v) in value.items())
    
    from formencode.schema import Schema
    s = Schema()
    for varname, validator in validator_dict.items():
        s.add_field(varname, validator.in_validator)
        identifiers.append("%s='%s'" % (varname, validator.ident))
        
    from formencode.validators import Wrapper    
    wrap = Wrapper(convert_to_python=_dict_values_to_unicode)
    
    v = Validator(s, ', '.join(identifiers), output_wrapper=wrap)
    v.argument_order = validator_dict.keys()
    return v

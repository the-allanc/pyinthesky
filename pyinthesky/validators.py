from formencode.api import Invalid, NoDefault as _NoDefault
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
    if objdesc.pytype is unicode:

    from formencode import validators as validmod
        if objdesc.allowed_values:
            vc = validmod.OneOf
            args = [objdesc.allowed_values]
            ident = 'enum text'
        else:
            vc = validmod.ConfirmType
            kw = {'subclass': basestring}
            ident = 'text'
    elif objdesc.pytype is int:
        vc = validmod.Int
        kw = dict(min=objdesc.min_value, max=objdesc.max_value)
        ident = 'int' if objdesc.max_value is None else 'int-range'
    elif objdesc.pytype is bool:
        vc = validmod.StringBool
        kw = dict(
            false_values='0 false no'.split(),
            true_values='1 true yes'.split()
        )
        ident = 'boolean'
    else:
        raise ValueError('cannot create validator for %s' % objdesc.pytype)

    if objdesc.default_value is not None:
        kw['if_missing'] = objdesc.default_value
        ident += ' with default'

    v = vc(*args, **kw)
    return Validator(v, ident, output_wrapper=_unicode_out)

def create_multivalidator(validator_dict, varname):

    identifiers = []
    defaults = {}

    def _dict_values_to_unicode(value):
        return dict((k, unicode(v)) for (k, v) in value.items())

    from formencode.schema import Schema
    s = Schema()
    for subvarname, subvalidator in validator_dict.items():
        s.add_field(subvarname, subvalidator.in_validator)
        identifiers.append("%s='%s'" % (subvarname, subvalidator.ident))
        the_default = subvalidator.in_validator.if_missing
        if the_default is not _NoDefault:
            defaults[subvarname] = the_default

    from formencode.validators import Wrapper
    wrap = Wrapper(convert_to_python=_dict_values_to_unicode,
        empty_value=dict)

    v = Validator(s, ', '.join(identifiers), output_wrapper=wrap)
    v.argument_order = validator_dict.keys()
    v.argument_defaults = defaults
    return v

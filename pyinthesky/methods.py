# XXX: Suggestions for improvement.
#  1. The ability to indicate what arguments should be passed in
#     positionally. True for all, or sequence for specific ordering.
#  2. Support for *args
#  3. Support for **kwargs.
def method_sig_wrapper(target, name, varnames, defaults=None):
    
    # First of all, defaults will need to be a tuple rather than a
    # dictionary.
    defaults_l = []
        
    # Translating the dictionary into the sequence required.
    if defaults:
        defaults_d = defaults.copy()
        
        # We get the X last variable names - they are presumably the
        # variables which have defaults.
        for argname in varnames[-len(defaults):]:
            try:
                defaults_l.append(defaults_d.pop(argname))
            except KeyError:
                # XXX: We've got awkward method definitions - we need to
                # be able to handle this gracefully:
                #   SetAVTransportURI ['InstanceID', 'CurrentURIMetaData', 'CurrentURI'] {'CurrentURIMetaData': 'NOT_IMPLEMENTED'}
                defaults_l = []
                defaults_d = {}
                break
                raise ValueError("require default value for '%s'" % argname)
        if defaults_d:
            raise ValueError("default provided for unspecified varname: '%s'" % defaults_d.keys()[0])
    
    del defaults
    
    argstr = ', '.join(varnames)
    wrapfunc = 'def {name}({argstr}): return _target_(**locals())\n'
    wrapfunc = wrapfunc.format(**vars())
    wrapcode = compile(wrapfunc, '<generated_function>', 'exec')
    global_ns = {}
    eval(wrapcode, {'_target_': target}, global_ns)
    f = global_ns[name]
    f.func_defaults = tuple(defaults_l)
    return f

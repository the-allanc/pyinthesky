# XXX: Suggestions for improvement.
#  1. The ability to indicate what arguments should be passed in
#     positionally. True for all, or sequence for specific ordering.
#  2. Support for *args
#  3. Support for **kwargs.
#
# Should be called func_sig_wrapper
def method_sig_wrapper(target, name, varnames, defaults=None,
    make_method=False):

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

    if make_method:
        argstr = ', '.join(['self'] + list(varnames))
        wrapfunc = (
            "def {name}({argstr}): __locals__ = locals(); "
            "__locals__.pop('self'); return _target_(**__locals__)\n"
        )
    else:
        argstr = ', '.join(varnames)
        wrapfunc = 'def {name}({argstr}): return _target_(**locals())\n'

    wrapfunc = wrapfunc.format(**vars())
    wrapcode = compile(wrapfunc, '<generated_function>', 'exec')
    global_ns = {}
    eval(wrapcode, {'_target_': target}, global_ns)
    f = global_ns[name]
    f.func_defaults = tuple(defaults_l)
    return f

_ambiguous_docstring = '''
This is a convenience function which cannot be used, as there are multiple
methods available with the same name. You will have to call the required
methods more directly:
'''.strip() + '\n'

def make_ambiguous_function(name, func_locations):
    e = 'method "%s" is ambiguous - will need to invoke directly from service'
    def cant_do_it(*args, **kwargs):
        raise RuntimeError(e % name)
    cant_do_it.__name__ = name
    describes = '\n'.join(['  - ' + fl for fl in func_locations])
    cant_do_it.__doc__ = _ambiguous_docstring + describes
    return cant_do_it

# XXX: Add docstrings...
def bind_service_methods(target, services=None, bind_to_class=False):
    if services is None:
        services = [target]

    from pyinthesky import meta
    bind_to_meta = bind_target_class = False

    if bind_to_class is True:
        target_class = target.__class__
    elif bind_to_class is False:
        target_class = None
    elif hasattr(meta, bind_to_class):
        target_class = getattr(meta, bind_to_class)
        bind_target_class = True
    else:
        target_class = type(bind_to_class, (target.__class__,), {})
        target_class.__module__ = 'pyinthesky.meta'
        bind_to_meta = True
        bind_target_class = True

    from functools import partial
    serv_methods = {}
    for service in services:
        for methname, (in_args, out_args) in service.methods.items():
            func = partial(service.invoke, methname)
            args = list(in_args.argument_order)
            f = method_sig_wrapper(func, methname, args,
                in_args.argument_defaults,
                make_method=target_class is not None)
            serv_methods.setdefault(methname, []).append([
                f, service.name + '.' + methname,
            ])

    # We've now built functions for all remote methods, so see what we
    # can set and what we can't.
    from types import MethodType
    for methname, methods in serv_methods.items():
        if len(methods) == 1:
            f = methods[0][0]
        else:
            f = make_ambiguous_function(methname, [x[1] for x in methods])
        if target_class is None:
            setattr(target, methname, f)
        else:
            setattr(target_class, methname, MethodType(f, None, target_class))

    if bind_target_class:
        target.__class__ = target_class
    if bind_to_meta:
        setattr(meta, target_class.__name__, target_class)
    return dict((k, len(serv_methods[k]) == 1) for k in serv_methods)

def build_service_methods(service, as_class_methods=False):
    if not hasattr(service, methods):
        raise ValueError('cannot pass unconnected service object')

    method_registry = {}
    for methname, (in_args, out_args) in service.methods.items():
        if as_class_methods:
            target = partial(service.__class__.invoke, action_name=methname)
        else:
            target = partial(service.invoke, methname)
        f = mkfunc(target, methname, in_args.argument_order, in_args.argument_defaults)
        method_registry[methname] = f
    return method_registry

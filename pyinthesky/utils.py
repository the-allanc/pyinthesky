def args_to_kwargs(args, kwargs, argnames):

    # Check we haven't exceeded the number of allowed arguments.
    argcount = len(args) + len(kwargs)
    if argcount > len(argnames):
        errmsg = {
            0: "takes no arguments ({1} given)",
            1: "takes exactly 1 argument ({1} given)",
        }.get(argcount, "takes exactly {0} arguments ({1} given)")
        raise TypeError(errmsg.format(len(argnames), argcount))

    # Check we haven't defined both arguments and keyword arguments for the
    # same. We turn argnames into a list in case we have a dict-keys object.
    for argname in list(argnames)[:len(args)]:
        if argname in kwargs:
            err = "got multiple values for keyword argument '%s'"
            raise TypeError(err % argname)

    # Combine the values.
    res = kwargs.copy()
    res.update(zip(argnames, args))
    return res


# Based around this: http://rosettacode.org/wiki/Find_Common_Directory_Path#Python
def common_url_prefix(urls):
    def same(values):
        return all(v == values[0] for v in values[1:])

    from six.moves.urllib import parse
    parsed = [parse.urlparse(url) for url in urls]

    # We need the same protocol and netloc (host/port), otherwise there
    # is not a common prefix.
    if not same([u[:2] for u in parsed]):
        return None

    # If we get here, it means we have a shared protocol and netloc, so
    # now we just compare paths.
    from itertools import takewhile as tw
    parts = zip(*[p.path.split('/') for p in parsed])
    commonpath = '/'.join(x[0] for x in tw(same, parts))

    res_parts = parsed[0][:2] + (commonpath, '', '', '')
    res = parse.urlunparse(res_parts)
    if res[-1] != '/':
        res += '/'
    return res

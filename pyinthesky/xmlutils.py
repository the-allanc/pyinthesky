# Expose the "best" ElementTree implementation available.
try:
	from xml.etree import cElementTree as ElementTree
except ImportError:
	from xml.etree import ElementTree as ElementTree

def text_to_etree(content):
    from StringIO import StringIO
    return ElementTree.parse(StringIO(content))
    
def etree_to_text(etree):
	return ElementTree.tostring(etree.getroot())

def nstag(tree, tag):
    # If you use the lxml implementation of etree, it's easier to get
    # the schema qualifier:
    #   schema = tree.getroot().nsmap[None]
    #
    # That would return the schema without the curly braces.
    roottag = tree.getroot().tag
    if '}' not in roottag:
        return tag # No schema.
    schema = roottag.split('}', 1)[0] + '}'
    return '{0}{1}'.format(schema, tag)

def simple_elements_dict(node):
    d = {}
    for childnode in node.getchildren():
        tagname = childnode.tag
        if '}' in tagname:
            tagname = tagname.split('}')[-1]
        text = childnode.text.strip()
        if text:
            d[tagname] = text
    return d

def args_to_kwargs(args, kwargs, argnames):

    # Check we haven't exceeded the number of allowed arguments.
    argcount = len(args) + len(kwargs)  
    if argcount > len(argnames):
        errmsg = {
            0: "takes no arguments ({1} given)",
            1: "takes exactly 1 argument ({1} given)",
        }.get(argcount, "takes exactly {0} arguments ({1} given)")
        raise TypeError(errmsg.format(len(argnames), argcount))
    
    # Check we haven't defined both arguments and keyword arguments for
    # the same.
    for argname in argnames[:len(args)]:
        if argname in kwargs:
            err = "got multiple values for keyword argument '%s'"
            raise TypeError(err % argname)

    # Combine the values.
    res = kwargs.copy()
    res.update(zip(argnames, args))
    return res

def striptag(node):
    return node.tag.split('}')[-1]

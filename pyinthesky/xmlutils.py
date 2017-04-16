# Expose the "best" ElementTree implementation available.
#
# Got to be careful with what combinations of modules we use here - see:
#   http://bugs.python.org/issue20612
try:
    from xml.etree import cElementTree as ElementTree
    from cStringIO import StringIO as _StrIO
except ImportError:
    from xml.etree import ElementTree as ElementTree
    from StringIO import StringIO as _StrIO
    

def text_to_etree(content):
    if isinstance(content, unicode):
        content = content.encode('utf-8')
    return ElementTree.parse(_StrIO(content))

def etree_to_text(etree):
    return ElementTree.tostring(etree.getroot())

# May need to implement strip_schema. Look at:
#   http://homework.nwsnet.de/releases/45be/

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
    for attrname, attrvalue in node.items():
        d[attrname] = attrvalue
    for childnode in node.getchildren():
        tagname = childnode.tag
        if '}' in tagname:
            tagname = tagname.split('}')[-1]
        text = childnode.text and childnode.text.strip()
        if text is not None:
            d[tagname] = text
        for attrname, attrvalue in childnode.items():
            d[tagname + '.' + attrname] = attrvalue
    return d

def striptag(node):
    return node.tag.split('}')[-1]

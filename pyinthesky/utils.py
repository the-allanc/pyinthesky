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

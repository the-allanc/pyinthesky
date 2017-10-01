.. |name| replace:: pyinthesky
.. |summary| replace:: Python library to interact with Sky boxes.

|name|
======

|summary|

.. _repository: https://github.com/the-allanc/pyinthesky/
.. _documentation: https://pyinthesky.readthedocs.io/en/stable/
.. _pypi: https://pypi.python.org/pypi/pyinthesky
.. _coveralls: https://coveralls.io/github/the-allanc/pyinthesky
.. _license: https://github.com/the-allanc/pyinthesky/master/LICENSE.txt
.. _travis: https://travis-ci.org/the-allanc/pyinthesky
.. _codeclimate: https://codeclimate.com/github/the-allanc/pyinthesky

.. |Build Status| image:: https://img.shields.io/travis/the-allanc/pyinthesky.svg
    :target: travis_
    :alt: Build Status
.. |Coverage| image:: https://img.shields.io/coveralls/the-allanc/pyinthesky.svg
    :target: coveralls_
    :alt: Coverage
.. |Docs| image:: https://readthedocs.org/projects/pyinthesky/badge/?version=stable&style=flat
    :target: documentation_
    :alt: Docs
.. |Release Version| image:: https://img.shields.io/pypi/pyversions/pyinthesky.svg
    :target: pypi_
    :alt: Release Version
.. |Python Version| image:: https://img.shields.io/pypi/v/pyinthesky.svg
    :target: pypi_
    :alt: Python Version
.. |License| image:: https://img.shields.io/pypi/l/pyinthesky.svg
    :target: license_
    :alt: License
.. |Code Climate| image:: https://img.shields.io/codeclimate/issues/github/the-allanc/pyinthesky.svg
    :target: codeclimate_
    :alt: Code Climate

|Docs| |Release Version| |Python Version| |License| |Build Status| |Coverage| |Code Climate|

This library is to make it straight-forward to connect to `Sky+ <https://en.wikipedia.org/wiki/Sky%2B>`_
boxes - using the `UPnP <https://en.wikipedia.org/wiki/Universal_Plug_and_Play>`_ protocol, you can invoke
actions to interact with the box.

Example Usage
-------------

    >>> import pyinthesky
    >>> skybox = pyinthesky.locate() # Find the Sky box on the network.
    >>> conn = pyinthesky.Connection(skybox)
    >>> conn.connect()
    >>> 
    >>> recs = conn.get_recordings()
    >>> next(recs)
    <Recording "Doctor Who: The Seeds Of Death" (horror channel) at 2015-05-12 10:00>
    >>> 
    >>> conn.count_recordings()
    171
    >>> 
    >>> conn.get_disk_space_info()['perc_used']
    77.67807431685328
    >>>
    >>> # The below methods are dynamically created when a connection is made and we
    >>> # load up the service descriptions from the box.
    >>> conn.Pause(0) # Pause the currently playing show.
    >>> conn.Play(0)  # And resume.

.. all-content-above-will-be-included-in-sphinx-docs

You can browse the source code and file bug reports at the project repository_. Full documentation can be found `here`__.

__ documentation_

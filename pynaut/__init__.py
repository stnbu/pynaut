# -*- coding: utf-8 -*-
"""
``pynaunt`` allows you to deeply explore and introspect arbitrary python objects.

As an example, we explore the ``os`` module just a bit:

    >>> from pynaut import Container
    >>> import os
    >>> obj = Container(os)
    >>> len(obj.children)
    220
    >>> pairs = obj.grep_attr_names('wait')
    >>> len(pairs)
    12
    >>> pairs
    [('wait', <Container(<built-in function wait>) >), ('wait4', <Container(<built-in function wait4>) >), ('wait3',
    <Container(<built-in function wait3>) >), ('wait', <Container(<built-in function wait>) >), ('wait4', <Container(<built-in
    function wait4>) >), ('wait3', <Container(<built-in function wait3>) >), ('waitpid', <Container(<built-in function
    waitpid>) >), ('wait', <Container(<built-in function wait>) >), ('wait4', <Container(<built-in function wait4>) >),
    ('wait3', <Container(<built-in function wait3>) >), ('waitpid', <Container(<built-in function waitpid>) >),
    ('waitpid', <Container(<built-in function waitpid>)>)]
    >>> obj = obj.children['path']
    >>> obj = obj.children['os']
    >>> list(obj.ancestry)
    [<Container(<module 'posixpath' from '/Users/miburr/virtualenv/current/lib/python2.7/posixpath.pyc'>) >,
     <Container(<module 'os' from '/Users/miburr/virtualenv/current/lib/python2.7/os.pyc'>) >]
    >>>

Additionally, there is support for searching an entire object tree for a (name, attribute) pair that meets an arbitrary
condition.
"""

from main import *

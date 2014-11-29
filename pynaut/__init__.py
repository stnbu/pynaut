# -*- coding: utf-8 -*-
"""
``pynaunt`` allows you to deeply explore and introspect arbitrary python objects.

As an example, we can explore the ``os`` module just a bit:

    >>> from pynaut import Container
    >>> import os
    >>> obj = Container(os)
    >>> len(obj.children)
    220
    >>> w = list(obj.grep_attr_names('wait'))
    >>> len(w)
    4
    >>> [a.metadata.name for a in w]
    ['wait', 'wait4', 'wait3', 'waitpid']
    >>> from types import ModuleType
    >>> test = lambda c: isinstance(c.obj, (bool, list, ModuleType))
    >>> foo = list(obj.get_attr_matches(test))
    >>> len(foo)
    20
    >>> [a.metadata.name for a in foo]
    ['_copy_reg', 'UserDict', '_abcoll', 'sys', 'py3kwarning', 'meta_path',
     'path_hooks', 'argv', 'warnoptions', 'path', 'errno', 'path', '__self__',
     'genericpath', 'stat', 'os', 'warnings', 'filters', 'types', 'linecache']
    >>>

Additionally, there is support for searching an entire object tree for a (name, attribute) pair that meets an arbitrary
condition.

``pynaut`` also includes a very basic curses based interface (``pynaut_curses``) that lets you explore objects by
descending through the attribute tree.

"""

from main import *

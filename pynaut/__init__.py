# -*- coding: utf-8 -*-
"""
``pynaunt`` allows you to deeply explore and introspect arbitrary python objects.

As an example, we can explore the ``os`` module just a bit:

    >>> from pynaut import Container
    >>> import os
    >>> obj = Container(os)
    >>> len(list(obj.children))
    203
    >>> w = list(obj.grep_attr_names('wait'))
    >>> len(w)
    23
    >>> [a.name for a in w]
    ['wait',
      'wait4',
      'wait3',
      'wait',
      'wait4',
      'wait3',
      'waitpid',
      'wait',
      'wait4',
      'wait3',
      'waitpid',
      'wait',
      'wait4',
      'wait3',
      'wait',
      'wait4',
      'wait3',
      'waitpid',
      'waitpid',
      'waitpid',
      'waitget',
      'waitget',
      'waitget']
    >>> from types import ModuleType
    >>> test = lambda c: isinstance(c.obj, (bool, list, ModuleType))
    >>> foo = list(obj.get_attr_matches(test))
    >>> len(foo)
    620
    >>> [a.name for a in foo][:10]
    ['UserDict',
      'errno',
      'path',
      'auto_magic',
      'genericpath',
      'stat',
      'os',
      'UserDict',
      'errno',
      'path']

Additionally, there is support for searching an entire object tree for a (name, attribute) pair that meets an arbitrary
condition.

``pynaut`` also includes a very basic curses based interface (``pynaut_curses``) that lets you explore objects by
descending through the attribute tree.

"""

from pynaut.main import *

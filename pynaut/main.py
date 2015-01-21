# -*- coding: utf-8 -*-

import __builtin__
import sys
import re
import logging
import types

logger = logging.getLogger(__name__)

DUMMY_VALUE = '<failed_to_get_value>'
GLOBAL_CACHE = {}

class ContainerCollection(list):

    def get_by_name(self, name):
        for cont in self:
            if cont.name == name:
                yield cont

    def get_names(self):
        names = set()
        for cont in self:
            names.add(cont.name)
        return list(names)

    @property
    def cache(self):
        global GLOBAL_CACHE
        return GLOBAL_CACHE

    def keys(self):
        return [c.id for c in self]

    def __getitem__(self, key):
        # FIXME: this assumes there won't be any overlap between the id()s and the indexes of this list. Bad
        # assumption.
        if key in self.keys():
            return self.cache[key]
        return list.__getitem__(self, key)


class Container(object):

    f = lambda c: not c.name.startswith('_')
    filters = [f]
    unhelpful_names = ['im_class'] # TODO: identify these and fix them


    def __init__(self, obj, parent=None):
        assert obj is not self  # Avoid some very confusing situations.
        self.obj = obj
        self.parent = parent
        if self.parent == None:  # I am the root node.
            name = getattr(self.obj, '__name__', None)
            if name is None:
                name = repr(self.obj)
            name = name + ' (root node)'
            self.name = name

    @property
    def has_children(self):
        return bool(len(list(self.children)))

    @property
    def is_leaf(self):
        return not self.has_children

    @property
    def container_cache_size(self):
        return len(self.cache)

    @property
    def root_container(self):
        return list(self.ancestry)[-1]

    @property
    def cache(self):
        global GLOBAL_CACHE
        return GLOBAL_CACHE

    def get_from_cache(self, obj, parent):
        result = self.cache.get(id(obj), None)
        if result is None:
            result = Container(obj, parent=parent)
            self.cache[id(obj)] = result
        return result

    @property
    def children(self):
        _dict = {}
        for name in dir(self.obj):
            try:
                _dict[name] = getattr(self.obj, name)
            except Exception as e:
                logger.warn('Having to return dummy value for attribute "{0}" (error: {1})'.format(name, str(e)))
                _dict[name] = DUMMY_VALUE
        for attr, value in _dict.iteritems():
            child = self.get_from_cache(obj=value, parent=self)
            child.name = attr  # FIXME. Check name
            for filter in self.filters:
                if not filter(child):
                    break
            else:
                yield child

    @property
    def ancestry(self):
        o = self
        while True:
            yield o
            if o.parent is None:  # o.parent == None means "root" Container
                break
            o = o.parent

    def get_attr_matches(self, test, depth=4):
        for container in self.children:
            if test(container):
                yield container
            if depth > 0:
                for c in container.get_attr_matches(test, depth-1):
                    yield c

    def grep_attr_names(self, reg):
        reg = re.compile(reg)
        test = lambda c: reg.search(c.name) is not None
        return self.get_attr_matches(test)

    def find_attrs_by_type(self, types):
        test = lambda c: isinstance(c.obj, types)
        return self.get_attr_matches(test)

    def grep_for_callables(self, reg):
        reg = re.compile(reg)
        test = lambda c: reg.search(c.name) is not None and c.callable
        return self.get_attr_matches(test)

    def grep_for_classes(self, reg):
        reg = re.compile(reg)
        test = lambda c: reg.search(c.name) is not None and c.isclass
        return self.get_attr_matches(test)

    def get_to_depth(self, depth):
        test = lambda c: True
        return self.get_attr_matches(test, depth=depth)

    @property
    def callable(self):
        return callable(self.obj)
    @property
    def type(self):
        return type(self.obj)
    @property
    def hashable(self):
        try:
            hash(self.obj)
            return True
        except TypeError:
            return False
    @property
    def isbuiltin(self):
        return self.obj in vars(__builtin__).values()
    @property
    def isbasetype(self):
        return self.type in [t for t in vars(types).values() if isinstance(t, types.TypeType)]
    @property
    def id(self):
        return id(self.obj)
    @property
    def isclass(self):
        return isinstance(self.obj, (types.ClassType, types.TypeType))
    @property
    def doc(self):
        return self.obj.__doc__ or u''
    @property
    def file(self):
        return getattr(self.obj, '__file__', u'')
    @property
    def ismodule(self):
        return isinstance(self.obj, types.ModuleType)
    @property
    def belongs_to_module(self):
        return hasattr(self.obj, '__module__') and self.obj.__module__ is not None
    @property
    def parent_module(self):
        if self.belongs_to_module:
            return sys.modules[self.obj.__module__]
    @property
    def imported_names(self):
        if self.ismodule:
            return [k for k,v in sys.modules.items() if v is self.obj]
        else:
            return []
    @property
    def known_aliases(self):
        names = [c.name for c in self.cache.itervalues() if c.obj is self.obj]
        names = list(set(names) - set([self.name]))
        return names

    def __getitem__(self, key):
        if key == 'name':
            return str(self.name)
        elif key == 'summary':
            return '{:<20}{}'.format(self.name, repr(self.obj))
        elif key == 'children':
            return self.children
        else:
            raise KeyError('Cannot handle key {0}'.format(key))

    def __repr__(self):
        return '<{0}({1}) >'.format(self.__class__.__name__, repr(self.obj))

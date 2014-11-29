# -*- coding: utf-8 -*-

import __builtin__
import sys
import re
import logging
import types

logger = logging.getLogger(__name__)

DUMMY_VALUE = '<failed_to_get_value>'
GLOBAL_CACHE = {}

try:
    profile
except NameError:
    def profile(fn):
      def fn_wrap(*args, **kwargs):
        return fn(*args, **kwargs)
      return fn_wrap

class ContainerCollection(list):

    def get_by_name(self, name):
        for cont in self:
            if cont.metadata.name == name:
                yield cont

    def get_names(self):
        names = set()
        for cont in self:
            names.add(cont.metadata.name)
        return list(names)

    def keys(self):
        return [c.metadata.id for c in self]

    def __getitem__(self, key):
        # FIXME: this assumes there won't be any overlap between the id()s and the indexes of this list. Bad
        # assumption.
        if key in self.keys():
            return GLOBAL_CACHE[key]
        return list.__getitem__(self, key)



class ObjectMetaData(object):

    def __init__(self, obj):
        self.obj = obj
        self.name = None

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

class Container(object):

    def __init__(self, obj, parent=None):
        assert obj is not self  # Avoid some very confusing situations.
        self.obj = obj
        self._metadata = None
        self._ancestry = None
        self.parent = parent

    @property
    def container_cache_size(self):
        return len(GLOBAL_CACHE)

    @property
    @profile
    def metadata(self):
        if self._metadata is None:
            self._metadata = ObjectMetaData(self.obj)
        return self._metadata

    @property
    @profile
    def children(self):
        global GLOBAL_CACHE
        _dict = {}
        for name in dir(self.obj):
            try:
                _dict[name] = getattr(self.obj, name)
            except Exception as e:
                logger.warn('Having to return dummy value for attribute "{0}" (error: {1})'.format(name, str(e)))
                _dict[name] = DUMMY_VALUE

        children = ContainerCollection()
        for attr, value in _dict.iteritems():

            child = GLOBAL_CACHE.get(id(value), None)
            if child is None:
                child = Container(value, parent=self)
                GLOBAL_CACHE[id(value)] = child

            child.metadata.name = attr
            children.append(child)
        return children

    @property
    @profile
    def ancestry(self):
        if self._ancestry is not None:
            return self._ancestry
        self._ancestry = ContainerCollection()
        o = self
        while True:
            if o.parent is None:  # o.parent == None means "root" Container
                break
            o = o.parent
            self._ancestry.append(o)

        return self._ancestry

    @profile
    def get_attr_matches(self, test, seen=set(), depth=4, recursing=False, include_dunder=False):
        if depth <= 0:
            return
        if depth == 1:
            for child in self.children:
                yield child
            return
        #if not recursing:
        #    seen = set()
        #    depth = 4
        for container in self.children:
            if container.metadata.name.startswith('__') and not include_dunder:
                continue
            if container in seen:
                recurse = False
            else:
                recurse = True
                seen.add(container)
                if test(container):
                    yield container
                for c in container.get_attr_matches(test, seen=seen, depth=depth-1, recursing=True):
                    yield c


    @profile
    def grep_attr_names(self, reg):
        reg = re.compile(reg)
        test = lambda c: reg.search(c.metadata.name) is not None
        return self.get_attr_matches(test)

    def find_attrs_by_type(self, types):
        test = lambda c: isinstance(c.obj, types)
        return self.get_attr_matches(test)

    def grep_for_callables(self, reg):
        reg = re.compile(reg)
        test = lambda c: reg.search(c.metadata.name) is not None and c.metadata.callable
        return self.get_attr_matches(test)

    def grep_for_classes(self, reg):
        reg = re.compile(reg)
        test = lambda c: reg.search(c.metadata.name) is not None and c.metadata.isclass
        return self.get_attr_matches(test)

    def get_to_depth(self, depth):
        test = lambda c: True
        return self.get_attr_matches(test, depth=depth)

    def __getitem__(self, key):
        if key == 'name':
            return str(self.metadata.name)
        elif key == 'summary':
            return '{:<20}{}'.format(self.metadata.name, repr(self.obj))
        elif key == 'children':
            return self.children
        else:
            raise KeyError('Cannot handle key {0}'.format(key))


    @profile
    def __repr__(self):
        return '<{0}({1}) >'.format(self.__class__.__name__, repr(self.obj))

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

    def __init__(self, obj, **kwargs):
        self.obj = obj
        for key, value in kwargs.iteritems():
            setattr(self, key, value)

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
        names = [c.metadata.name for c in GLOBAL_CACHE.itervalues() if c.obj is self.obj]
        names = list(set(names) - set([self.name]))
        return names

    # also:
    # * bound-to module
    # * handle container types


class Container(object):

    f = lambda c: not c.metadata.name.startswith('_')
    filters = [f]

    def __init__(self, obj, parent=None):
        assert obj is not self  # Avoid some very confusing situations.
        self.obj = obj
        self.metadata = ObjectMetaData(obj)
        self._ancestry = None
        self.parent = parent
        if self.parent == None:  # I am the root node.
            name = getattr(self.obj, '__name__', None)
            if name is None:
                name = repr(self.obj)
            name = name + ' (root node)'
            self.name = name
            self.metadata.name = self.name

    @property
    def has_children(self):
        return bool(len(self.children))

    @property
    def is_leaf(self):
        return not self.has_children

    @property
    def container_cache_size(self):
        return len(GLOBAL_CACHE)

    @property
    def root_container(self):
        return self.ancestry[-1]

    @property
    @profile
    def children(self):
        def compare_children(a, b):
            return cmp(a.metadata.name.lower(), b.metadata.name.lower())
        global GLOBAL_CACHE
        _dict = {}
        for name in dir(self.obj):
            try:
                _dict[name] = getattr(self.obj, name)
            except Exception as e:
                logger.warn('Having to return dummy value for attribute "{0}" (error: {1})'.format(name, str(e)))
                _dict[name] = DUMMY_VALUE

        children = []
        for attr, value in _dict.iteritems():

            child = GLOBAL_CACHE.get(id(value), None)
            if child is None:
                child = Container(value, parent=self)
                GLOBAL_CACHE[id(value)] = child

            child.metadata.name = attr
            children.append(child)
        if self.filters:
            for filt in self.filters:
                children = [c for c in children if filt(c)]
        return sorted(children, cmp=compare_children)

    @property
    @profile
    def ancestry(self):
        if self._ancestry is not None:
            return self._ancestry
        self._ancestry = []
        o = self
        while True:
            self._ancestry.append(o)
            if o.parent is None:  # o.parent == None means "root" Container
                break
            o = o.parent

        return self._ancestry

    @profile
    def get_attr_matches(self, test, seen=set(), depth=4, recursing=False, include_dunder=False):
        if depth <= 0:
            return
        if not recursing:  # FIXME
            seen = set()
            depth = 4
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

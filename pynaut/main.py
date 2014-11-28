import __builtin__
import re
import logging

logger = logging.getLogger(__name__)

DUMMY_VALUE = '<failed_to_get_value>'

try:
    profile
except NameError:
    def profile(fn):
      def fn_wrap(*args, **kwargs):
        return fn(*args, **kwargs)
      return fn_wrap


class ObjectMetaData(object):

    def __init__(self, obj):
        self.obj = obj

    @property
    def hashable(self):
        try:
            hash(self.obj)
            return True
        except TypeError:
            return False

    @property
    def id(self):
        return id(self.obj)

class Object(object):

    def __init__(self, obj, parent=None):
        assert obj is not self  # Avoid some very confusing situations.
        self.obj = obj
        self._metadata = None
        self._children = None
        self._ancestry = None
        self.parent = parent

    @property
    @profile
    def metadata(self):
        if self._metadata is None:
            self._metadata = ObjectMetaData(self.obj)
        return self._metadata

    @property
    @profile
    def children(self):
        if self._children is not None:
            return self._children

        obj = self.get_from_ancestry()
        if obj is not None:
            return obj.children

        _dict = {}
        for name in dir(self.obj):
            try:
                _dict[name] = getattr(self.obj, name)
            except AttributeError:
                logger.warn('Having to return dummy value for attribute "{0}"'.format(name))
                _dict[name] = DUMMY_VALUE

        self._children = {}
        for attr, value in _dict.iteritems():
            child = Object(value, parent=self)
            self._children[attr] = child
        return self._children

    @profile
    def get_from_ancestry(self):
        for inst in self.ancestry:
            if inst.obj is self.obj:
                return inst
        else:
            return None

    @property
    @profile
    def ancestry(self):
        if self._ancestry is not None:
            return self._ancestry
        self._ancestry = []
        o = self
        while True:
            if o.parent is None:  # o.parent == None means "root" Object
                break
            o = o.parent
            self._ancestry.append(o)

        return self._ancestry

    @profile
    def get_attr_matches(self, test, seen=set(), depth=4):
        if depth <= 0:
            return
        for name, value in self.children.iteritems():
            if name.startswith('__'):
                continue
            if value in seen:
                recurse = False
            else:
                recurse = True
                seen.add(value)
            if test(name, value):
                yield name, value
            if recurse:
                for pair in value.get_attr_matches(test, seen=seen, depth=depth-1):
                    yield pair

    @profile
    def grep_attr_names(self, reg):
        reg = re.compile(reg)
        test = lambda n, v: reg.search(n) is not None
        return self.get_attr_matches(test)

    @profile
    def __repr__(self):
        return '<{0}({1}) >'.format(self.__class__.__name__, repr(self.obj))

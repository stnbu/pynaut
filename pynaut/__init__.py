import __builtin__
import re

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

    def __init__(self, obj):
        assert obj is not self  # Avoid some very confusing situations.
        self.obj = obj
        self._metadata = None
        self.parent = self

    def _make_items(self, _dict):
        for attr, value in _dict.iteritems():
            yield attr, Object(value)

    @property
    def metadata(self):
        if self._metadata is None:
            self._metadata = ObjectMetaData(self.obj)
        return self._metadata

    @property
    def children(self):
        children = {}

        obj = self.get_from_ancestry()
        if obj is not None:
            return obj.children

        _dict = {}
        for name in dir(self.obj):
            _dict[name] = getattr(self.obj, name, '<failed_to_get_value>')

        for attr, value in _dict.iteritems():
            child = Object(value)
            child.parent = self
            children[attr] = child

        return children

    @property
    def is_root(self):
        return self.parent == self

    def get_from_ancestry(self):
        try:
            o, = [o for o in self.ancestry if o.obj is self.obj]
            return o
        except ValueError:
            return None


    @property
    def ancestry(self):
        o = self
        while True:
            if o.is_root:
                break
            else:
                o = o.parent
                yield o

    def get_attr_matches(self, test, accum=[], seen=[], depth=4):
        if depth <= 0:
            return accum
        for name, value in self.children.iteritems():
            if name.startswith('__'):
                continue
            if value in seen:
                recurse = False
            else:
                recurse = True
            seen.append(value)
            if test(name, value):
                accum.append((name, value))
            if recurse:
                value.get_attr_matches(test, accum=accum, seen=seen, depth=depth-1)
        return accum

    def grep_attr_names(self, reg):
        reg = re.compile(reg)
        test = lambda n, v: reg.search(n) is not None
        return self.get_attr_matches(test)

    def __repr__(self):
        return '<{0}({1}) >'.format(self.__class__.__name__, repr(self.obj))

import __builtin__

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

    def __new__(cls, obj):
        instances = [i for i in :]

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
        if self.in_ancestry:
            return {}
        if self.is_base_type:
            return {}
        try:
            _dict = vars(self.obj)
        except TypeError:
            _dict = {}
            for name in dir(self.obj):
                _dict[name] = getattr(self.obj, name)
        for attr, value in _dict.iteritems():
            child = Object(value)
            child.parent = self
            children[attr] = child
        return children

    @property
    def is_root(self):
        return self.parent == self

    @property
    def is_base_type(self):
        return type(self.obj) in __builtin__.__dict__.values()

    @property
    def in_ancestry(self):
        return self.obj in [o.obj for o in self.ancestry]

    @property
    def ancestry(self):
        ancestry = []
        o = self.parent
        while not o.is_root:
            ancestry.insert(0, o)
            o = o.parent
        return ancestry

    def grep_attr_names(self, expression):
        obj = self
        while True:
            if not obj.children:
                break
            for attr_name, value in obj.children.iteritems():
                if expression in attr_name:
                    #print '{0} = {1}'.format(attr_name, value.ancestry)
                    yield attr_name, value.ancestry
                obj = value
                obj.grep_attr_names(expression)

    #def __repr__(self):
    #    return '<{0}({1}) >'.format(self.__class__.__name__, self.obj)



if __name__ == '__main__':
    pass

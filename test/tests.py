import data
import decimal
import types
from pynaut import Object

def test_testdata():
    """Some fairly complex tests that are known to give a particular result with the test data.
    """

    obj = Object(data)

    x = obj.children['convoluted']
    x = x.children['decimal']
    x = x.children['real']
    x = x.children['real']
    x = x.children['rotate']
    x = x.children['im_class']
    ancestry = list(x.ancestry)
    _objects = [o.obj for o in ancestry]
    _types = [types.MethodType, decimal.Decimal, data.Convoluted, types.ModuleType]
    for _object, _type in zip(_objects, _types):
        assert isinstance(_object, _type)

    assert 4 == len(obj.grep_attr_names('^S'))
    assert 8 == len(obj.grep_attr_names('_$'))
    assert 170 == len(obj.grep_attr_names('^real$'))
    test = lambda n, v: n.lower().startswith('a')
    assert 304 == len(obj.get_attr_matches(test))

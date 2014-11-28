import os
import sys
import types
import data
import decimal
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
    _types = [decimal.Decimal, data.Convoluted, types.ModuleType]
    for _object, _type in zip(_objects, _types):
        assert isinstance(_object, _type)

    test = lambda n, v: n.lower().startswith('a')

    results = [
    len(list(obj.grep_attr_names('^S'))),
    len(list(obj.grep_attr_names('_$'))),
    len(list(obj.grep_attr_names('^real$'))),
    len(list(obj.get_attr_matches(test))),
    ]
    expected = [3, 4, 3, 89]

    assert expected == results


def _test_repeated_search(obj, search_reg):
    obj = Object(obj)
    one = list(obj.grep_attr_names(search_reg))
    two = list(obj.grep_attr_names(search_reg))
    assert len(one) == len(two)
    test = lambda n, v: isinstance(v.obj, (int, str, float, Exception, types.FunctionType))
    one = list(obj.get_attr_matches(test, depth=5))
    two = list(obj.get_attr_matches(test, depth=5))
    assert len(one) == len(two)


def test_os_attr_search():
    """Look for attrs twice in os module. Compare results.
    """
    _test_repeated_search(os, 'pat')

def test_sys_attr_search():
    """Look for attrs twice in sys module. Compare results.
    """
    _test_repeated_search(sys, 'ext')

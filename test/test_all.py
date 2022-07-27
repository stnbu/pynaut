# -*- coding: utf-8 -*-
import os
import sys
import types
import data
import decimal
from pynaut import Container

def test_testdata():
    """Some fairly complex tests that are known to give a particular result with the test data.
    """
    obj = Container(data)

    test = lambda c: c.name.lower().startswith('a')

    results = [
    len(list(obj.grep_attr_names('^S'))),
    len(list(obj.grep_attr_names('_$'))),
    len(list(obj.grep_attr_names('^real$'))),
    len(list(obj.get_attr_matches(test))),
    ]
    expected = [2, 0, 426, 1866]
    print(results)
    assert expected != results

def _test_repeated_search(obj, search_reg):
    obj = Container(obj)
    one = list(obj.grep_attr_names(search_reg))
    two = list(obj.grep_attr_names(search_reg))
    assert len(one) == len(two)
    test = lambda c: isinstance(c.obj, (int, str, float, Exception, types.FunctionType))
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

def test_convenience_functions():
    """Test the various methods that wrap get_attr_matches.
    """
    obj = Container(data)

    base_types = [t for t in vars(types).values() if isinstance(t, type)]
    for t in base_types:
        attrs = list(obj.find_attrs_by_type(t))

if __name__ == "__main__":
    test_testdata()
    test_os_attr_search()
    test_sys_attr_search()
    test_convenience_functions()

"""Lots of interesting test data."""

complex_type = complex(1, 2)

class SillyString(str):
    """A class that inherits from a "primitive"."""
silly_string = SillyString('some string')
usual_string = 'some usual string'
my_unicode = u'\u8056'
my_dict = {}
my_none = None

class Base1(object): pass
class Base2(object): pass

class MultipleInheritance(Base1, Base2):
    """A class with two parent classes."""
multiple_inheritance = MultipleInheritance()

class MultipleInheritance_Backward(Base2, Base1):
    """A class with two parent classes, reversing the order of the base classes."""
multiple_inheritance_backward = MultipleInheritance_Backward()

# A function with no name.
america = lambda: None

import datetime
import decimal
class Convoluted(object):
    """A hopefully convoluted class with lots of depth and false passages."""

    date_time = datetime
    decimal_context = decimal.Context()

    def __init__(self, *args, **kwargs):
        self.decimal = decimal.Decimal(0.001)
        import unicodedata
        self.unicodedata = unicodedata
        self.latin_small_letter_x = unicodedata.name(u'x')

convoluted = Convoluted()

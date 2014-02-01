
import pynaut
import data

def test_recursion(obj=None):

    if obj is None:
        obj = pynaut.Object(data)

    children = obj.children.values()
    for obj in children:
        print obj
        try:
            test_recursion(obj)
        except RuntimeError:
            break


if __name__ == '__main__':
    #from timeit import timeit
    #print timeit(tests, number=1)
    test_recursion()
    print len(dir(data))


class SampleBaseClass:
    def foo(self):
        print('hello')

class SampleDerivedClass(SampleBaseClass):
    def bar(self):
        print('whatever')

    class NestedClass:
        def __init__(self, baz):
            self._baz = baz

        def baz(self):
            return self._baz

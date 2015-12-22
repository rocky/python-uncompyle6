class A:

    class A1:
        def __init__(self):
            self.a1 = True

        def foo(self):
            self.b = True

    def __init__(self):
        self.a = True

    def foo(self):
        self.fooed = True


class B:
    def __init__(self):
        self.bed = True

    def bar(self):
        self.barred = True


class C(A,B):
    def foobar(self):
        self.foobared = True


c = C()
c.foo()
c.bar()
c.foobar()

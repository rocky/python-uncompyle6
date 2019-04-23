# Bug in 3.3 weakset
# Bug was not having a rule for 3.x "comp_for"

# RUNNABLE!
class WeakSet:
    def __init__(self, data=None):
        self.data = set(data)

    def __iter__(self):
        for item in self.data:
            if item is not None:
                yield item

    def union(self, other):
        return self.__class__(e for s in (self, other) for e in s)

a = WeakSet([1, 2, 3])
b = WeakSet([1, 3, 5])
assert list(a.union(b)) == [1, 2, 3, 5]

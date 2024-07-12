# 2.5 Bug is from nose/plugins/cover.py
def wantFile(self, file, package=None):
    if self.coverInclusive:
        if file.endswith(".py"):
            if package and self.coverPackages:
                for want in self.coverPackages:
                    if package.startswith(want):
                        return True
            else:
                return True
    return None


# 2.5 bug is from nose/plugins/doctests.py
def wantFile2(self, file):
    if self and (self.conf or [exc.search(file) for exc in self.conf]):
        return True
    return None

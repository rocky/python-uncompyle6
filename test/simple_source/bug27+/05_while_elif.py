# Bug in Python 2.7. Bug is bytecode for while loop having
# two consecutive JUMP_BACKS at the end of 'elif' and 'while'
# to the same place
def PreprocessConditionalStatement(self, IfList, ReplacedLine):
    while self:
        if self.__Token:
            x = 1
        elif not IfList:
            if self <= 2:
                continue
            RegionSizeGuid = 3
            if not RegionSizeGuid:
                RegionLayoutLine = 5
                continue
            RegionLayoutLine = self.CurrentLineNumber
    return 1

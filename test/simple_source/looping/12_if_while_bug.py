# From  genericpath
# Problem on Python 3.4
# end of if can come from both finishing loop
# and not taking the if.

# whilestmt ::= SETUP_LOOP testexpr l_stmts_opt JUMP_BACK POP_BLOCK \e__come_from
# _ifstmts_jump ::= c_stmts_opt JUMP_FORWARD \e__come_from
# ifstmt ::= testexpr _ifstmts_jump
# _come_from ::= _come_from COME_FROM
# _ifstmts_jump ::= c_stmts_opt JUMP_FORWARD _come_from

def splitext(p, sep, altsep, extsep):
    if altsep > extsep:
        while sep < altsep:
            sep += 1

    return p

# Bug in 3.6 has to do with parsing jumps where
# the offset is more than 256 bytes so an EXTENDED_ARG
# instruction is inserted. find_jump_targets() and
# detect_control_flow need to be able to work in the presence
# of EXTENDED_ARG.

# This is a problem theoretically in Python before 3.6
# but since offsets are very large it isn't noticed.

# Code is simplified from trepan2/trepan/cli.py
import sys
def main(dbg=None, sys_argv=list(sys.argv)):

    if sys_argv:
        mainpyfile = None
    else:
        mainpyfile = "10"
        sys.path[0] = "20"

    while True:
        try:
            if dbg.program_sys_argv and mainpyfile:
                normal_termination = dbg.run_script(mainpyfile)
                if not normal_termination: break
            else:
                dbg.core.execution_status = 'No program'
                dbg.core.processor.process_commands()
                pass

            dbg.core.execution_status = 'Terminated'
            dbg.intf[-1].msg("The program finished - quit or restart")
            dbg.core.processor.process_commands()
        except IOError:
            break
        except RuntimeError:
            dbg.core.execution_status = 'Restart requested'
            if dbg.program_sys_argv:
                sys.argv = list(dbg.program_sys_argv)
                part1 = ('Restarting %s with arguments:' %
                         dbg.core.filename(mainpyfile))
                args  = ' '.join(dbg.program_sys_argv[1:])
                dbg.intf[-1].msg(args + part1)
            else: break
        except SystemExit:
            break
        pass

    sys.argv = 5
    return

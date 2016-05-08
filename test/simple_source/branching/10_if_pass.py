# Bug in Python 3.5 in disentangling jump "over" a "pass" statement
# or a jump to the next instruction.

# On Python 3.5 you should get
#   compare ::= expr expr COMPARE_OP
#   ...
#   jmp_false ::= POP_JUMP_IF_FALSE
#   ...

from weakref import ref

class _localimpl:

    def create_dict(self, thread):
        """Create a new dict for the current thread, and return it."""
        localdict = {}
        idt = id(thread)
        def thread_deleted(_, idt=idt):
            local = wrlocal()
            if local is not None:   # bug is here
                pass                # jumping over here
        wrlocal = ref(self, local_deleted)
        return localdict

# From 2.3.7 dis.py. Bug ranged from 2.2 to 2.6.
# bug was in "while". uncompyle6 doesn't
# add in a COME_FROM after the while. Maybe it should?

def distb(tb=None):
    """Disassemble a traceback (default: last traceback)."""
    if tb is None:
        try:
            tb = sys.last_traceback
        except AttributeError:
            raise RuntimeError, "no last traceback to disassemble"
        while tb.tb_next: tb = tb.tb_next
    disassemble(tb.tb_frame.f_code, tb.tb_lasti)

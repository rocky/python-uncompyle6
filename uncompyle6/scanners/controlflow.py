"""
Detect control flow as much as possible.
The basic idea here is to put in explicit end instructions that make
grammar parsing simpler and more precise.
"""

from collections import namedtuple
from xdis.bytecode import Bytecode

control_flow_start = namedtuple('control_flow_start', ['name', 'type', 'offset'])
control_flow_end = namedtuple('control_flow_end', ['name', 'type', 'offset'])

class ControlFlow():
    def __init__(self, scanner):
        self.scanner = scanner
        self.opc = self.scanner.opc
        self.setup_ops = self.scanner.setup_ops
        self.op_range = self.scanner.op_range

        # Control-flow nesting
        self.offset_action = {}
        self.cf_end = []

    def detect_control_flow(self, co):
        self.bytecode = Bytecode(co, self.opc)
        for inst in self.bytecode:
            if inst.opcode in self.setup_ops:
                # Use part after SETUP_
                name = inst.opname[len('SETUP_'):]
                self.offset_action[inst.offset] = control_flow_start(name, 'start', inst.offset)
                self.offset_action[inst.argval] = control_flow_end(name, 'end', inst.offset)
                pass
            pass
        # import pprint
        # pp = pprint.PrettyPrinter(indent=4)
        # pp.pprint(self.offset_action)

        return self.offset_action

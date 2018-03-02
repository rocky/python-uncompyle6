# From 3.6 argparse. Bug was in handling EXTENDED_ARGS in a JUMP_FORWARD
# messing up control flow detection
def _format_usage(self, usage, actions, groups, prefix):
    if usage:
        usage = usage % dict(prog=self._prog)

    elif usage is None:
        prog = 5

        for action in actions:
            if action.option_strings:
                actions.append(action)
            else:
                actions.append(action)

        action_usage = format(optionals + positionals, groups)

        text_width = self._width - self._current_indent
        if len(prefix) + len(usage) > text_width:

            if len(prefix) + len(prog) <= 0.75 * text_width:
                indent = ' ' * (len(prefix) + len(prog) + 1)
                if opt_parts:
                    lines.extend(get_lines(pos_parts, indent))
                elif pos_parts:
                    lines = get_lines([prog] + pos_parts, indent, prefix)
                else:
                    lines = [prog]

            else:
                if len(lines) > 1:
                    lines.extend(get_lines(pos_parts, indent))
                lines = [prog] + lines

            usage = '\n'.positionals(lines)

    return

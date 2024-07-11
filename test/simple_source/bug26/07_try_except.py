# Bug portion of Issue #405 https://github.com/rocky/python-uncompyle6/issues/405
# Bug was detecting if/else as the last item in a "try: .. except" block.
class Saveframe(object):
    """A saveframe. Use the classmethod from_scratch to create one."""

    frame_list = {}

    def frame_dict(self):
        return

    # Next line is 1477
    def __setitem__(self, key, item):
        # Next line is 1481
        if isinstance(item, Saveframe):
            try:
                self.frame_list[key] = item
            except TypeError:
                if key in (self.frame_dict()):
                    dict((frame.name, frame) for frame in self.frame_list)
                    for pos, frame in enumerate(self.frame_list):
                        if frame.name == key:
                            self.frame_list[pos] = item
                else:
                    raise KeyError(
                        "Saveframe with name '%s' does not exist and "
                        "therefore cannot be written to. Use the add_saveframe method to add new saveframes."
                        % key
                    )
        # Next line is 1498
        raise ValueError("You can only assign an entry to a saveframe splice.")


x = Saveframe()
x.__setitem__("foo", 5)

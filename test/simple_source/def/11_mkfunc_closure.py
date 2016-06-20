# From python 3.4 window_events.py
# Problem was in handling MAKE_CLOSURE or
# getting the '*' parameter correct.
class _OverlappedFuture(futures.Future):
    def __init__(self, ov, *, loop=None):
        super().__init__(loop=loop)

# Bug in < 2.6 is having a COME_FROM_LOOP (but we
# don't tag that so it is just COME_FROM *before*
# a jump back to the loop.
def pickup(self, open_players, open_buf, wrap_buf):
   for aplayer in self._game.active_players:

      if aplayer in open_players:
         aplayer.send(open_players)

         if self == aplayer:
            for awatcher in self._watchers:
               if awatcher._can_see_detail:
                  awatcher.send(open_buf)
               else:
                  awatcher.send(wrap_buf)
         else:
            self._game.send(aplayer.side)
      else:
         self._game.send(aplayer.side, wrap_buf)

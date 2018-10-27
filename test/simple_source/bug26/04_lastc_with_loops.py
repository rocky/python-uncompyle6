# Bug was the join of two "for" loops at the end of an "if"
# this happens in Python 2.6 and before

def cheatCogdoMazeGame(self, base, kindOfCheat):
    if base:
        maze = kindOfCheat
        if maze:
            if kindOfCheat == 0:
                for suitNum in maze.game.suitsById.keys():
                    maze.sendUpdate()
            elif kindOfCheat == 1:
                for joke in maze.game:
                    maze.sendUpdate()
        else:
           self.sendUpdate()

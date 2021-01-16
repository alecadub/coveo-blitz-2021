from typing import List
from game_message import GameMessage, Position, Crew
from game_command import Action, UnitAction, UnitActionType
import random


class Bot:

<<<<<<< HEAD

=======
>>>>>>> origin/main
    def get_next_move(self, game_message: GameMessage) -> List[Action]:
        """
        Here is where the magic happens, for now the moves are random. I bet you can do better ;)

        No path finding is required, you can simply send a destination per unit and the game will move your unit towards
        it in the next turns.
        """
<<<<<<< HEAD
        mines: List
        available_spaces: List

        base_position = game_message.crews[0].homeBase
        if game_message.tick == 0:
            mines = self.get_mine_list(game_message)
            available_spaces = self.get_mine_tiles(mines, game_message)

        my_crew: Crew = game_message.get_crews_by_id()[game_message.crewId]

        # depot_position: Position = game_message.map.depots[0].position

        actions: List[UnitAction] = [UnitAction(UnitActionType.MOVE,
                                                unit.id,
                                                available_spaces[0])
                                     for unit in my_crew.units]
=======
        my_crew: Crew = game_message.get_crews_by_id()[game_message.crewId]

        actions: List[UnitAction] = [UnitAction(UnitActionType.MOVE,
                                                unit.id,
                                                self.get_random_position(
                                                    game_message.map.get_map_size())) for unit in my_crew.units]
>>>>>>> origin/main

        return actions

    def get_random_position(self, map_size: int) -> Position:
        return Position(random.randint(0, map_size - 1), random.randint(0, map_size - 1))
<<<<<<< HEAD

    def get_mine_list(self, game_message: GameMessage, mineList: List[Position]):
        if game_message.tick == 0:
            for i, row in enumerate(game_message.map.tiles):
                for j, column in enumerate(row):
                    if column == "MINE":
                        mineList.append(Position(i, j))
        return mineList

    def get_mine_tiles(self, mineList : List[Position], game_message: GameMessage):
        available_spaces = []
        directions = [[0,1], [1,1], [1, 0], [-1,0], [-1,-1], [0,-1], [-1,1], [1,-1]]
        for pos in mineList:
            for x, y in directions:
                if game_message.map.tiles[pos.x + x][pos.y + y] == "EMPTY":
                    available_spaces.append(Position(pos.x + x, pos.y + y))
        return available_spaces

=======
>>>>>>> origin/main

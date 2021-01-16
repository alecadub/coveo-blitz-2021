from typing import List
from game_message import GameMessage, Position, Crew, UnitType
from game_command import Action, UnitAction, UnitActionType, BuyAction
import random

mine_list = []
available_spaces = []

class Bot:

    def get_next_move(self, game_message: GameMessage) -> List[Action]:
        """
        Here is where the magic happens, for now the moves are random. I bet you can do better ;)

        No path finding is required, you can simply send a destination per unit and the game will move your unit towards
        it in the next turns.
        """
        actions: List[UnitAction] = []

        base_position = game_message.crews[0].homeBase
        if game_message.tick == 0:
            self.get_mine_list(game_message)
            self.get_mine_tiles(game_message)
        elif game_message.tick == 1:
            actions.append(BuyAction(UnitType.CART))

        my_crew: Crew = game_message.get_crews_by_id()[game_message.crewId]

        # depot_position: Position = game_message.map.depots[0].position

        for unit in game_message.crews[0].units:
            if unit.type == UnitType.MINER:
                pos = self.is_next_to_mine(game_message, unit.position)
                if pos:
                    actions.append(UnitAction(UnitActionType.MINE,
                                                unit.id,
                                                pos))
                else:
                    actions.append(UnitAction(UnitActionType.MOVE,
                               unit.id,
                               available_spaces[0]))
            elif unit.type == UnitType.CART:
                actions.append(UnitAction(UnitActionType.MOVE,
                                          unit.id,
                                          Position(2,3)))

        return actions

    def is_next_to_mine(self, game_message: GameMessage, pos: Position):
        directions = [[0, 1], [1, 0], [-1, 0], [0, -1]]
        for x, y in directions:
            if game_message.map.tiles[pos.x + x][pos.y + y] == "MINE":
                return Position(pos.x + x, pos.y + y)
        return []

    def get_random_position(self, map_size: int) -> Position:
        return Position(random.randint(0, map_size - 1), random.randint(0, map_size - 1))


    def get_mine_list(self, game_message: GameMessage):
        global mine_list
        if game_message.tick == 0:
            for i, row in enumerate(game_message.map.tiles):
                for j, column in enumerate(row):
                    if column == "MINE":
                        mine_list.append(Position(i, j))
        return mine_list


    def get_mine_tiles(self, game_message: GameMessage):
        global available_spaces
        directions = [[0,1], [1,1], [1, 0], [-1,0], [-1,-1], [0,-1], [-1,1], [1,-1]]
        for pos in mine_list:
            for x, y in directions:
                if game_message.map.tiles[pos.x + x][pos.y + y] == "EMPTY":
                    available_spaces.append(Position(pos.x + x, pos.y + y))
        return available_spaces

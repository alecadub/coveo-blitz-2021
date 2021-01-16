import math
from typing import List
from game_message import GameMessage, Position, Crew, UnitType
from game_command import Action, UnitAction, UnitActionType, BuyAction

mine_list = []
available_spaces = []
miner_positions = []


class Bot:

    def get_next_move(self, game_message: GameMessage) -> List[Action]:
        """
        Here is where the magic happens, for now the moves are random. I bet you can do better ;)

        No path finding is required, you can simply send a destination per unit and the game will move your unit towards
        it in the next turns.
        """
        global miner_positions
        actions: List[UnitAction] = []

        my_crew: Crew = game_message.get_crews_by_id()[game_message.crewId]
        base_position = my_crew.homeBase

        if game_message.tick == 0:
            self.get_mine_list(game_message, base_position)
            self.get_mine_tiles(game_message)
        elif game_message.tick == 1:
            actions.append(BuyAction(UnitType.CART))

        # depot_position: Position = game_message.map.depots[0].position

        for unit in my_crew.units:
            if unit.type == UnitType.MINER:
                miner_pos = self.is_next_to_mine(game_message, unit.position)
                if miner_pos:
                    actions.append(UnitAction(UnitActionType.MINE,
                                              unit.id,
                                              miner_pos))
                else:
                    actions.append(UnitAction(UnitActionType.MOVE,
                                              unit.id,
                                              available_spaces[0]))
            elif unit.type == UnitType.CART:
                miner_pos = self.cart_is_next_to_miner(unit.position)
                if unit.blitzium != 0:
                    if self.next_to_home(unit.position, base_position):
                        actions.append(UnitAction(UnitActionType.DROP,
                                                  unit.id,
                                                  base_position))
                    else:
                        actions.append(UnitAction(UnitActionType.MOVE,
                                                  unit.id,
                                                  Position(base_position.x + 1, base_position.y)))


                elif miner_pos:
                    actions.append(UnitAction(UnitActionType.PICKUP,
                                              unit.id,
                                              miner_pos))
                elif miner_positions:
                    #     means there is a stationary miner

                    actions.append(UnitAction(UnitActionType.MOVE,
                                              unit.id,
                                              self.find_empty_positions(miner_positions[0], game_message, base_position)))

        return actions

    def next_to_home(self, current_pos: Position, base: Position):
        if base == Position(current_pos.x, current_pos.y + 1) or base == Position(current_pos.x,
                                                                                  current_pos.y - 1) or base == Position(
            current_pos.x + 1, current_pos.y) or base == Position(current_pos.x - 1, current_pos.y):
            return True
        return []


    def cart_is_next_to_miner(self, curret_pos: Position):
        for miner in miner_positions:
            if miner == Position(curret_pos.x, curret_pos.y + 1) or miner == Position(curret_pos.x,
                                                                                      curret_pos.y - 1) or miner == Position(
                curret_pos.x + 1, curret_pos.y) or miner == Position(curret_pos.x - 1, curret_pos.y):
                return miner
        return []


    def find_empty_positions(self, pos: Position, game_message: GameMessage, base: Position):
        directions = [[0, 1], [1, 0], [-1, 0], [0, -1]]
        list_of_options = []
        for x, y in directions:
            if game_message.map.tiles[pos.x + x][pos.y + y] == "EMPTY":
                list_of_options.append(Position(pos.x + x, pos.y + y))
        if not list_of_options:
            return False
        return self.find_closest_to_position(base, list_of_options)[0]


    def is_next_to_mine(self, game_message: GameMessage, pos: Position):
        directions = [[0, 1], [1, 0], [-1, 0], [0, -1]]
        for x, y in directions:
            if game_message.map.tiles[pos.x + x][pos.y + y] == "MINE":
                miner_positions.append(pos)
                return Position(pos.x + x, pos.y + y)
        return []


    def get_mine_list(self, game_message: GameMessage, base: Position):
        global mine_list
        temp = []
        if game_message.tick == 0:
            for i, row in enumerate(game_message.map.tiles):
                for j, column in enumerate(row):
                    if column == "MINE":
                        temp.append(Position(i, j))
        # sort by distance from base
        mine_list = self.find_closest_to_position(base, temp)
        return mine_list


    def find_closest_to_position(self, pos: Position, random_list: List):
        sorted_list = []
        for x in range(0, len(random_list)):
            closest_mine = self.find_closes_mine(pos, random_list)
            sorted_list.append(closest_mine)
            random_list.remove(closest_mine)
        return sorted_list


    def get_mine_tiles(self, game_message: GameMessage):
        global available_spaces
        directions = [[0, 1], [1, 0], [-1, 0], [0, -1]]
        for pos in mine_list:
            for x, y in directions:
                if game_message.map.tiles[pos.x + x][pos.y + y] == "EMPTY":
                    available_spaces.append(Position(pos.x + x, pos.y + y))
        return available_spaces


    def distance(self, first: Position, second: Position):
        return math.sqrt(((first.x - second.x) ** 2) + ((first.y - second.y) ** 2))


    def find_closes_mine(self, pos: Position, minelist: List[Position]):
        closest_mine = minelist[0]
        dist = 1000000000
        for mine in minelist:
            if self.distance(pos, mine) < dist:
                closest_mine = mine
                dist = self.distance(pos, mine)
        return closest_mine

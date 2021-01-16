import math
from typing import List
from game_message import GameMessage, Position, Crew, UnitType, Unit
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
            self.get_mine_tiles(game_message, base_position)
        elif game_message.tick == 1:
            actions.append(BuyAction(UnitType.CART))

        # depot_position: Position = game_message.map.depots[0].position

        if my_crew.blitzium > my_crew.prices.OUTLAW and not self.has_outlaw(my_crew):
            actions.append(BuyAction(UnitType.OUTLAW))

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


                elif miner_pos and self.check_if_miner_has_blitz(my_crew):
                    actions.append(UnitAction(UnitActionType.PICKUP,
                                              unit.id,
                                              miner_pos))
                else:

                        miner_p =self.find_miner_position(my_crew)
                        actions.append(UnitAction(UnitActionType.MOVE,
                                                unit.id,
                                                self.find_empty_positions(miner_p, game_message,base_position)))

            elif unit.type == UnitType.OUTLAW:
                next_miner_pos = self.find_next_miner(game_message, my_crew)
                if next_miner_pos:
                    if self.is_next_to_position(unit.position, next_miner_pos) and my_crew.blitzium > 120:
                        actions.append(UnitAction(UnitActionType.ATTACK,
                                                  unit.id,
                                                  next_miner_pos))
                    else:
                        actions.append(UnitAction(UnitActionType.MOVE,
                                                  unit.id,
                                                  self.find_empty_positions(next_miner_pos, game_message,
                                                                            base_position)))

        return actions

    # def assign_the_cart(self, current_pos: Position):
    #     count = Unit.count("CART")
    #     for i in range(1,count)
    #         Unit.find("MINER")

    def find_miner_position(self, my_crew:Crew):
        for unit in my_crew.units:
            if unit.type==UnitType.MINER:
                return unit.position
        return []

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

    def get_mine_tiles(self, game_message: GameMessage, base: Position):  # OPTIMIZEEEEE
        global available_spaces
        directions = [[0, 1], [1, 0], [-1, 0], [0, -1]]
        for pos in mine_list:
            for x, y in directions:
                if game_message.map.tiles[pos.x + x][pos.y + y] == "EMPTY":
                    available_spaces.append(Position(pos.x + x, pos.y + y))

        available_spaces = self.find_closest_to_position(base, available_spaces)
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

    def find_next_miner(self, game_message: GameMessage, my_crew: Crew):
        for crew in game_message.crews:
            if crew.id != my_crew.id and crew.blitzium > my_crew.blitzium:
                for unit in crew.units:
                    if unit.type == UnitType.MINER:
                        return unit.position

    def are_we_first_place(self, game_message: GameMessage, my_crew: Crew):
        id_of_current_winner = None
        blitzium_of_current_winner = 0
        for crew in game_message.crews:
            if crew.blitzium > blitzium_of_current_winner:
                id_of_current_winner = crew.id
                blitzium_of_current_winner = crew.blitzium

        if id_of_current_winner == my_crew.id:
            return True
        else:
            return False

    def is_next_to_position(self, my_pos: Position, other_pos: Position):
        directions = [[0, 1], [1, 0], [-1, 0], [0, -1]]
        is_next = False
        for x, y in directions:
            pos_x = my_pos.x + x
            pos_y = my_pos.y + y
            if pos_x == other_pos.x and pos_y == other_pos.y:
                is_next = True
        return is_next

    def has_outlaw(self, my_crew: Crew):
        has_outlaw = False
        for unit in my_crew.units:
            if unit.type == UnitType.OUTLAW:
                has_outlaw = True

        return has_outlaw

    def check_if_miner_has_blitz(self, my_crew: Crew):
        for unit in my_crew.units:
            if unit.type == UnitType.MINER and unit.blitzium > 0:
                return True
        return False

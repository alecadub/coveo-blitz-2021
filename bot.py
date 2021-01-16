import math
from typing import List
from game_message import GameMessage, Position, Crew, UnitType, Unit
from game_command import Action, UnitAction, UnitActionType, BuyAction

mine_list = []
available_spaces = []
miner_positions = []
miners = []
carts = []
bought_last_round = False
nminers = 0
ncarts = 0

class Bot:

    def get_next_move(self, game_message: GameMessage) -> List[Action]:
        """
        Here is where the magic happens, for now the moves are random. I bet you can do better ;)

        No path finding is required, you can simply send a destination per unit and the game will move your unit towards
        it in the next turns.
        """
        global miner_positions
        global miners
        global carts
        global nminers
        global ncarts
        global bought_last_round
        actions: List[UnitAction] = []

        my_crew: Crew = game_message.get_crews_by_id()[game_message.crewId]
        base_position = my_crew.homeBase

        if bought_last_round:
            if my_crew.units[-1].type == UnitType.MINER:
                miners.append(my_crew.units[-1].id)
            elif my_crew.units[-1].type == UnitType.CART:
                carts.append(my_crew.units[-1].id)
        bought_last_round = False

        if game_message.tick == 0:
            self.get_mine_list_sorted(game_message, base_position)
            self.get_free_tile_around_mine(game_message, base_position)
            nminers += 1
            miners.append(my_crew.units[0].id)
        elif game_message.tick == 1:
            actions.append(BuyAction(UnitType.CART))
            ncarts += 1
        elif game_message.tick == 2:
            carts.append(my_crew.units[1].id)
        elif self.is_worth(my_crew, game_message):
            if nminers > ncarts:
                if my_crew.blitzium > my_crew.prices.CART and ncarts < 3:
                    actions.append(BuyAction(UnitType.CART))
                    ncarts += 1
                    bought_last_round = True
            else:
                if my_crew.blitzium > my_crew.prices.MINER and nminers < 3:
                    actions.append(BuyAction(UnitType.MINER))
                    nminers += 1
                    bought_last_round = True


        # depot_position: Position = game_message.map.depots[0].position
        # if not self.are_we_first_place(game_message, my_crew):

        if not self.are_we_first_place(game_message,
                                       my_crew) and my_crew.blitzium > my_crew.prices.OUTLAW and not self.has_outlaw(
            my_crew):
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
                                              available_spaces[miners.index(unit.id)]))

            elif unit.type == UnitType.CART:
                miner_pos = self.cart_is_next_to_miner(unit.position)
                if unit.blitzium != 0:
                    if self.next_to_home(unit.position, base_position):
                        actions.append(UnitAction(UnitActionType.DROP,
                                                  unit.id,
                                                  base_position))
                    else:
                        blocked = False
                        for guys in my_crew.units:
                            if unit.path:
                                if unit.path[0] == guys.position:
                                    blocked = True
                        if not blocked:
                            actions.append(UnitAction(UnitActionType.MOVE,
                                                  unit.id,
                                                  self.find_empty_positions(base_position, game_message, base_position)))


                elif miner_pos and self.check_if_miner_has_blitz(my_crew):
                    if not unit.path:
                        buddy = Unit
                        for temp in my_crew.units:
                            if miners[carts.index(unit.id)] == temp.id:
                                buddy = temp
                                break
                        actions.append(UnitAction(UnitActionType.PICKUP,
                                              unit.id,
                                              buddy.position))
                else:
                        # miner_p = self.find_miner_position(my_crew, unit)
                        buddy = Unit
                        for temp in my_crew.units:
                            if miners[carts.index(unit.id)] == temp.id:
                                buddy = temp
                                break
                        actions.append(UnitAction(UnitActionType.MOVE,
                                                unit.id,
                                                self.find_empty_positions(buddy.position, game_message,base_position)))

            elif unit.type == UnitType.OUTLAW:
                next_miner_pos = self.find_next_miner(game_message, my_crew)
                if next_miner_pos:
                    if self.is_next_to_position(unit.position,
                                                next_miner_pos) and my_crew.blitzium > 120 and not self.are_we_first_place(
                            game_message, my_crew):
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
            if unit.type == UnitType.MINER:
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
        temp = self.sorted_list_based_on_distance(base, list_of_options)
        return self.list_filter_remove_people_tiles(temp, game_message)[0]


    def is_next_to_mine(self, game_message: GameMessage, pos: Position):
        directions = [[0, 1], [1, 0], [-1, 0], [0, -1]]
        for x, y in directions:
            if game_message.map.tiles[pos.x + x][pos.y + y] == "MINE":
                if pos not in miner_positions:
                    miner_positions.append(pos)
                return Position(pos.x + x, pos.y + y)
        return []


    def get_mine_list_sorted(self, game_message: GameMessage, base: Position):
        global mine_list
        temp = []
        if game_message.tick == 0:
            for i, row in enumerate(game_message.map.tiles):
                for j, column in enumerate(row):
                    if column == "MINE":
                        temp.append(Position(i, j))
        # sort by distance from base
        mine_list = self.sorted_list_based_on_distance(base, temp)
        return mine_list


    def sorted_list_based_on_distance(self, pos: Position, random_list: List):
        sorted_list = []
        for x in range(0, len(random_list)):
            closest_mine = self.find_closest_point_in_a_list_to_another_point(pos, random_list)
            sorted_list.append(closest_mine)
            random_list.remove(closest_mine)
        return sorted_list


    def get_free_tile_around_mine(self, game_message: GameMessage, base: Position): #hide from people
        global available_spaces
        temp = []
        directions = [[0, 1], [1, 0], [-1, 0], [0, -1]]
        for pos in mine_list:
            for x, y in directions:
                if game_message.map.tiles[pos.x + x][pos.y + y] == "EMPTY":
                    temp.append(Position(pos.x + x, pos.y + y))

        temp = self.sorted_list_based_on_distance(base, temp)
        available_spaces = self.list_filter_remove_people_tiles(temp, game_message)


    def list_filter_remove_people_tiles(self, spaces: List[Position], game_message: GameMessage):
        unit_list = []
        filtered_list = []
        for crew in game_message.crews:
            for unit in crew.units:
                unit_list.append(unit.position)
        for space in spaces:
            if not space in unit_list:
                filtered_list.append(space)
        return filtered_list


    def distance(self, first: Position, second: Position):
        return math.sqrt(((first.x - second.x) ** 2) + ((first.y - second.y) ** 2))


    def find_closest_point_in_a_list_to_another_point(self, pos: Position, list: List[Position]):
        closest_point = list[0]
        dist = 1000000000
        for point in list:
            if self.distance(pos, point) < dist:
                closest_point = point
                dist = self.distance(pos, point)
        return closest_point

    def find_next_miner(self, game_message: GameMessage, my_crew: Crew):
        highest_miner_position = None
        highest_miner_blitzium = 0
        for crew in game_message.crews:
            if crew.id != my_crew.id and crew.blitzium > highest_miner_blitzium:
                for unit in crew.units:
                    if unit.type == UnitType.MINER:
                        highest_miner_position = unit.position
                        highest_miner_blitzium = crew.blitzium
        return highest_miner_position

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

    def is_worth(self, my_crew: Crew, game_message: GameMessage):
        if(my_crew.prices.CART + my_crew.prices.MINER < 1000 - game_message.tick):
            return True
        else:
            return False

import math
import random
from typing import List
from game_message import GameMessage, Position, Crew, UnitType, Unit, Depot
from game_command import Action, UnitAction, UnitActionType, BuyAction

mine_list = []
available_spaces = []
miner_positions = []
miners = []
carts = []
bought_last_round = False
nminers = 0
ncarts = 0
noutlaws = 0
miner_died = False
cart_died = False
extra_cart = False
extra_extra_cart = False
extra_extra_extra_cart = False


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
        global noutlaws
        global miner_died
        global cart_died
        global extra_cart
        global extra_extra_cart
        global extra_extra_extra_cart


        actions: List[UnitAction] = []

        my_crew: Crew = game_message.get_crews_by_id()[game_message.crewId]
        base_position = my_crew.homeBase

        worth = self.is_worth(my_crew, game_message)
        if bought_last_round:
            if miner_died:
                i = miners.index('rip')
                miners[i] = my_crew.units[-1].id
                miner_died = False
            elif cart_died:
                i = carts.index('rip')
                carts[i] = my_crew.units[-1].id
                cart_died = False
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
        elif worth:
            if nminers <= ncarts:
                self.get_free_tile_around_mine(game_message, base_position)
                if my_crew.blitzium > my_crew.prices.MINER and nminers < len(available_spaces):
                    actions.append(BuyAction(UnitType.MINER))
                    nminers += 1
                    bought_last_round = True

        if nminers > ncarts and not bought_last_round:
            if my_crew.blitzium > my_crew.prices.CART:
                actions.append(BuyAction(UnitType.CART))
                ncarts += 1
                bought_last_round = True

        if game_message.tick > 5 and len(my_crew.units) < (noutlaws + nminers + ncarts) and not bought_last_round:
            if worth:
                found = False
                for i, id in enumerate(miners):
                    for unit in my_crew.units:
                        if unit.id == id:
                            # this is not the dead unit
                            found = True
                    if found:
                        found = False
                        continue
                    else:
                        # this is the dead unit
                        miners[i] = "rip"
                        if (my_crew.blitzium > my_crew.prices.MINER):
                            bought_last_round = True
                            miner_died = True
                            actions.append(BuyAction(UnitType.MINER))
                if not miner_died:
                    for i, id in enumerate(carts):
                        for unit in my_crew.units:
                            if unit.id == id:
                                # this is not the dead unit
                                found = True
                        if found:
                            found = False
                            continue
                        else:
                            # this is the dead unit
                            carts[i] = "rip"
                            if (my_crew.blitzium > my_crew.prices.CART):
                                bought_last_round = True
                                cart_died = True
                                actions.append(BuyAction(UnitType.CART))



        if 0 < len(game_message.map.depots) < 3 and not extra_cart:
            if my_crew.blitzium > my_crew.prices.CART and not bought_last_round:
                actions.append(BuyAction(UnitType.CART))
                extra_cart = True
        elif 3 <= len(game_message.map.depots) < 6 and not extra_extra_cart:
            if my_crew.blitzium > my_crew.prices.CART and not bought_last_round:
                actions.append(BuyAction(UnitType.CART))
                extra_extra_cart = True
        elif len(game_message.map.depots) >= 7 and not extra_extra_extra_cart:
            if my_crew.blitzium > my_crew.prices.CART and not bought_last_round:
                actions.append(BuyAction(UnitType.CART))
                extra_extra_extra_cart = True

        if not self.are_we_first_place(game_message,
                                       my_crew) and my_crew.blitzium > my_crew.prices.OUTLAW and not self.has_outlaw(
            my_crew):
            actions.append(BuyAction(UnitType.OUTLAW))
            noutlaws += 1

        for unit in my_crew.units:
            if unit.type == UnitType.MINER:
                miner_pos = self.is_next_to_mine(game_message, unit.position)
                if miner_pos:
                    actions.append(UnitAction(UnitActionType.MINE,
                                              unit.id,
                                              miner_pos))

                elif not self.find_available(game_message):
                    if noutlaws == 0:
                        actions.append(BuyAction(UnitType.OUTLAW))
                        noutlaws += 1

                else:
                    self.get_free_tile_around_mine(game_message, base_position)
                    actions.append(UnitAction(UnitActionType.MOVE,
                                              unit.id,
                                              self.find_available(game_message)))

            elif unit.type == UnitType.CART:

                if game_message.tick % 200 == 0:

                    actions.append(UnitAction(UnitActionType.MOVE,
                                              unit.id,
                                              self.find_empty_positions(
                                                  self.get_random_position(game_message.map.get_map_size()),
                                                  game_message,
                                                  base_position)))
                else:

                    if extra_cart and not unit.id in carts:
                        depot_pos = self.next_to_a_depot(unit.position, game_message.map.depots)
                        if game_message.map.depots and unit.blitzium < 25 and depot_pos:
                            # we are next to a depot, pickup
                            actions.append(UnitAction(UnitActionType.PICKUP,
                                                      unit.id,
                                                      depot_pos))
                        elif game_message.map.depots and unit.blitzium < 25:
                            #         go to depot
                            depot_positions = []
                            for depot in game_message.map.depots:
                                depot_positions.append(depot.position)

                            sorted_depot_list_positions = self.sorted_list_based_on_distance(base_position, depot_positions)
                            actions.append(UnitAction(UnitActionType.MOVE,
                                                      unit.id,
                                                      self.find_empty_positions(sorted_depot_list_positions[0],
                                                                                game_message, base_position)))

                        elif self.next_to_home(unit.position, base_position) and unit.blitzium > 0:
                            actions.append(UnitAction(UnitActionType.DROP,
                                                      unit.id,
                                                      base_position))
                        elif unit.blitzium == 25 or (unit.blitzium > 0 and not game_message.map.depots):
                            actions.append(UnitAction(UnitActionType.MOVE,
                                                      unit.id,
                                                      self.find_empty_positions(base_position, game_message,
                                                                                base_position)))
                        else:
                            actions.append(UnitAction(UnitActionType.MOVE,
                                                      unit.id,
                                                      self.find_empty_positions(
                                                          self.get_random_position(game_message.map.get_map_size()),
                                                          game_message,
                                                          base_position)))
                    else:
                        miner_pos = self.cart_is_next_to_miner(unit.position)
                        if miner_died:
                            try:
                                if miners[carts.index(unit.id)] == "rip":
                                    if game_message.map.depots:
                                        actions.append(UnitAction(UnitActionType.MOVE,
                                                                  unit.id,
                                                                  game_message.map.depots[0].position))
                                    else:
                                        continue
                            except:
                                continue
                        elif unit.blitzium != 0:
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
                                                              self.find_empty_positions(base_position, game_message,
                                                                                        base_position)))
                        elif miner_pos and self.check_if_miner_has_blitz(my_crew):
                            buddy = None
                            for temp in my_crew.units:
                                try:
                                    if miners[carts.index(unit.id)] == temp.id:
                                        buddy = temp
                                        break
                                except:
                                    continue
                            if buddy and self.is_next_to_position(buddy.position, unit.position):
                                actions.append(UnitAction(UnitActionType.PICKUP,
                                                          unit.id,
                                                          buddy.position))
                            else:
                                if buddy:
                                    actions.append(UnitAction(UnitActionType.MOVE,
                                                              unit.id,
                                                              self.find_empty_positions(buddy.position, game_message,
                                                                                        base_position)))
                                else:
                                    drop = self.find_depot(game_message)
                                    if drop:
                                        actions.append(UnitAction(UnitActionType.MOVE,
                                                                  unit.id,
                                                                  self.find_empty_positions(drop, game_message,
                                                                                            base_position)))
                                    else:
                                        actions.append(UnitAction(UnitActionType.MOVE,
                                                                  unit.id,
                                                                  self.find_empty_positions(
                                                                      self.get_random_position(
                                                                          game_message.map.get_map_size()),
                                                                      game_message,
                                                                      base_position)))
                        else:
                            # miner_p = self.find_miner_position(my_crew, unit)
                            buddy = None
                            for temp in my_crew.units:
                                try:
                                    if miners[carts.index(unit.id)] == temp.id:
                                        buddy = temp
                                        break
                                except:
                                    continue
                            if buddy:
                                actions.append(UnitAction(UnitActionType.MOVE,
                                                          unit.id,
                                                          self.find_empty_positions(buddy.position, game_message,
                                                                                    base_position)))
                            else:
                                drop = self.find_depot(game_message)
                                if drop:
                                    if self.is_next_to_position(drop, unit.position):
                                        actions.append(UnitAction(UnitActionType.PICKUP,
                                                                  unit.id,
                                                                  drop))
                                    else:
                                        actions.append(UnitAction(UnitActionType.MOVE,
                                                                  unit.id,
                                                                  self.find_empty_positions(drop, game_message,
                                                                                            base_position)))
                                else:
                                    actions.append(UnitAction(UnitActionType.MOVE,
                                                              unit.id,
                                                              self.find_empty_positions(
                                                                  self.get_random_position(game_message.map.get_map_size()),
                                                                  game_message,
                                                                  base_position)))


            elif unit.type == UnitType.OUTLAW:
                if self.outlaw_on_depot(unit.position, game_message.map.depots):
                    actions.append(UnitAction(UnitActionType.MOVE,
                                              unit.id,
                                              self.find_empty_positions(base_position, game_message,
                                                                        base_position)))
                next_miner_pos = self.find_next_miner(game_message, my_crew)
                if next_miner_pos:
                    if self.is_next_to_position(unit.position,
                                                next_miner_pos) and my_crew.blitzium > 120 and not self.are_we_first_place(
                        game_message, my_crew):
                        actions.append(UnitAction(UnitActionType.ATTACK,
                                                  unit.id,
                                                  next_miner_pos))
                    elif self.find_empty_positions(next_miner_pos, game_message,
                                                   base_position):
                        actions.append(UnitAction(UnitActionType.MOVE,
                                                  unit.id,
                                                  self.find_empty_positions(next_miner_pos, game_message,
                                                                            base_position)))
        return actions

    def outlaw_on_depot(self, pos: Position, list: List[Depot]):
        for depot in list:
            if pos == depot.position:
                return True
        return False

    def find_available(self, game_message: GameMessage):
        filtered = self.list_filter_remove_people_tiles(available_spaces, game_message)
        if filtered:
            return filtered[0]
        return False

    def find_miner_position(self, my_crew: Crew):
        for unit in my_crew.units:
            if unit.type == UnitType.MINER:
                return unit.position
        return []

    def next_to_a_depot(self, pos: Position, depots: List[Depot]):
        #     iterate throught the depots, if its next to it return that, if not return false
        for depot in depots:
            if self.is_next_to_position(depot.position, pos):
                # aim towards the depot
                return depot.position
        return False

    def get_random_position(self, map_size: int) -> Position:
        return Position(random.randint(0, map_size - 1), random.randint(0, map_size - 1))

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
        y_length = len(game_message.map.tiles)
        x_length = len(game_message.map.tiles[0])
        list_of_options = []
        for x, y in directions:
            if game_message.map.tiles[(pos.x + x) % x_length][(pos.y + y) % y_length] == "EMPTY":
                list_of_options.append(Position(pos.x + x, pos.y + y))
        if not list_of_options:
            return False
        temp = self.sorted_list_based_on_distance(base, list_of_options)
        if not self.list_filter_remove_people_tiles(temp, game_message):
            return None
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

    def get_free_tile_around_mine(self, game_message: GameMessage, base: Position):  # hide from people
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
        if ((my_crew.prices.CART + my_crew.prices.MINER)*3 < 1000 - game_message.tick) or nminers < 4:
            return True
        else:
            return False

    def find_depot(self, game_message: GameMessage):
        lowest_depot = 0
        depot_position = None

        for depot in game_message.map.depots:
            if depot.blitzium > lowest_depot:
                lowest_depot = depot.blitzium
                depot_position = depot.position

        return depot_position

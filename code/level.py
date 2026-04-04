import pygame
from tilemap import TileMap
from pathfinder import Pathfinder
from bush import Bush
from rat import Rat
from snake import Snake
from stats import Stats
from player  import Player
from settings import TILE_SIZE, MAP_W, MAP_H

class Level:

    def __init__(self, screen, camera, level_name,
        players, creatures, obstacles, map_w = MAP_W, map_h = MAP_H):

        self.screen     = screen
        self.camera     = camera
        self.tilemap    = TileMap("../data/levels/" + level_name)
        self.players    = players
        self.creatures  = creatures
        self.obstacles  = obstacles
        self.map_w      = map_w
        self.map_h      = map_h

        self.player = None
        self.creature_list  = []
        self.obstacle_list  = []

        self._load_assets()
        self._spawn_entities()

        # Debug code
        self.tilemap.print_grids()

    # Called: __init__()
    def _load_assets(self):

        # Loads assets: Ground tiles of the level.
        ground_tile  = pygame.image.load("../assets/sprites/tile/grass.png").convert()
        self.ground = pygame.transform.scale(ground_tile, (TILE_SIZE, TILE_SIZE))

        # Give all to camera.
        self.camera.ground = self.ground

    # Called: __init__()
    def _spawn_entities(self):

        # player setup
        pd = self.tilemap.get_player_data()

        player_stats = Stats(
            str_=pd["str"], agi=pd["agi"], sta=pd["sta"],
            int_=pd["int"], spr=pd["spr"], res=pd["res"], def_=pd["def"],
            is_player=True
        )
        player_stats.gain_exp(pd["exp"])

        player_pos = self.tilemap.find(1)
        px, py = self.tilemap.to_world(*player_pos[0])

        self.player = Player(px, py, player_stats, *[self.camera, self.players])

        # Creature and obstacle setup
        for row in range(self.tilemap.rows):
            for col in range(self.tilemap.cols):

                # Get tile id of specific position from tilemap
                tile = self.tilemap.get(row, col)
                # Convert the tilemap coordinates to real screen coordinates.
                x, y = self.tilemap.to_world(row, col)

                # All different tiles (types) ids (except player tile).
                if tile in (2, 3):

                    # All creatures.
                    if tile == 2:

                        cd = self.tilemap.get_creature_data(row, col)

                        # If there is no consistency between csv and json data files continue.
                        # Means: In the grid there is a creature in (x,y) witch is not appearing in json file.
                        if cd is None:
                            continue

                        stats = Stats(
                            str_=cd["str"], agi=cd["agi"], sta=cd["sta"],
                            int_=cd["int"], spr=cd["spr"], res=cd["res"],
                            def_=cd["def"]
                        )
                        stats.gain_exp(cd["exp"])
                        home = pygame.Rect(x, y, 32, 32) if cd["home"] else None

                        if cd["type"] == "rat":
                            self.creature_list.append(
                                Rat(x, y, stats, self.player, home, cd["returning"], cd["fleeing"],
                                    *[self.camera, self.creatures]))

                        elif cd["type"] == "snake":
                            self.creature_list.append(
                                Snake(x, y, stats, self.player, home, cd["returning"], cd["fleeing"],
                                    *[self.camera, self.creatures]))
                    # All obstacles
                    elif tile == 3:

                        # Only obstacle in game right now is the bush.
                        self.obstacle_list.append(Bush(x, y, self.tilemap, *[self.camera, self.obstacles]))

        # Now that all creatures and obstacles are set.
        # We give all creatures and obstacles to player.
        self.player.enemies     = self.creature_list
        self.player.obstacles   = self.obstacle_list
        # We pass all obstacles to creatures.
        for c in self.creature_list:
            c.obstacles   = self.obstacle_list
        # We pass all obstacles to tilemap.
        self.tilemap.obstacles = self.obstacle_list

        # We pass pathfinder to all creatures and to all creatures all other creatures list
        pathfinder = Pathfinder(self.tilemap)
        for c in self.creature_list:
            c.pathfinder    = pathfinder
            c.neighbors     = self.creature_list

        self.tilemap.build_hitbox_grid(self.obstacle_list, hitbox_inflate = -50)


    # Called: Indie_Game._update(), Indie_Game._draw()
    @property
    def active_creatures(self):

        return [c for c in self.creature_list if c.state != "dead"]

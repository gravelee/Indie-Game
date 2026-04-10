import pygame
from tilemap import TileMap
from pathfinder import Pathfinder
from bush import Bush
from rat import Rat
from snake import Snake
from stats import Stats
from player  import Player
from settings import MAP_W, MAP_H

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

        # Load the full grass spritesheet.
        sheet = pygame.image.load("../assets/sprites/tilemaps/leaf/leaf32.png").convert()

        # Each tile is 16x16 in the sheet, scale to 32x32 for game.
        SHEET_COLS = 24
        SHEET_ROWS = 4
        tile_w = sheet.get_width() // SHEET_COLS   # 32px
        tile_h = sheet.get_height() // SHEET_ROWS  # 32px

        # We import to tileset the whole grass tilemap and also transform it to fit to games tile size.
        self.grass_tileset = []
        for row in range(SHEET_ROWS):
            for col in range(SHEET_COLS):
                tile = sheet.subsurface(pygame.Rect(col * tile_w, row * tile_h, tile_w, tile_h))
                self.grass_tileset.append(tile)

        # Give all to camera.
        self.camera.grass_tileset   = self.grass_tileset
        self.camera.terrain_grid    = self.tilemap.terrain_grid

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
                if tile in (2, 3, 101):

                    # All creatures.
                    if tile in (2, 3):

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

                        # Rat creature.
                        if tile == 2:

                            #if cd["type"] == "rat":
                                self.creature_list.append(
                                    Rat(x, y, stats, self.player, home, cd["returning"], cd["fleeing"],
                                        *[self.camera, self.creatures]))

                        # Snake creature.
                        elif tile == 3:

                            #if cd["type"] == "snake":
                                self.creature_list.append(
                                    Snake(x, y, stats, self.player, home, cd["returning"], cd["fleeing"],
                                        *[self.camera, self.creatures]))

                    # Bush obstacle.
                    elif tile == 101:

                        # Only obstacle in game right now is the bush.
                        self.obstacle_list.append(Bush(x, y, self.tilemap, *[self.camera, self.obstacles]))

        # Now that all creatures and obstacles are set.
        # We build the obstacle hash.
        self._build_obstacle_hash()

        # We give all creatures, obstacles, obstacle hash and cell size to player.
        self.player.enemies         = self.creature_list
        self.player.obs_hash        = self._obs_hash
        self.player.obs_cell_size   = self._obs_cell_size

        # We pass all obstacles, obstacle hash and cell size to tilemap.
        self.tilemap.obstacles      = self.obstacle_list
        self.tilemap.obs_hash       = self._obs_hash
        self.tilemap.obs_cell_size  = self._obs_cell_size

        # We build the hitbox grind in tilemap.
        self.tilemap.build_hitbox_grid(self.obstacle_list)

        # We pass the remove from hash func to all obstacles.
        for obs in self.obstacle_list:
            obs.remove_from_hash = self._remove_from_obstacle_hash

        # We pass pathfinder, neighbors, obstacle hash and cell size to all creatures.
        pathfinder = Pathfinder(self.tilemap)
        for c in self.creature_list:
            c.pathfinder    = pathfinder
            c.neighbors     = self.creature_list
            c.obs_hash      = self._obs_hash
            c.obs_cell_size = self._obs_cell_size


    # Called: _spawn_entities().
    def _build_obstacle_hash(self, cell_size = 96):

        self._obs_cell_size = cell_size
        self._obs_hash = {}

        for obs in self.obstacle_list:

            cx = obs.hitbox.centerx // cell_size
            cy = obs.hitbox.centery // cell_size

            for dx in range(-1, 2):
                for dy in range(-1, 2):

                    key = (cx + dx, cy + dy)
                    if key not in self._obs_hash:
                        self._obs_hash[key] = set()
                    self._obs_hash[key].add(obs)

    # Called: Bush.take_hit().
    def _remove_from_obstacle_hash(self, obs):

        cx = obs.hitbox.centerx // self._obs_cell_size
        cy = obs.hitbox.centery // self._obs_cell_size

        for dx in range(-1, 2):
            for dy in range(-1, 2):
                key = (cx + dx, cy + dy)
                self._obs_hash.get(key, set()).discard(obs)

    # Called: Indie_Game._update(), Indie_Game._draw()
    @property
    def active_creatures(self):

        return [c for c in self.creature_list if c.state != "dead"]

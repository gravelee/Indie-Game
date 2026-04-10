import csv
import json
import pygame
from settings import TILE_SIZE, SPRITE_SCALE

class TileMap:

    def __init__(self, path):

        self.original_grid          = []

        # Opens the csv map data and put them in a grid.
        with open(path + ".csv", newline="") as f:
            reader = csv.reader(f)
            for row in reader:
                self.original_grid.append([int(cell) for cell in row])

        # Transpose so grid is indexed as grid[x][y] = grid[horizontal][vertical]
        self.original_grid          = [list(col) for col in zip(*self.original_grid)]

        self.data                   = None

        # Opens the json entities data and loads it to data attr.
        with open(path + ".json") as f:
            self.data = json.load(f)

        self.rows                   = len(self.original_grid)
        self.cols                   = len(self.original_grid[0])

        self.width                  = self.rows * TILE_SIZE
        self.height                 = self.cols * TILE_SIZE

        self.obs_hash               = None
        self.obs_cell_size          = None
        self.hitbox_blocked         = None

        self.terrain_grid           = []

        # Load the terain map data.
        with open("../data/levels/level1.csv") as f:
            reader = csv.reader(f)
            for row in reader:
                self.terrain_grid.append([int(cell) for cell in row])

        # Transpose so terain grid is indexed as terrain_grid[x][y] = terrain_grid[horizontal][vertical]
        self.terrain_grid           = [list(col) for col in zip(*self.terrain_grid)]

    # Called: Level._spawn_entities()
    def get(self, row, col):
        # Returns the value on that specific (x,y) place of the original_grid.
        return self.original_grid[row][col]

    # Called: Level._spawn_entities()
    def find(self, tile_id):
            # Return a list of all specific tile id positions on the original_grid.
            results = []
            for r, row in enumerate(self.original_grid):
                for c, val in enumerate(row):
                    if val == tile_id:
                        results.append((r, c))
            return results

    # Called: Level._spawn_entities()
    def to_world(self, row, col):
        # Converts the tilemap system (#row_tiles x #col_tiles) to world size.
        return row * TILE_SIZE, col * TILE_SIZE

    # Called: Level._spawn_entities()
    def get_player_data(self):
        # Returns the json file player data.
        return self.data["player"]

    # Called: Level._spawn_entities()
    def get_creature_data(self, row, col):
        # Returns all creature json data that much with the csv file grid data.
        for r in self.data["creatures"]:
            if r["row"] - 1 == row and r["col"] - 1 == col:
                return r
        return None

    # Called: Pathfinder._nearest_walkable(), Pathfinder._neighbors(),
    #   Pathfinder.find_path(), Pathfinder.move_to_target(), Pathfinder.line_of_sight()
    def is_walkable(self, row, col):

        # Returns if the specific position is walkable always from the grid.
        return self.original_grid[row][col] < 100

    # Called: Level._spawn_entities()
    def build_hitbox_grid(self, obstacles):

        # Precompute which tiles a creature cannot stand on due to obstacle hitboxes.

        sprite_size = TILE_SIZE * SPRITE_SCALE
        hitbox_size = sprite_size - 50  # Hitbox inflation.

        self.hitbox_blocked = [[False] * self.cols for _ in range(self.rows)]

        for r in range(self.rows):
            for c in range(self.cols):

                world_x = r * TILE_SIZE + TILE_SIZE // 2
                world_y = c * TILE_SIZE + TILE_SIZE // 2
                creature_hitbox = pygame.Rect(0, 0, hitbox_size, hitbox_size)
                creature_hitbox.center = (world_x, world_y)

                if any(creature_hitbox.colliderect(obs.hitbox) for obs in obstacles):
                    self.hitbox_blocked[r][c] = True

    # Called: Bush.take_hit().
    def update_hitbox_grid(self, obs):

        # Only clear tiles affected by this specific obstacle.
        # Check tiles in the region around the dead bush only.

        sprite_size = TILE_SIZE * SPRITE_SCALE
        hitbox_size = sprite_size - 50  # same inflate as build

        r_center = obs.rect.centerx // TILE_SIZE
        c_center = obs.rect.centery // TILE_SIZE

        # Only check tiles in the vicinity of the dead bush.
        for r in range(r_center - 1, r_center + 2):
            for c in range(c_center - 1, c_center + 2):

                if not (0 <= r < self.rows and 0 <= c < self.cols):
                    continue

                # Recheck this tile against remaining obstacles only.
                world_x = r * TILE_SIZE + TILE_SIZE // 2
                world_y = c * TILE_SIZE + TILE_SIZE // 2
                creature_hitbox = pygame.Rect(0, 0, hitbox_size, hitbox_size)
                creature_hitbox.center = (world_x, world_y)

                # Check nearby obstacles using hash.
                cell_x = world_x // self.obs_cell_size
                cell_y = world_y // self.obs_cell_size

                nearby = set()
                for dx in range(-1, 2):
                    for dy in range(-1, 2):
                        nearby |= self.obs_hash.get((cell_x + dx, cell_y + dy), set())

                # Update the hitbox grid.
                self.hitbox_blocked[r][c] = any(
                    creature_hitbox.colliderect(o.hitbox) for o in nearby)

    # Called: Bush.take_hit()
    def update_original_grid(self, world_x, world_y):

        # Mark destroyed obstacle tile as walkable in original_grid.
        row = world_x // TILE_SIZE
        col = world_y // TILE_SIZE

        if 0 <= row < self.rows and 0 <= col < self.cols:
            self.original_grid[row][col] = 0

    # Called: Level.__init__()
    def print_grids(self, path="../data/levels/grids_debug.txt"):

        with open(path, "w") as f:
            f.write("=== ORIGINAL ===\n")
            # outer loop = y (vertical, cols axis after transpose)
            # inner loop = x (horizontal, rows axis after transpose)
            for c in range(self.cols):
                line = ""
                for r in range(self.rows):
                    og = self.original_grid[r][c]
                    if og == 101:
                        line += "X"
                    elif og == 1:
                        line += "P"
                    elif og == 2:
                        line += "R"
                    elif og == 3:
                        line += "S"
                    elif og == 100:
                        line += "#"
                    else:
                        line += " "  # walkable
                f.write(line + "\n")
            f.write("\n")

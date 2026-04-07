import csv
import json
import pygame
from settings import TILE_SIZE, SPRITE_SCALE

class TileMap:

    def __init__(self, path):

        # Opens the csv map data and put them in a grid.
        self.original_grid = []
        with open(path + ".csv", newline="") as f:
            reader = csv.reader(f)
            for row in reader:
                self.original_grid.append([int(cell) for cell in row])

        # Transpose so grid is indexed as grid[x][y] = grid[horizontal][vertical]
        self.original_grid = [list(col) for col in zip(*self.original_grid)]

        # Opens the json entities data and loads it to data attr.
        with open(path + ".json") as f:
            self.data = json.load(f)

        # Grid row and column length.
        self.rows   = len(self.original_grid)
        self.cols   = len(self.original_grid[0])

        # Sets width and heigh.
        self.width  = self.rows * TILE_SIZE
        self.height = self.cols * TILE_SIZE

        self.obstacles      = None
        self.hitbox_blocked = None

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
            if r["row"] -1 == row and r["col"] -1 == col:
                return r
        return None

    # Called: Pathfinder._nearest_walkable(), Pathfinder._neighbors(),
    #   Pathfinder.find_path(), Pathfinder.move_to_target(), Pathfinder.line_of_sight()
    def is_walkable(self, row, col):

        # Returns if the specific position is walkable always from the grid.
        return self.original_grid[row][col] != 3

    # Called: update_tilemap(), Level._spawn_entities()
    def build_hitbox_grid(self, obstacles, hitbox_inflate=-50):

        # Precompute which tiles a creature cannot stand on due to obstacle hitboxes
        sprite_size = TILE_SIZE * SPRITE_SCALE
        hitbox_size = sprite_size + hitbox_inflate

        self.hitbox_blocked = [[False] * self.cols for _ in range(self.rows)]

        for r in range(self.rows):
            for c in range(self.cols):
                world_x = r * TILE_SIZE + TILE_SIZE // 2
                world_y = c * TILE_SIZE + TILE_SIZE // 2
                creature_hitbox = pygame.Rect(0, 0, hitbox_size, hitbox_size)
                creature_hitbox.center = (world_x, world_y)
                if any(creature_hitbox.colliderect(obs.hitbox) for obs in obstacles):
                    self.hitbox_blocked[r][c] = True

        #for r in range(self.rows):
        #    for c in range(self.cols):
        #        tile_rect = pygame.Rect(r * TILE_SIZE, c * TILE_SIZE, TILE_SIZE, TILE_SIZE)
        #        if any(tile_rect.colliderect(obs.rect) for obs in obstacles):
        #            self.hitbox_blocked[r][c] = True

    # Called: Bush.take_hit()
    def update_tilemap(self, world_x, world_y):

        # Mark destroyed obstacle tile as walkable in original_grid.
        row = world_x // TILE_SIZE
        col = world_y // TILE_SIZE
        self.original_grid[row][col] = 0

        # Rebuild hitbox grid to reflect the removed obstacle.
        if self.obstacles is not None:
            self.build_hitbox_grid(self.obstacles, hitbox_inflate=-50)


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
                    if og == 1:
                        line += "P"
                    elif og == 2:
                        line += "C"
                    elif og == 3:
                        line += "X"
                    elif og == 100:
                        line += "#"
                    else:
                        line += " "  # walkable
                f.write(line + "\n")
            f.write("\n")

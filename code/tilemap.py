import csv
import json
import math
from settings import TILE_SIZE, OBSTACLE_SIZE_MAX

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

        # Inflating the original grid with neighbor obstacle tiles based of their respective sizes.
        self.occupied_grid_1 = [[False] * self.cols for _ in range(self.rows)]
        # Inflating the occupied_grid_1 with neighbor obstacle/occupied tiles based on the creatures size (3x3 tiles of 32x32 tile size).
        self.occupied_grid_2 = [[False] * self.cols for _ in range(self.rows)]
        # Inflating the occupied_grid_2 with neighbor obstacle/occupied tiles based on the creatures size (5x5 tiles of 32x32 tile size).
        self.occupied_grid_3 = [[False] * self.cols for _ in range(self.rows)]

        self.obstacles = None

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

    # Called: construct_grid(), update_grid(),
    #   Pathfinder._nearest_walkable(), Pathfinder._to_world_safe(),
    #   Pathfinder._reconstruct(), Pathfinder._neighbors(),
    #   Pathfinder.find_path(), Pathfinder.has_line_of_sight().
    def is_walkable(self, grid_update, row, col):
        # Returns if the specific position is walkable always from the apropriate grid.
        if grid_update == -1:
            return self.original_grid[row][col] != 3
        if grid_update == 0:
            return not self.occupied_grid_1[row][col]
        if grid_update == 1:
            return not self.occupied_grid_2[row][col]
        if grid_update == 2:
            return not self.occupied_grid_3[row][col]

    # Called: update_tilemap()
    def construct_grid(self, grid_update, world_x = 0, world_y = 0):

        # Here we construct the occupied 1, 2 and 3 grids for the first time.
        # Also we reconstruct occupied_grid_2 and 3 (world_ coordinates != 0) if there is a change in occupied_grid_1.

        # It recalculates some of the cleared map tile occupation status because there was a change in the map.
        row     = world_x // TILE_SIZE
        col     = world_y // TILE_SIZE

        # Ranges are calculated based on if we got world_x and y. Also clamps the coordinates to be safe.
        range_x = range(0, self.rows) if world_x == 0 else range(max(0, row - grid_update), min(self.rows, row + grid_update + 1))
        range_y = range(0, self.cols) if world_y == 0 else range(max(0, col - grid_update), min(self.cols, col + grid_update + 1))

        # Do that only for reconstructure
        if world_x != 0 and world_y != 0:
            # For all the grids size.
            for r in range_x:
                for c in range_y:
                    # Init grids.
                    if grid_update == 2:
                        self.occupied_grid_2[r][c] = False
                    elif grid_update == 3:
                        self.occupied_grid_3[r][c] = False

        # For all the original_grid size.
        for r in range_x:
            for c in range_y:

                # If tile is not walkable from the "grid".
                if not self.is_walkable(grid_update - 2, r, c):

                    # For all tiles within unwalkable tile range 1.
                    for dr in range(-1, 2):
                        for dc in range(-1, 2):

                            nr, nc = r + dr, c + dc

                            # If tile falls out of the map (or check area) continue.
                            if not (nr in range_x and nc in range_y):
                                continue

                            # Check what grid you update.
                            if grid_update == 1:
                                self.occupied_grid_1[nr][nc] = True
                            elif grid_update == 2:
                                self.occupied_grid_2[nr][nc] = True
                            elif grid_update == 3:
                                self.occupied_grid_3[nr][nc] = True

    # Called: update_tilemap()
    def update_grid(self, footprint, world_x, world_y):

        # Here we update original and occupied_1 grids if there is a change in the obstacle list.

        # It recalculates some of the cleared map tile occupation status because there was a change in the map.
        row = world_x // TILE_SIZE
        col = world_y // TILE_SIZE

        # Mark the tile itself as walkable in grid
        self.original_grid[row][col] = 0

        # For each tile in the footprint zone around the removed obstacle.
        # Check walkability from original_grid to update occupied_grid_1.
        for rr in range(-footprint, footprint + 1):
            for rc in range(-footprint, footprint + 1):

                # Neighbor coordinates.
                nr, nc = row + rr, col + rc

                # If tile falls out of the map continue.
                if not (0 <= nr < self.rows and 0 <= nc < self.cols):
                    continue

                # Check if this tile is still within max footprint size of any remaining obstacle.
                still_blocked = False
                for er in range(-OBSTACLE_SIZE_MAX, OBSTACLE_SIZE_MAX + 1):
                    for ec in range(-OBSTACLE_SIZE_MAX, OBSTACLE_SIZE_MAX + 1):

                        # Check obstacle coordinates.
                        cr, cc = nr + er, nc + ec

                        # If tile falls out of the map continue.
                        if not (0 <= cr < self.rows and 0 <= cc < self.cols):
                            continue

                        # Checks if the tile is originally occupied (from original_grid).
                        if not self.is_walkable(-1, cr, cc):

                            # Differencial coordinates.
                            dr, dc = cr - nr, cc - nc

                            # Check for all obstacles.
                            for obs in self.obstacles:

                                # If obstacle coordinates same as check obstacle coordinates.
                                if obs.rect.centerx // TILE_SIZE == cr and obs.rect.centery // TILE_SIZE == cc:

                                    # Check if obstacle footprint radius overlaps specific tile.
                                    if obs.tile_radius >= math.hypot(dr, dc):

                                        still_blocked = True
                                        break

                    if still_blocked:
                        break

                # Update all other grids.
                if not still_blocked:
                    self.occupied_grid_1[nr][nc] = False

    # Called: Level._spawn_entities(), Bush.take_hit()
    def update_tilemap(self, footprint, world_x = 0, world_y = 0):

        # Here we update the tilemap based on the parameters that are given (world_x, y).
        # Usually this is happening when an obstacle is destroyed.

        if world_x != 0 and world_y != 0:
            # Updates general and occuplied grids after change.
            self.update_grid(footprint, world_x, world_y)
            # Updates occupied_grid_2 grid too.
            self.construct_grid(2, world_x, world_y)
            # Updates occupied_grid_3 grid too.
            self.construct_grid(3, world_x, world_y)
        else:
            self.construct_grid(footprint, world_x, world_y)

    # Called: None
    def print_grids(self, path="../data/levels/grids_debug.txt"):
        grids = {
            "ORIGINAL":   self.original_grid,
            "OCCUPIED_1": self.occupied_grid_1,
            "OCCUPIED_2": self.occupied_grid_2,
            "OCCUPIED_3": self.occupied_grid_3,
        }
        with open(path, "w") as f:
            for name, grid in grids.items():
                f.write(f"=== {name} ===\n")
                # outer loop = y (vertical, cols axis after transpose)
                # inner loop = x (horizontal, rows axis after transpose)
                for c in range(self.cols):
                    line = ""
                    for r in range(self.rows):
                        og = self.original_grid[r][c]
                        if og == 1:     line += "P"
                        elif og == 2:   line += "C"
                        elif og == 3:   line += "X"
                        elif og == 100: line += "#"
                        elif name == "ORIGINAL":
                            line += " "
                        elif grid[r][c]:
                            line += "."  # blocked
                        else:
                            line += " "  # walkable
                    f.write(line + "\n")
                f.write("\n")

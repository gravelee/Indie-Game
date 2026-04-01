import heapq
import math
import random
from settings import ATTACK_DIST, TILE_SIZE

class Pathfinder:

    def __init__(self, tilemap):

        self.tilemap = tilemap

    # Called: find_path(), has_line_of_sight().
    def _to_grid(self, world_pos):

        # Convert and returns world coordinates to grid coordinates.
        row = int(world_pos[0] / TILE_SIZE)
        col = int(world_pos[1] / TILE_SIZE)
        row = max(0, min(row, self.tilemap.rows - 1))
        col = max(0, min(col, self.tilemap.cols - 1))
        return (row, col)

    # Called: _reconstruct(), find_path(), has_line_of_sight().
    def _snap_to_tile_center(self, grid_pos):

        # If position is none returns none.
        if not grid_pos:
            return grid_pos

        # Takes the grid coordinates and snaps them to world tile center.
        row, col = grid_pos
        return (row * TILE_SIZE + TILE_SIZE // 2,
                col * TILE_SIZE + TILE_SIZE // 2)

    # Called: find_path()
    def _nearest_walkable(self, grid_pos, tile_radius = 1):

        # Does BFS to all tiles till it finds one closser to target coordinates.
        from collections import deque
        visited = {grid_pos}
        queue = deque([grid_pos])

        while queue:
            print(f"[_nearest_walkable] grid_pos={grid_pos}, tile_radius={tile_radius}")
            r, c = queue.popleft()
            # check all tiles creature would occupy
            fits = all(
                0 <= r+er < self.tilemap.rows and
                0 <= c+ec < self.tilemap.cols and
                self.tilemap.is_walkable(0, r+er, c+ec)
                for er in range(-tile_radius, tile_radius + 1)
                for ec in range(-tile_radius, tile_radius + 1)
            )
            print(f"[_nearest_walkable] starting tile fits immediately: {fits}")
            if fits:
                return (r, c)

            for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]:
                nr, nc = r + dr, c + dc
                if (0 <= nr < self.tilemap.rows and
                    0 <= nc < self.tilemap.cols and
                    (nr,nc) not in visited):
                    visited.add((nr,nc))
                    queue.append((nr,nc))

        return None

    # Called: find_path()
    def _heuristic(self, a, b):

        # Euclidean distance
        return math.hypot(a[0] - b[0], a[1] - b[1])

    # Called: find_path()
    def _reconstruct(self, came_from, current):

        # If came_from is empty return enpty list.
        if not came_from:
            return []

        # Reverses the current path.
        raw = []
        while current in came_from:
            raw.append(current)
            current = came_from[current]
        raw.reverse()

        # Convert directly to grid tile centers — no diagonal splitting
        return [self._snap_to_tile_center(grid_pos) for grid_pos in raw]

    # Called: find_path()
    def _neighbors(self, row, col, tile_radius = 1):

        # Calculates and returns all neighboring tiles that can host the creature if it moves there.
        dirs = [(-1,0),(1,0),(0,-1),(0,1),(-1,-1),(-1,1),(1,-1),(1,1)]
        result = []
        for dr, dc in dirs:

            r, c = row + dr, col + dc

            if not (0 <= r < self.tilemap.rows and 0 <= c < self.tilemap.cols):
                continue

            # Check all tiles the creature would occupy at this position.
            fits = True
            for er in range(-tile_radius, tile_radius + 1):
                for ec in range(-tile_radius, tile_radius + 1):

                    cr, cc = r + er, c + ec

                    if not (0 <= cr < self.tilemap.rows and 0 <= cc < self.tilemap.cols):
                        fits = False
                        break

                    if not self.tilemap.is_walkable(tile_radius, cr, cc):
                        fits = False
                        break

                if not fits:
                    break

            if fits:
                result.append((r, c))

        return result

    # Called: Creature._move_smart()
    def find_path(self, start_world, end_world, tile_radius = 1):

        # A* graph algorythm. Finds a path from creature to the target.
        start = self._to_grid(start_world)
        end   = self._to_grid(end_world)

        # Snapped coordinates.
        snapped_start = self._snap_to_tile_center(start)

        if not self.tilemap.is_walkable(tile_radius, *end):
            end = self._nearest_walkable(end, tile_radius = 0)
            if end is None:
                return []

        snapped_end_tuple = self._snap_to_tile_center(end)

        if start == end:
            return []

        open_set = []
        heapq.heappush(open_set, (0, start))
        came_from = {}
        g_score = {start: 0}
        f_score = {start: self._heuristic(start, end)}

        while open_set:
            _, current = heapq.heappop(open_set)
            if current == end:
                path = self._reconstruct(came_from, current)
                if path:
                    # Insert to path also the snapped position of the creature.
                    path.insert(0, snapped_start)
                path.append(snapped_end_tuple)
                return path
            for neighbor in self._neighbors(*current, tile_radius = tile_radius):
                dr = abs(neighbor[0] - current[0])
                dc = abs(neighbor[1] - current[1])
                step = 1.414 if dr == 1 and dc == 1 else 1.0
                tg = g_score[current] + step
                if tg < g_score.get(neighbor, float("inf")):
                    came_from[neighbor] = current
                    g_score[neighbor]   = tg
                    f_score[neighbor]   = tg + self._heuristic(neighbor, end)
                    heapq.heappush(open_set, (f_score[neighbor], neighbor))

        return []

    # Called: Creature._move_smart()
    def handle_corners(self, start_world, end_world, tile_radius = 1):

        # Casts a DDA ray from all creature footprint tiles to target central tile and checks every tile in between.
        # We do that to check tile absence of obstacles between the target and the creature.
        # Returns the coordinates for the next movement closer to target.
        # None if no line of sight of the footprint exists.

        # Converts world coordinates to grid coordinates.
        start   = self._to_grid(start_world)
        end     = self._to_grid(end_world)

        # work directly in tile space — no world conversion needed
        x0, y0 = float(start[0]), float(start[1])
        x1, y1 = float(end[0]),   float(end[1])

        # Checks all footprint tiles for clear LOS to the target.
        has_sight = None
        min_steps = None

        for er in range(-tile_radius, tile_radius + 1):
            for ec in range(-tile_radius, tile_radius + 1):

                # Check only the footprint tiles that interests us.
                # representing a cross of tiles with center the center of the creature.
                if ((er < x0 or er > x0) and ec == y0) or ((ec < y0 or ec > y0) and er == x0):

                    cr, cc = int(x0 + er), int(y0 + ec)

                    # Calculate the vector and the steps to check (every tile once).
                    dx = x1 - cr
                    dy = y1 - cc
                    steps = int(max(abs(dx), abs(dy)))
                    if steps == 0:
                        return (cr,cc)

                    beem_cleared = True
                    # For all the beem steps check.
                    for i in range(steps + 1):

                        t = i / steps
                        x = cr + dx * t
                        y = cc + dy * t

                        # Because of t earlier we need to return to integer values.
                        center_r = int(y)
                        center_c = int(x)

                        # Check if the tile in question is within or out of the map range.
                        if not (0 <= center_r < self.tilemap.rows and
                            0 <= center_c < self.tilemap.cols):
                            beem_cleared = False
                            break

                        if not self.tilemap.is_walkable( -1, center_r, center_c):
                            beem_cleared = False
                            break

                    # If line of sight and min_steps not init or coordinates with lower steps exist.
                    if beem_cleared and (not min_steps or steps < min_steps):
                        has_sight = (cr,cc)
                        min_steps = steps

        return self._snap_to_tile_center(has_sight)

    # Called: Creature._move_smart()
    def collision_handle(self, start_world, tile_radius = 1):

        # Converts world coordinates to grid coordinates.
        start   = self._to_grid(start_world)
        print(f"[collision_handle] start_world={start_world} → grid={start}, tile_radius={tile_radius}")
        nearest = self._nearest_walkable(start, tile_radius)
        print(f"[collision_handle] nearest={nearest}")
        if nearest is None:
            return None
        result = self._snap_to_tile_center(nearest)
        print(f"[collision_handle] snapped result={result}")
        return result

    # Called: Creature._move_smart()
    def move_to_target(self, start_world, end_world, tile_radius = 1):

        # Calculates and returns the closest footprint coordinates to the target.

        # Converts world coordinates to grid coordinates.
        start   = self._to_grid(start_world)
        end     = self._to_grid(end_world)

        # Calculate distance to target.
        original_dist = self._heuristic(start, end)

        print(f"Start coordinates: ({start[0]}, {start[1]}).")
        print(f"End   coordinates: ({end[0]}, {end[1]}).")
        print(f"distance         : {original_dist}.")

        closer_coordinates = start
        min_distance = original_dist

        # For all footprint tiles of creature.
        for er in range(start[0] - tile_radius, start[0] + tile_radius + 1):
            for ec in range(start[1] - tile_radius, start[1] + tile_radius + 1):

                # Calculate distance.
                distance = self._heuristic((er, ec), end)

                # In move_to_target — always use raw grid, same as player movement
                footprint_clear = all(
                    0 <= er+fr < self.tilemap.rows and
                    0 <= ec+fc < self.tilemap.cols and
                    self.tilemap.is_walkable(0, er+fr, ec+fc)
                    for fr in range(-tile_radius, tile_radius + 1)
                    for fc in range(-tile_radius, tile_radius + 1)
                )
                if not footprint_clear:
                    continue

                # Check if coordinates distance is closer.
                if distance < min_distance:
                    closer_coordinates = (er, ec)
                    min_distance = distance

        return self._snap_to_tile_center(closer_coordinates)

    # Called: Creature._move_smart()
    def line_of_sight( self, start_world, end_world, tile_radius = 1):

        # Casts a beem from creatures tile center to targets tile center.

        # Converts world coordinates to grid coordinates.
        start   = self._to_grid(start_world)
        end     = self._to_grid(end_world)

        print(f"[LOS] start_world={start_world} → grid={start} → tile_value={self.tilemap.original_grid[start[0]][start[1]]}")

        # work directly in tile space — no world conversion needed
        x0, y0 = float(start[0]), float(start[1])
        x1, y1 = float(end[0]),   float(end[1])

        # Calculate coordinate differences and steps to check from creature to target.
        dx = x1 - x0
        dy = y1 - y0
        steps = int(max(abs(dx), abs(dy)))
        if steps == 0:
            return True

        # Cast multiple parallel rays spanning the creature's full width.
        # All rays must be clear for LOS to be true.
        offsets = range(-tile_radius, tile_radius + 1)

        for offset in offsets:

            # Offset perpendicular to the ray direction.
            # If ray is mostly horizontal offset in y, if mostly vertical offset in x.
            if abs(dx) >= abs(dy):
                ox, oy = 0, offset  # mostly horizontal ray → offset vertically
            else:
                ox, oy = offset, 0  # mostly vertical ray → offset horizontally

            ray_clear = True

            # Skip the first and last tile_radius steps for offset rays
            # so bushes beside the endpoints don't falsely block LOS
            start_i = 1 if offset == 0 else tile_radius + 1
            end_i   = steps if offset == 0 else steps - tile_radius

            # For all the beem steps check.
            for i in range(start_i, end_i):

                t = i / steps
                x = x0 + dx * t
                y = y0 + dy * t

                # Because of t earlier we need to return to integer values.
                center_r = int(round(x))
                center_c = int(round(y))

                # Check if the tile in question is within or out of map range.
                if not (0 <= center_r < self.tilemap.rows and
                    0 <= center_c < self.tilemap.cols):
                    ray_clear = False
                    break

                # Center ray uses raw grid — only actual bush tiles block
                # Offset rays use occupied_grid_1 — detects clusters
                grid_to_check = -1 if offset == 0 else 0

                if not self.tilemap.is_walkable(grid_to_check, center_r, center_c):
                    ray_clear = False
                    break

            if not ray_clear:
                return False

        return True

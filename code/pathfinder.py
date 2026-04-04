import heapq
import math
from settings import TILE_SIZE

class Pathfinder:

    def __init__(self, tilemap):

        self.tilemap = tilemap

    # Called: find_path(), line_of_sight().
    def _to_grid(self, world_pos):

        # Convert and returns world coordinates to grid coordinates.
        row = int(world_pos[0] / TILE_SIZE)
        col = int(world_pos[1] / TILE_SIZE)
        row = max(0, min(row, self.tilemap.rows - 1))
        col = max(0, min(col, self.tilemap.cols - 1))
        return (row, col)

    # Called: _reconstruct(), find_path(), line_of_sight().
    def _snap_to_tile_center(self, grid_pos):

        # If position is none returns none.
        if not grid_pos:
            return grid_pos

        # Takes the grid coordinates and snaps them to world tile center.
        row, col = grid_pos
        return (row * TILE_SIZE + TILE_SIZE // 2,
                col * TILE_SIZE + TILE_SIZE // 2)

    # Called: find_path(), collision_handle().
    def _nearest_walkable(self, grid_pos, tile_radius = 1, dynamic_blocked = None):

        # Does BFS to all tiles till it finds one closser to target coordinates.
        from collections import deque
        visited = {grid_pos}
        queue = deque([grid_pos])

        while queue:

            r, c = queue.popleft()

            # check all tiles creature would occupy
            fits = all(
                0 <= r+er < self.tilemap.rows and
                0 <= c+ec < self.tilemap.cols and
                self.tilemap.is_walkable(r+er, c+ec)
                for er in range(-tile_radius, tile_radius + 1)
                for ec in range(-tile_radius, tile_radius + 1)
            )

            # Check precomputed hitbox grid.
            if fits and self.tilemap.hitbox_blocked and self.tilemap.hitbox_blocked[r][c]:
                    fits = False

            # Check dynamic creature positions.
            if fits and dynamic_blocked and (r, c) in dynamic_blocked:
                fits = False

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
    def _neighbors(self, row, col, tile_radius = 1, dynamic_blocked = None):

        # Calculates and returns all neighboring tiles that can host the creature if it moves there.
        dirs = [(-1,0),(1,0),(0,-1),(0,1),(-1,-1),(-1,1),(1,-1),(1,1)]
        result = []

        for dr, dc in dirs:

            r, c = row + dr, col + dc

            if not (0 <= r < self.tilemap.rows and 0 <= c < self.tilemap.cols):
                continue

            # Center tile must not be a bush.
            if not self.tilemap.is_walkable(r, c):
                continue

            # Precomputed hitbox check — O(1) lookup instead of per-frame rect collision.
            if self.tilemap.hitbox_blocked and self.tilemap.hitbox_blocked[r][c]:
                    continue

            if dynamic_blocked and (r, c) in dynamic_blocked:
                continue

            result.append((r, c))

        return result


    # Called: Creature._move_smart()
    def find_path(self, start_world, end_world, tile_radius = 1, dynamic_blocked = None):

        # A* graph algorythm. Finds a path from creature to the target.
        start = self._to_grid(start_world)
        end   = self._to_grid(end_world)

        # Snapped coordinates.
        snapped_start = self._snap_to_tile_center(start)

        # Always find nearest reachable tile to end — regardless of whether end is walkable
        # This ensures we never try to pathfind to an unreachable destination
        reachable_end = self._nearest_walkable(end, tile_radius = tile_radius, dynamic_blocked = dynamic_blocked)
        if reachable_end is None:
            return []
        end = reachable_end

        # If end tile is hitbox-blocked, find nearest reachable tile.
        if self.tilemap.hitbox_blocked and self.tilemap.hitbox_blocked[end[0]][end[1]]:
            end = self._nearest_walkable(end, tile_radius = tile_radius, dynamic_blocked = dynamic_blocked)
            if end is None:
                return []

        snapped_end_tuple = self._snap_to_tile_center(end)

        if start == end:
            return []

        if not self._neighbors(*start, tile_radius = tile_radius, dynamic_blocked = dynamic_blocked):
            nearest = self._nearest_walkable(start, tile_radius = tile_radius, dynamic_blocked = dynamic_blocked)
            if nearest is None:
                return []
            return [snapped_start, self._snap_to_tile_center(nearest)]

        # If end has no neighbors it is surrounded — find nearest reachable instead.
        if not self._neighbors(*end, tile_radius = tile_radius, dynamic_blocked = dynamic_blocked):
            end = self._nearest_walkable(end, tile_radius = tile_radius, dynamic_blocked = None)
            if end is None:
                return []
            snapped_end_tuple = self._snap_to_tile_center(end)

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
            for neighbor in self._neighbors(*current, tile_radius = tile_radius, dynamic_blocked = dynamic_blocked):
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
    def collision_handle(self, start_world, tile_radius = 1):

        # Converts world coordinates to grid coordinates.
        start   = self._to_grid(start_world)

        nearest = self._nearest_walkable(start, tile_radius)

        if nearest is None:
            return None

        return self._snap_to_tile_center(nearest)

    # Called: Creature._move_smart()
    def move_to_target(self, start_world, end_world, tile_radius = 1):

        # Calculates and returns the closest footprint coordinates to the target.

        # Converts world coordinates to grid coordinates.
        start   = self._to_grid(start_world)
        end     = self._to_grid(end_world)

        # Calculate distance to target.
        original_dist = self._heuristic(start, end)

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
                    self.tilemap.is_walkable(er+fr, ec+fc)
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
    def line_of_sight( self, start_world, end_world, tile_radius = 1, neighbors = None):

        # Casts a beem from creatures tile center to targets tile center.

        # Converts world coordinates to grid coordinates.
        start   = self._to_grid(start_world)
        end     = self._to_grid(end_world)

        # work directly in tile space — no world conversion needed
        x0, y0 = float(start[0]), float(start[1])
        x1, y1 = float(end[0]),   float(end[1])

        # Calculate coordinate differences and steps to check from creature to target.
        dx = x1 - x0
        dy = y1 - y0
        steps = int(max(abs(dx), abs(dy)))
        if steps == 0:
            return True

        # For all the beem steps check.
        for i in range(1, steps):

            t = i / steps

            # Because of t earlier we need to return to integer values.
            center_r = int(round(x0 + dx * t))
            center_c = int(round(y0 + dy * t))

            # Check if the tile in question is within or out of map range.
            if not (0 <= center_r < self.tilemap.rows and
                0 <= center_c < self.tilemap.cols):
                    continue

            if not self.tilemap.is_walkable(center_r, center_c):
                return False

            # Block if ray passes through hitbox-blocked zone
            # (creature body would overlap a bush if standing here)
            if self.tilemap.hitbox_blocked and self.tilemap.hitbox_blocked[center_r][center_c]:
                return False

            # Block if a neighbor creature occupies this tile.
            if neighbors:
                world_x = center_r * TILE_SIZE + TILE_SIZE // 2
                world_y = center_c * TILE_SIZE + TILE_SIZE // 2
                if any(
                    math.hypot(world_x - n.rect.centerx,
                                world_y - n.rect.centery) < TILE_SIZE
                    for n in neighbors
                ):
                    return False

        return True

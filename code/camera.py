import pygame
import math

class YSortCameraGroup(pygame.sprite.Group):

    # Called: Indie_Game.__init__().
    def __init__(self, screen, tile_size, map_w, map_h):
        super().__init__()

        self.screen     = screen
        self.tile_size  = tile_size
        self.map_w      = map_w
        self.map_h      = map_h

        self.screen_w = screen.get_width()
        self.screen_h = screen.get_height()

        self._rad   = 0.0
        self._cos_a = 1.0
        self._sin_a = 0.0

        self.terrain_grid   = None   # Is set by level later.
        self.grass_tileset  = []
        self.offset         = pygame.math.Vector2(0, 0)
        self.angle          = 0.0   # Current world rotation in degrees.
        self._last_angle    = 0.0
        self._player        = None

        self._sprite_rot_cache = {}

        # Now the we only calculate the initial screen
        self._world_surf = pygame.Surface((self.screen_w, self.screen_h), pygame.SRCALPHA)

    # Called: custom_draw()
    def update_camera(self):

        self.offset.x = self._player.rect.centerx - self.screen_w // 2
        self.offset.y = self._player.rect.centery - self.screen_h // 2

        if self.angle == 0.0:

            self.offset.x = max(0, min(self.offset.x, self.map_w - self.screen_w))
            self.offset.y = max(0, min(self.offset.y, self.map_h - self.screen_w))

    # Called: custom_draw()
    def _rotated_y(self, sprite, player_cx, player_cy):

        if self.angle == 0.0:
            return sprite.rect.bottom

        dx = sprite.rect.centerx - player_cx
        dy = sprite.rect.bottom - player_cy

        return dx * self._sin_a + dy * self._cos_a

    # Called: custom_draw()
    def _draw_world(self, surface, offset):

        sw = surface.get_width()
        sh = surface.get_height()

        start_x = int(offset.x // self.tile_size) * self.tile_size
        start_y = int(offset.y // self.tile_size) * self.tile_size
        end_x   = int(offset.x + sw) + self.tile_size
        end_y   = int(offset.y + sh) + self.tile_size

        # Draw ground tiles.
        for y in range(start_y, end_y, self.tile_size):
            for x in range(start_x, end_x, self.tile_size):

                col = x // self.tile_size
                row = y // self.tile_size

                if 0 <= col < len(self.terrain_grid) and 0 <= row < len(self.terrain_grid[0]):
                    tile_id = self.terrain_grid[col][row]
                else:
                    tile_id = 25

                surface.blit(self.grass_tileset[tile_id], (
                    x - int(offset.x),
                    y - int(offset.y)
                ))

        player_cx = self._player.rect.centerx if self._player else 0
        player_cy = self._player.rect.centery if self._player else 0

        # Draw sprites sorted by y (painter's algorithm).
        for sprite in sorted(self.sprites(), key = lambda s: self._rotated_y(s, player_cx, player_cy)):
            if self.angle != 0.0 :#and not isinstance(sprite, Bush):

                key = (self.angle, id(sprite), id(sprite.image))
                if key not in self._sprite_rot_cache:
                    if len(self._sprite_rot_cache) > 20000:
                        self._sprite_rot_cache.clear()
                    self._sprite_rot_cache[key] = pygame.transform.rotate(sprite.image, self.angle)
                rotated_img = self._sprite_rot_cache[key]

                # Keep the sprite centered on its world position after rotation.
                rx = sprite.rect.centerx - int(offset.x) - rotated_img.get_width()  // 2
                ry = sprite.rect.centery - int(offset.y) - rotated_img.get_height() // 2
                surface.blit(rotated_img, (rx, ry))

            else:

                surface.blit(sprite.image, (
                    sprite.rect.x - int(offset.x),
                    sprite.rect.y - int(offset.y)
                ))

    # Called: custom_draw(), screen_to_world(), world_to_screen().
    def _basic_calc(self):

        if self.angle != self._last_angle:

            self._last_angle = self.angle
            self._rad   = math.radians(self.angle)
            self._cos_a = math.cos(self._rad)
            self._sin_a = math.sin(self._rad)

    # Called: Indie_Game._draw()
    def custom_draw(self, player):

        self._player = player
        self.update_camera()

        if self.angle == 0.0:

            # Fast path — no rotation, draw directly to screen.
            self._draw_world(self.screen, self.offset)

        else:

            self.screen.fill((0, 0, 0))

            self._basic_calc()

            needed_w = int(self.screen_w * abs(self._cos_a) + self.screen_h * abs(self._sin_a)) + 2
            needed_h = int(self.screen_w * abs(self._sin_a) + self.screen_h * abs(self._cos_a)) + 2

            if self._world_surf.get_width() != needed_w or self._world_surf.get_height() != needed_h:
                self._world_surf = pygame.Surface((needed_w, needed_h), pygame.SRCALPHA)

            # Offset so the player appears at the center of world_surf.
            surf_offset = pygame.math.Vector2(
                player.rect.centerx - needed_w // 2,
                player.rect.centery - needed_h // 2
            )

            self._world_surf.fill((0, 0, 0, 0))
            self._draw_world(self._world_surf, surf_offset)

            # Rotate the offscreen surface around its center.
            rotated = pygame.transform.rotate(self._world_surf, -self.angle)

            # Blit centered on the player's screen position.
            player_screen_x = player.rect.centerx - int(self.offset.x)
            player_screen_y = player.rect.centery - int(self.offset.y)
            blit_x = player_screen_x - rotated.get_width()  // 2
            blit_y = player_screen_y - rotated.get_height() // 2
            self.screen.blit(rotated, (blit_x, blit_y))

    # Called: Indie_Game._handle_events().
    def screen_to_world(self, screen_x, screen_y, player):

        if self.angle == 0.0:
            return (
                screen_x + self.offset.x,
                screen_y + self.offset.y
            )

        # Player's position on screen (unrotated).
        player_screen_x = player.rect.centerx - int(self.offset.x)
        player_screen_y = player.rect.centery - int(self.offset.y)

        # Vector from player screen pos to clicked screen pos.
        dx = screen_x - player_screen_x
        dy = screen_y - player_screen_y

        self._basic_calc()

        world_dx =  dx * self._cos_a + dy * self._sin_a
        world_dy = -dx * self._sin_a + dy * self._cos_a

        return (
            player.rect.centerx + world_dx,
            player.rect.centery + world_dy
        )

    # Called: UIManager._draw_hp_bars(), DamageNumber.draw().
    def world_to_screen(self, world_x, world_y, player):

        if self.angle == 0.0:
            return (
                world_x - self.offset.x,
                world_y - self.offset.y
            )

        # Vector from player world pos to point in world space.
        dx = world_x - player.rect.centerx
        dy = world_y - player.rect.centery

        self._basic_calc()

        screen_dx = dx * self._cos_a - dy * self._sin_a
        screen_dy = dx * self._sin_a + dy * self._cos_a

        # Player's screen position.
        player_screen_x = player.rect.centerx - self.offset.x
        player_screen_y = player.rect.centery - self.offset.y

        return (
            player_screen_x + screen_dx,
            player_screen_y + screen_dy
        )

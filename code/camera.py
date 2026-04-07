import pygame
import math

from bush import Bush

class YSortCameraGroup(pygame.sprite.Group):

    # Called: Indie_Game.__init__().
    def __init__(self, screen, tile_size, map_w, map_h):
        super().__init__()

        self.screen     = screen
        self.tile_size  = tile_size
        self.map_w      = map_w
        self.map_h      = map_h

        self.ground     = None   # Is set by level later.
        self.offset     = pygame.math.Vector2(0, 0)
        self.angle      = 0.0   # Current world rotation in degrees.
        self._player    = None

        # Offscreen surface — large enough to cover screen at any rotation angle.
        # The diagonal of the screen is the maximum extent needed.
        sw = screen.get_width()
        sh = screen.get_height()
        diag = int(math.hypot(sw, sh)) + tile_size * 2
        self._world_surf = pygame.Surface((diag, diag), pygame.SRCALPHA)


    # Called: custom_draw()
    def update_camera(self, player):

        self.offset.x = player.rect.centerx - self.half_w
        self.offset.y = player.rect.centery - self.half_h

        if self.angle == 0.0:

            self.offset.x = max(0, min(self.offset.x, self.map_w - self.screen.get_width()))
            self.offset.y = max(0, min(self.offset.y, self.map_h - self.screen.get_height()))

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
                surface.blit(self.ground, (
                    x - int(offset.x),
                    y - int(offset.y)
                ))

        player_cx = self._player.rect.centerx if self._player else 0
        player_cy = self._player.rect.centery if self._player else 0

        # Called: custom_draw()
        def _rotated_y(sprite):

            if self.angle == 0.0:
                return sprite.rect.bottom

            rad = math.radians(self.angle)
            cos_a = math.cos(rad)
            sin_a = math.sin(rad)
            dx = sprite.rect.centerx - player_cx
            dy = sprite.rect.bottom - player_cy
            return dx * sin_a + dy * cos_a

        # Draw sprites sorted by y (painter's algorithm).
        for sprite in sorted(self.sprites(), key = _rotated_y):
            if self.angle != 0.0 and not isinstance(sprite, Bush):

                rotated_img = pygame.transform.rotate(sprite.image, self.angle)
                # Keep the sprite centered on its world position after rotation.
                rx = sprite.rect.centerx - int(offset.x) - rotated_img.get_width()  // 2
                ry = sprite.rect.centery - int(offset.y) - rotated_img.get_height() // 2
                surface.blit(rotated_img, (rx, ry))

            else:

                surface.blit(sprite.image, (
                    sprite.rect.x - int(offset.x),
                    sprite.rect.y - int(offset.y)
                ))

    # Called: Indie_Game._draw()
    def custom_draw(self, player):

        self._player = player
        self.update_camera(player)

        if self.angle == 0.0:

            # Fast path — no rotation, draw directly to screen.
            self._draw_world(self.screen, self.offset)

        else:

            # Draw world onto offscreen surface centered on the player.
            sw = self._world_surf.get_width()
            sh = self._world_surf.get_height()

            # Offset so the player appears at the center of world_surf.
            surf_offset = pygame.math.Vector2(
                player.rect.centerx - sw // 2,
                player.rect.centery - sh // 2
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

        # Rotate that vector by -angle to get back to world space.
        rad = math.radians(self.angle)
        cos_a = math.cos(rad)
        sin_a = math.sin(rad)
        world_dx =  dx * cos_a + dy * sin_a
        world_dy = -dx * sin_a + dy * cos_a

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

        # Rotate by -angle (opposite of screen_to_world).
        rad = math.radians(self.angle)
        cos_a = math.cos(rad)
        sin_a = math.sin(rad)
        screen_dx = dx * cos_a - dy * sin_a
        screen_dy = dx * sin_a + dy * cos_a

        # Player's screen position.
        player_screen_x = player.rect.centerx - self.offset.x
        player_screen_y = player.rect.centery - self.offset.y

        return (
            player_screen_x + screen_dx,
            player_screen_y + screen_dy
        )

    # Called: YSortCameraGroup.update_camera().
    @property
    def half_w(self):

        return self.screen.get_width() // 2

    # Called: YSortCameraGroup.update_camera().
    @property
    def half_h(self):

        return self.screen.get_height() // 2

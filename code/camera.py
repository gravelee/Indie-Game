import pygame

class YSortCameraGroup(pygame.sprite.Group):

    # Called: Indie_Game.__init__().
    def __init__(self, screen, tile_size, map_w, map_h):
        super().__init__()

        self.screen    = screen
        self.tile_size = tile_size
        self.map_w     = map_w
        self.map_h     = map_h

        self.ground    = None   # Is set by level later.
        self.offset    = pygame.math.Vector2(0, 0)


    # Called: custom_draw()
    def update_camera(self, player):

        self.offset.x = player.rect.centerx - self.half_w
        self.offset.y = player.rect.centery - self.half_h

        self.offset.x = max(0, min(self.offset.x, self.map_w - self.screen.get_width()))
        self.offset.y = max(0, min(self.offset.y, self.map_h - self.screen.get_height()))

    # Called: Indie_Game._draw()
    def custom_draw(self, player):

        self.update_camera(player)

        start_x = int(self.offset.x // self.tile_size) * self.tile_size
        start_y = int(self.offset.y // self.tile_size) * self.tile_size
        end_x   = int(self.offset.x + self.screen.get_width())  + self.tile_size
        end_y   = int(self.offset.y + self.screen.get_height()) + self.tile_size

        for y in range(start_y, end_y, self.tile_size):
            for x in range(start_x, end_x, self.tile_size):
                self.screen.blit(self.ground, (
                    x - int(self.offset.x),
                    y - int(self.offset.y)
                ))

        for sprite in sorted(self.sprites(), key=lambda s: s.rect.centery):
            self.screen.blit(sprite.image, (
                sprite.rect.x - int(self.offset.x),
                sprite.rect.y - int(self.offset.y)
            ))


    # Called: YSortCameraGroup.update_camera().
    @property
    def half_w(self):

        return self.screen.get_width() // 2

    # Called: YSortCameraGroup.update_camera().
    @property
    def half_h(self):

        return self.screen.get_height() // 2

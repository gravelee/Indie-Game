import pygame
from settings import TILE_SIZE,SPRITE_SCALE

class Bush(pygame.sprite.Sprite):

    _IMG = "../assets/sprites/objects/bush/bush.png"


    def __init__(self, x, y, tilemap, *groups):
        super().__init__(*groups)

        raw_image = pygame.image.load(self._IMG).convert_alpha()
        self.image = pygame.transform.scale(raw_image, (TILE_SIZE*SPRITE_SCALE, TILE_SIZE*SPRITE_SCALE))

        self.rect           = self.image.get_rect(topleft=(x, y))
        self.tilemap        = tilemap
        self.hitbox         = self.rect.inflate(-30, -30)
        self.alive          = True
        self.tile_radius    = SPRITE_SCALE // 2

    # Called: Player.attack()
    def take_hit(self):

        self.alive = False
        # Updates the tilemap.
        self.tilemap.update_tilemap(self.rect.centerx, self.rect.centery)

        self.kill()

    # Called: UIManager._draw_hp_bars()
    @property
    def is_alive(self):
        return self.alive

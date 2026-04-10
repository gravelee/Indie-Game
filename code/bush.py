import pygame
from utils      import SpriteSheet
from settings   import TILE_SIZE, SPRITE_SCALE, ANIM_SPEED

class Bush(pygame.sprite.Sprite):

    _IMG        = "../assets/sprites/objects/bush/bush.png"
    _DEATH_IMG  = "../assets/sprites/objects/bush/death.png"


    def __init__(self, x, y, tilemap, *groups):
        super().__init__(*groups)

        # ── static idle image ──────────────────────────────────
        raw_image = pygame.image.load(self._IMG).convert_alpha()
        self.image = pygame.transform.scale(raw_image, (TILE_SIZE*SPRITE_SCALE, TILE_SIZE*SPRITE_SCALE))

        # ── death animation frames ─────────────────────────────
        raw_frames      = SpriteSheet(self._DEATH_IMG, 64, 64).get_all_frames()
        self._death_frames = [
            pygame.transform.scale(f, (TILE_SIZE * SPRITE_SCALE, TILE_SIZE * SPRITE_SCALE))
            for f in raw_frames
        ]

        self.rect           = self.image.get_rect(topleft = (x, y))
        self.tilemap        = tilemap
        self.hitbox         = self.rect.inflate(-30, -30)
        self.alive          = True
        self.tile_radius    = SPRITE_SCALE // 2

        # ── animation state ────────────────────────────────────
        self._frame_index   = 0
        self._anim_timer    = 0.0

    # Called: Indie_Game._update()
    def update(self, dt):

        if self.alive:
            return

        self._anim_timer += dt
        if self._anim_timer >= ANIM_SPEED:
            self._anim_timer = 0.0
            self._frame_index += 1

            # Animation finished — remove from all groups.
            if self._frame_index >= len(self._death_frames):
                self.kill()
                return

            self.image = self._death_frames[self._frame_index]

    # Called: Player.attack()
    def take_hit(self):

        self.alive = False
        self._frame_index = 0
        self._anim_timer  = 0.0
        self.image = self._death_frames[0]

        # Remove self from the tilemap's obstacle list before rebuilding
        # the hitbox grid — otherwise the dead bush still blocks the tile.
        if self.tilemap.obstacles is not None:
            self.tilemap.obstacles[:] = [o for o in self.tilemap.obstacles if o is not self]

        # Updates the obstacle hash.
        if hasattr(self, 'remove_from_hash'):
            self.remove_from_hash(self)

        # Updates hitbox grid.
        self.tilemap.update_hitbox_grid(self)

        # Updates original grid.
        self.tilemap.update_original_grid(self.rect.centerx, self.rect.centery)


    # Called: UIManager._draw_hp_bars()
    @property
    def is_alive(self):
        return self.alive

import pygame
import math
from utils          import SpriteSheet
from status_effect  import EffectManager
from ability        import get_ability
from settings       import (
    SPRITE_SCALE,HP_REGEN, ENERGY_REGEN, RAGE_DECREASE)

class Entity(pygame.sprite.Sprite):

    _BASE               = "../assets/sprites/creatures/"
    _ANIM_FILES         = {}

    def __init__(self, x, y, stats, *groups):
        super().__init__(*groups)

        #   Entity coordinates
        self.pos_x = float(x)
        self.pos_y = float(y)

        #   Entity Stats, Abilities, Effects
        self.stats = stats
        self.abilities    = []
        for ability in self.ATTACKS:
            self.abilities.append(get_ability(ability, self.stats._calc_level()))
        self.effects = EffectManager()

        #   Entity State, Direction
        self.state          = "idle_neutral"
        self.target         = None
        self.target_dist    = 0.0
        self.in_combat      = False
        self.facing_right   = False
        self.corpse_alpha   = 255

        #   Animation, cooldown
        self.frame_index    = 0
        self.anim_timer     = 0.0
        self.anim_done      = False
        self.animations     = {}
        self.gcd_timer      = 0.0

        #   Combat UI feedback data
        self.last_hit           = None
        self.last_target        = None
        self.dot_damage         = 0
        self.expired_effects    = []


    # Called: Creaturn.init(), Player.init()
    def _load(self, filename, scale = SPRITE_SCALE):

        frames = SpriteSheet(self._BASE + filename, 32, 32).get_all_frames()
        if scale != 1:
            frames = [pygame.transform.scale(f, (32 * scale, 32 * scale)) for f in frames]
        return frames


    # Called: Creature._update_state(), Creature.attack(), Creature._begin_death(),
    #           Player._update_state(), Player.attack(), Player._begin_death()
    def _set_state(self, new_state):

        if self.state != new_state:
            self.state       = new_state
            self.frame_index = 0
            self.anim_timer  = 0.0
            self.anim_done   = False


    # Called: Creature.attack(), Player.attack()
    def _pick_ability(self, choices):

        # Chooses one ability to use (max damage).
        return max(choices, key=lambda a: a.damage_mult)

    # Called: Creature.attack(), Player.attack()
    def _ready_abilities(self, dist):

        # Collect all usable abilities atm.
        usable = [
            a for a in self.abilities
            if a.can_use(self.stats, dist)
        ]
        if not usable:
            return None
        return usable


    # Called: Creature.update(), Player.update()
    def _regen(self, dt):

        # If entities state is dying skip regen.
        if self.state != "dying":

            # If creatures life is zero and state not dying and not dead.
            if (not self.is_alive):
                self._begin_death()

            # If creature is not in combat regenerate.
            elif not self.in_combat:
                self.stats.energy = min(self.stats.energy_max, self.stats.energy + ENERGY_REGEN * dt)
                self.stats.rage = max(0, self.stats.rage - RAGE_DECREASE * dt)

                self.stats.hp = min(
                    self.stats.hp_max,
                    self.stats.hp + HP_REGEN * dt
                )

        # Updates the damage over time and effects on self.
        self.dot_damage, self.expired_effects = self.effects.update(dt, self.stats)

    #   Called: Creature.update(), Player.update()
    def _update_cooldowns(self, dt):

        # If gcd timer is up update it.
        if self.gcd_timer > 0:
            self.gcd_timer = max(0.0, self.gcd_timer - dt)

        # For every ability that the entity has update their timers.
        for ability in self.abilities:
            ability.tick(dt)

    # Called: Player.update()
    def set_target_dist(self):

        self.target_dist = math.hypot(
            self.target.rect.centerx - self.rect.centerx,
            self.target.rect.centery - self.rect.centery)


    # Called: Creature._begin_death(), Player._begin_death()
    def _begin_death(self):
        pass

    @property
    def is_alive(self):

        return self.stats.is_alive

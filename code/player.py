import pygame
import math

from entity         import Entity
from settings       import (FACING_CONE, ANIM_SPEED, GCD)

class Player(Entity):

    _SUBBASE = "rat/"
    _ANIM_FILES = {
        "idle_neutral" :    "idle_neutral.png",
        "idle_attack"  :    "idle_attack.png",
        "move"         :    "move.png",
        "attack_slash" :    "attack_slash.png",
        "attack_bite"  :    "attack_bite.png",
        "dying"        :    "death.png"
    }

    ATTACKS             = frozenset(("rat_slash", "rat_bite"))
    ABILITY_STATES      = frozenset(("attack_bite","attack_slash"))
    COMBAT_STATES       = frozenset(("idle_attack", "attack_slash", "attack_bite"))
    NON_COMBAT_STATES  = frozenset(("idle_neutral", "move", "dying"))
    ONE_SHOT_STATES     = frozenset(("attack_slash", "attack_bite", "dying"))


    def __init__(self, x, y, stats, *groups):
        super().__init__(x, y, stats, *groups)

        self.enemies = []
        self.obstacles = []
        self.facing_angle = 0.0
        self.stopped = False
        self.player_move_input = False

        self.animations = {k: self._load(self._SUBBASE + v) for k, v in self._ANIM_FILES.items()}
        self.image      = self.animations["idle_neutral"][0]

        self.rect       = self.image.get_rect(topleft = (x, y))
        self.hitbox     = self.rect.inflate(-50, -50)


    # Called: Player.attack()
    def _target_in_cone(self):

        if self.target.state == "dying" or not self.target.is_alive:
            return False

        dx = self.target.rect.centerx - self.rect.centerx
        dy = self.target.rect.centery - self.rect.centery
        dist = math.hypot(dx, dy)

        if not any(a.range_ >= dist for a in self.abilities):
            return False

        angle_to = math.degrees(math.atan2(dy, dx))
        diff = (angle_to - self.facing_angle + 180) % 360 - 180

        return abs(diff) <= FACING_CONE / 2

    # Called: Player.attack()
    def _auto_target(self):

        target      = None
        best_dist   = float("inf")

        # cone origin — edge of sprite in facing direction
        origin_x = self.rect.right if self.facing_right else self.rect.left
        origin_y = self.rect.centery

        for enemy in self.enemies:

            if enemy.state == "dying":
                continue

            dx   = enemy.rect.centerx - origin_x
            dy   = enemy.rect.centery - origin_y
            dist = math.hypot(dx, dy)

            if not any(a.range_ >= dist for a in self.abilities):
                continue

            angle_to = math.degrees(math.atan2(dy, dx))
            diff = (angle_to - self.facing_angle + 180) % 360 - 180

            if abs(diff) <= FACING_CONE / 2:
                if dist < best_dist:
                    best_dist = dist
                    target    = enemy

        return target, best_dist

    # Called: Indie_Game.handle_events()
    def attack(self):

        # If no target, try to find one target within the range of atleast on of your abilities.
        # Enemy should be spoted within a cone in font of you.
        if self.target is None:
            self.target, self.target_dist = self._auto_target()
            # If none is found it return (stops attack)
            if self.target is None:
                return False
        # If you have a target then check if he is in the cone in front of you. If not returns.
        elif not self._target_in_cone():
            return False

        # Check if you are in an one shot animation (bussy). returns False.
        if self.state in self.ONE_SHOT_STATES:
            return False

        # Check if the global cooldown is on. If so returns False.
        if self.gcd_timer > 0:
            return False

        # Get the list of all the abilities that can be triggered (no cooldown) and are in range and costs exist.
        choices = self._ready_abilities(self.target_dist)
        # If the list is empty returns False.
        if choices is None:
            return False

        # You choose an ability (from the list before) based on max damage output.
        ability = self._pick_ability(choices)

        # This is the footprint the outcome of the ability being used.
        result = ability.use(
            self.stats,
            self.target.stats,
            self.target.effects,
            self.target_dist
        )

        # If target creature is in a non combat state he enters immediately.
        if self.target.state in self.NON_COMBAT_STATES:

            # If the creature has an enter stance animation do it else enter idle attack instantly.
            if "enter_stance" in self.target.animations:
                self.target._set_state("enter_stance")
            else:
                self.target._set_state("idle_attack")

        self.gcd_timer   = GCD
        self.last_hit    = result
        self.last_target = self.target

        # Sets the state to the specific ability used.
        self._set_state(ability.anim)

        return True


    # Called: Player.update()
    def _handle_movement(self, dt, bounds):

        # If player is in attack animation continue the animation till it ends.
        if self.state in self.ONE_SHOT_STATES:
            return

        # Calculate player vector by player keyboard input.
        keys = pygame.key.get_pressed()
        dx, dy = 0.0, 0.0

        if keys[pygame.K_w]: dy -= 1
        if keys[pygame.K_s]: dy += 1
        if keys[pygame.K_a]: dx -= 1
        if keys[pygame.K_d]: dx += 1
        dist = (dx**2 + dy**2) ** 0.5

        # If keys are clicked.
        if dist > 0:
            dx /= dist
            dy /= dist

            # Sets facing sprite of player to where he moves.
            self.facing_right = dx > 0 if dx != 0 else self.facing_right

            # updates angle for the cone attack mechanic.
            self.facing_angle = math.degrees(math.atan2(dx,dy))

            # Calculate imaginary hitbox and move it to the direction the player is moving
            # If there is collision do not let the player to move at that direction.
            new_rect_x = round(self.pos_x + dx * self.stats.mspd * dt)
            new_rect_y = round(self.pos_y + dy * self.stats.mspd * dt)
            new_hitbox = self.hitbox.move(new_rect_x - self.rect.x, new_rect_y - self.rect.y)

            # Check if player is blocked by enemy hitbox.
            blocked = any(
                new_hitbox.colliderect(e.hitbox)
                for e in self.enemies
                if e.state != "dead"
            )

            # If player is not blocked by creature hitbox check if player is blocked by obstacles hitbox.
            if not blocked:
                blocked = blocked or any(
                    new_hitbox.colliderect(obs.hitbox)
                    for obs in self.obstacles)

            # If not blocked.
            if not blocked:

                # Calculate new (x,y) based on players movement speed.
                self.pos_x += dx * self.stats.mspd * dt
                self.pos_y += dy * self.stats.mspd * dt

                self.rect.x = round(self.pos_x)
                self.rect.y = round(self.pos_y)

                # If players finds an obsticle he hits it.
                self.rect.clamp_ip(bounds)

                self.pos_x = float(self.rect.x)
                self.pos_y = float(self.rect.y)

                # We set the center of our hitbox to the center of your rect.
                self.hitbox.center = self.rect.center

                # Sets stopped to False
                self.stopped = False

            # If player found collision set stopped to True
            else:
                self.stopped = True

            # Set the move input to true.
            self.player_move_input = True

        # No keyboard input.
        else:
            # Set the move input to false.
            self.player_move_input = False

    # Called: Player.update()
    def _animate(self, dt):

        if self.state not in self.animations and self.state != "dying":
            self._set_state("idle_neutral")

        frames = self.animations[self.state]

        if self.frame_index >= len(frames):
            self.frame_index = 0

        self.anim_timer += dt
        if self.anim_timer >= ANIM_SPEED:
            self.anim_timer = 0.0
            if self.state in self.ONE_SHOT_STATES:
                if self.frame_index < len(frames) - 1:
                    self.frame_index += 1
                else:
                    if self.state != "dying":
                        self.state     = "idle_neutral"
                    self.anim_done = True
                    self.frame_index = 0
            else:
                self.frame_index = (self.frame_index + 1) % len(frames)

        self.image = pygame.transform.flip(
            frames[self.frame_index], self.facing_right, False
        )

    # Called: Player.update()
    def _update_state(self, dt):

        # If player in idle neutral state.
        if self.state == "idle_neutral":
            # If player move input True and player found no collision.
            if self.player_move_input and not self.stopped:
                self._set_state("move")
            # If player is in combat.
            elif self.in_combat:
                self._set_state("idle_attack")

        # If player in idle attack state.
        elif self.state == "idle_attack":
            # If player move input True and player found no collision.
            if self.player_move_input and not self.stopped:
                # Set player state to move.
                self._set_state("move")
            elif not self.in_combat:
                self._set_state("idle_neutral")

        # If player in move state.
        elif self.state == "move":
            # If found collision and player in combat.
            if self.stopped and self.in_combat:
                # Set player state to idle attack.
                self._set_state("idle_attack")
            # If found collision player not in combat.
            elif self.stopped:
                # Set player state to idle neutral.
                self._set_state("idle_neutral")
            # If no collision and no player input.
            elif not self.player_move_input:
                # Set player state to idle neutral.
                self._set_state("idle_neutral")

        # If player in ability states.
        elif self.state in self.ABILITY_STATES:
            # Ability animation has played.
            if self.anim_done:
                # Set player state to idle attack.
                self._set_state("idle_attack")

        # If player in dying state.
        elif self.state == "dying":
            # Dying animation has played.
            if self.anim_done:
                # Set player state to dead.
                self._set_state("dead")

        # If player in dead state.
        elif self.state == "dead":
            # Start fading the corpse.
            self.corpse_alpha = max(0, self.corpse_alpha - 300 * dt)
            self.image.set_alpha(int(self.corpse_alpha))
            if self.corpse_alpha <= 0:
                self.kill()

    # Called: Player.update()
    def _update_combat(self):

        # For every creature in the level check if any is in combat and if so so are you.
        self.in_combat = self.enemies and any(
            c.state in c.COMBAT_STATES
            for c in self.enemies
        )

    # Called: Indie_Game.update()
    def update(self, dt, bounds = None):

        if self.state != "dead":

            if bounds:
                self._handle_movement(dt, bounds)   # Player
            if self.target:
                self.set_target_dist()              # Entity

            self._animate(dt)                       # Player
            self._regen(dt)                         # Entity

        self._update_state(dt)                      # Player
        self._update_cooldowns(dt)                  # Entity
        self._update_combat()                       # Player


    # Called: Entity._regen()
    def _begin_death(self):

        # Clean effects to show no data on screen
        self.effects.cleanse_all(self.stats)

        # clear players target.
        self.target         = None
        self.in_combat      = False
        self.target_dist    = 0.0

        # Creature enters dying state.
        self._set_state("dying")

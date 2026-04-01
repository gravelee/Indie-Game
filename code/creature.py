import pygame
import random
import math

from entity         import Entity
from settings       import (ANIM_SPEED, TILE_SIZE, NOTICE_COOLDOWN, GCD, SPRITE_SCALE)

class Creature(Entity):

    ATTACKS             = frozenset()
    ABILITY_STATES      = frozenset()
    COMBAT_STATES       = frozenset()
    NON_COMBAT_STATES   = frozenset()
    ONE_SHOT_STATES     = frozenset()

    def __init__(self, x, y, stats, player, home_position = None, returning = False, fleeing = False, *groups):
        super().__init__(x, y, stats, *groups)

        # Basic attr
        self.target             = player
        self.obstacles          = []
        self.last_target        = player
        self.home_position      = home_position
        self.temp_home          = False
        self.returning          = returning
        self.fleeing            = fleeing
        self.home_max_dist      = 0
        self.out_of_energy      = False
        self.notice_cooldown    = NOTICE_COOLDOWN

        # Wander attr
        self.wander_timer           = random.uniform(0, 1.0)
        self.wander_interval_range  = (0.9, 1.1)
        self.wander_interval        = random.uniform(*self.wander_interval_range)
        self.wander_chance          = 0.04
        self.wander_duration        = 0.0
        self.wander_duration_range  = (0.5, 3.0)
        self.wander_elapsed         = 0.0
        self.wander_dx              = 0.0
        self.wander_dy              = 0.0

        # Pathfinder attr
        self.pathfinder     = None      # set by level after spawn
        self.path           = []        # current A* waypoint list
        self.plan                       = None
        self.move_target                = None

        self.neighbors      = []        # nearby creatures for separation — set by level

        self.animations  = {k: self._load(self._SUBBASE + v) for k, v in self._ANIM_FILES.items()}
        self.image = self.animations["idle_neutral"][0]
        self.rect  = self.image.get_rect(topleft = (x, y))
        self.hitbox     = self.rect.inflate(-50, -50)
        self.tile_radius = SPRITE_SCALE // 2


    # Called: Rat._update_state(), Snake._update_state()
    def _distance_to(self, target_rect):

        # It calculates and returns the distance to target (player, home_position).
        dx = self.rect.centerx - target_rect.centerx
        dy = self.rect.centery - target_rect.centery
        return (dx**2 + dy**2) ** 0.5

    # Called: Rat._update_state(),_wander(), Snake._update_state(),_wander()
    def _move_toward(self, dt, target_rect, speed, bounds = None):

        # It calculates the distance to target (player, home_position).
        dx = target_rect.centerx - self.rect.centerx
        dy = target_rect.centery - self.rect.centery
        dist = max((dx**2 + dy**2) ** 0.5, 1)

        # Calculates and updates the new (x,y) position.
        new_x = self.pos_x + (dx / dist) * speed * dt
        new_y = self.pos_y + (dy / dist) * speed * dt

        # Imaginary hitbox if creature moves dt.
        new_hitbox = self.hitbox.move(
            round(new_x) - self.rect.x,
            round(new_y) - self.rect.y
        )

        # If creatures future movement hits the player stops it before moving there.
        if new_hitbox.colliderect(self.target.hitbox):
            return

        # If creatures future movement hits an obstacle stops it before moving there.
        for obs in self.obstacles:
            if new_hitbox.colliderect(obs.hitbox):
                return

        # If nothing of the above set the new coordinates of the creature.
        self.pos_x = new_x
        self.pos_y = new_y
        self.rect.x = round(self.pos_x)
        self.rect.y = round(self.pos_y)
        self.hitbox.center = self.rect.center

        # If creatures movement hits a boundary. Recalculate wander attr.
        if bounds and not bounds.contains(self.rect):

            # If bounds are hit in the x axes change direction 180 degrees.
            if self.rect.left < bounds.left or self.rect.right > bounds.right:
                self.wander_dx = -self.wander_dx
                self.facing_right = self.wander_dx > 0

            # If bounds are hit in the y axes change direction 180 degrees.
            if self.rect.top < bounds.top or self.rect.bottom > bounds.bottom:
                self.wander_dy = -self.wander_dy

            # Recalculate for wander for random time.
            self.wander_elapsed  = 0.0
            self.wander_duration = random.uniform(*self.wander_duration_range)

    # Called: Rat._update_state(), Snake._update_state()
    def _move_smart(self, dt, target_rect, speed, bounds = None):

        from steering import separate

        # Use separation from the other creatures so they do not stuck in a pile.
        #sep_x, sep_y = separate(
        #    self,
        #    self.neighbors,
        #    radius   = 80,
        #    strength = speed * 0.4 * dt
        #)

        # If creature has no plan and no target to move to.
        if not self.plan and not self.move_target:

                # If a path exists.
                if self.path:

                    # First waypoint is reached. Pop it out.
                    self.path.pop(0)

                    # If more waypoints exist.
                    if self.path:
                        self.move_target = pygame.Rect(self.path[0][0], self.path[0][1], 1, 1)

                # If no path to follow.
                else:

                    # Checks if creature has line of sight of the target.
                    line_of_sight = self.pathfinder.line_of_sight(
                        (self.rect.centerx, self.rect.centery),
                        (target_rect.centerx, target_rect.centery),
                        tile_radius = self.tile_radius)

                    # If line of sight.
                    if line_of_sight:
                        self.plan = "move to target"
                    else:
                        self.plan = "collision handle"

        # Creature moves directly to the target rect.
        elif( self.plan == "move to target"):

            # Get the next coordinates to move.
            coordinates = self.pathfinder.move_to_target(
                (self.rect.centerx, self.rect.centery),
                (target_rect.centerx, target_rect.centery),
                tile_radius = self.tile_radius)

            # If returns different coordinates from the current coordinates of the creature.
            if not ((coordinates[0] == self.rect.centerx) and (coordinates[1] == self.rect.centery)):
                self.move_target = pygame.Rect(coordinates[0], coordinates[1], 1, 1)
                self.plan = None
            else:
                self.plan = "collision handle"

        elif( self.plan == "collision handle"):
            print(f"[COLLISION HANDLE] creature center: ({self.rect.centerx}, {self.rect.centery})")
            # Get the next coordinates to move.
            coordinates = self.pathfinder.collision_handle(
                (self.rect.centerx, self.rect.centery),
                tile_radius = self.tile_radius)
            print(f"[COLLISION HANDLE] returned coordinates: {coordinates}")
            # If returns none empty coordinates.
            if coordinates:
                print(f"[COLLISION HANDLE] setting move_target to {coordinates}")
                self.move_target = pygame.Rect(coordinates[0], coordinates[1], 1, 1)
                self.plan = None
            else:
                print("[COLLISION HANDLE] returned None - creature fully stuck")

        # Creature needs to handle a corner.
        elif( self.plan == "handle corners"):

            # Get the next coordinates to move.
            coordinates = self.pathfinder.handle_corners(
                (self.rect.centerx, self.rect.centery),
                (target_rect.centerx, target_rect.centery),
                tile_radius = self.tile_radius)

            # If returns none empty coordinates.
            if coordinates:
                self.move_target = pygame.Rect(coordinates[0], coordinates[1], 1, 1)
                self.plan = None
            else:
                self.plan = "path finding"

        elif( self.plan == "path finding"):

            # Calculate the new path (list of coordinates to move).
            self.path = self.pathfinder.find_path(
                (self.rect.centerx, self.rect.centery),
                (target_rect.centerx, target_rect.centery),
                tile_radius = self.tile_radius)

            # If path is found.
            if self.path:
                self.move_target = pygame.Rect(self.path[0][0], self.path[0][1], 1, 1)
                self.plan == None
            else:
                self.plan == None

        # Current plan failed so its changed. Do nothing for that frame.
        if not self.move_target:
            return

        # Only plan returned coordinates to move to.

        # Now seek to move closer to move_target.
        dx = self.move_target.centerx - self.rect.centerx
        dy = self.move_target.centery - self.rect.centery
        dist = max(math.hypot(dx, dy), 1)

        # Calculate new seek coordinates.
        seek_x = (dx / dist) * speed * dt
        seek_y = (dy / dist) * speed * dt

        # Calculate new position coordinates.
        new_x = self.pos_x + seek_x
        new_y = self.pos_y + seek_y

        self.pos_x = new_x
        self.pos_y = new_y
        self.rect.x = round(self.pos_x)
        self.rect.y = round(self.pos_y)
        self.hitbox.center = self.rect.center

        # If target is reached the target rect then remove target rect.
        if math.hypot(self.move_target[0] - self.rect.centerx, self.move_target[1] - self.rect.centery) < TILE_SIZE // 4:
            self.move_target = None

    # Called: Rat._update_state(), Snake._update_state()
    def _snap_to_home(self):

        # Updated the new (x,y) position of creature to home position.
        self.pos_x         = float(self.home_position.x)
        self.pos_y         = float(self.home_position.y)
        self.rect.topleft  = self.home_position.topleft

        # If temp home then remove it.
        if self.temp_home:
            self.home_position = None
            self.temp_home = False

    # Called: Rat_update_dtate(), Snake._update_state()
    def _attack(self):

        # Check if the global cooldown is on. If so returns False.
        if self.gcd_timer > 0:
            return False

        # Get the list of all the abilities that can be triggered (no cooldown) and are in range and costs exist.
        choices = self._ready_abilities(self.target_dist)
        if choices is None:
            return False

        # Creature chooses an ability (from the list before) based on max damage output.
        ability = self._pick_ability(choices)

        # This is the footprint the outcome of the ability being used.
        result = ability.use(
            self.stats,
            self.target.stats,
            self.target.effects,
            self.target_dist
        )

        # auto-target player if player has no target
        if self.target.target is None:
            self.target.target = self
            self.target.set_target_dist()

        self.gcd_timer      = GCD
        self.last_hit       = result

        # If creature runs out of energy.
        if self.stats.energy < 1:
            self.out_of_energy  = True

        # Sets the state to the specific ability used.
        self._set_state(ability.anim)

        return result

    # Called: Rat._update_state(), Snake._update_state().
    def _wander(self, dt, bounds = None):

        # If creature in idle neutral state.
        if self.state == 'idle_neutral':

            # Move the wander timer and check if it hits the interval.
            self.wander_timer += dt
            if self.wander_timer >= self.wander_interval:

                # Reset the timer and the interval randomness.
                self.wander_timer = 0.0
                self.wander_interval = random.uniform(*self.wander_interval_range)

                # Roll for chance to wander.
                if random.random() < self.wander_chance:

                    # Calculate random direction and random time to wander.
                    angle = random.uniform(0, 2 * math.pi)
                    self.wander_dx       = math.cos(angle)
                    self.wander_dy       = math.sin(angle)
                    self.wander_elapsed  = 0.0
                    self.wander_duration = random.uniform(*self.wander_duration_range)

                    # Return start signal to enter wander state.
                    return "start"
            # If timer is not up do nothing.
            return None

        # Creature is wandering. Update timer.
        self.wander_elapsed += dt

        # Builds a future rect to where wander sends the creature.
        wander_target = self.rect.move(
            round(self.wander_dx * self.stats.mspd),
            round(self.wander_dy * self.stats.mspd)
        )

        # Try to move to that future spot.
        self._move_toward(dt, wander_target, self.stats.mspd, bounds)
        # Change what creature is facing.
        self.facing_right = self.wander_dx > 0

        # If wander timer hits.
        if self.wander_elapsed >= self.wander_duration:
            # Return done signal to exit wander state.
            return "done"

        # If no timer is hit return none to continue wandering.
        return None

    # Called: Rat._update_state(), Snake._update_state()
    def _update_state(self, dt, target, bounds = None):
        pass


    # Called: Creature.update().
    def _animate(self, dt):

        self.anim_done = False
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
                    self.anim_done = True
            else:
                self.frame_index = (self.frame_index + 1) % len(frames)

        self.image = pygame.transform.flip(
            frames[self.frame_index], self.facing_right, False)

    #   Called: Rat.update(), Snake.update()
    def _update_cooldowns(self, dt):

        # If gcd timer is up update it.
        if self.gcd_timer > 0:
            self.gcd_timer = max(0.0, self.gcd_timer - dt)

        # If notice cooldonw timer is up update it.
        if self.notice_cooldown > 0:
            self.notice_cooldown = max(0.0, self.notice_cooldown - dt)

        # For every ability that the entity has update their timers.
        for ability in self.abilities:
            ability.tick(dt)

    # Called: Player.update()
    def set_target_dist(self):

        self.target_dist = math.hypot(
            self.target.rect.centerx - self.rect.centerx,
            self.target.rect.centery - self.rect.centery)

    # Called: Creature.update().
    def _update_combat(self):

        # Updates the state of the creature.
        self.in_combat  = self.state in self.COMBAT_STATES

    # Called: Indie_Game._update()
    def update(self, dt, bounds = None):

        if self.state != "dead":
            self._animate(dt)           # Creature
            self._regen(dt)             # Entity
        self._update_state(dt, bounds)  # Rat, Snake etc
        self._update_cooldowns(dt)      # Creature
        self._update_combat()           # Creature


    # Called: Entity._regen()
    def _begin_death(self):

        # clear players target if this creature was targeted
        if self.target.target is self:
            self.target.target = None
            self.target.target_dist = 0.0

        # Give exp to the player.
        self.target.stats.gain_exp(self.stats.exp_reward)
        # Clean effects to show no data on screen
        self.effects.cleanse_all(self.stats)
        # Creature enters dying state.
        self._set_state("dying")

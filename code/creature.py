import pygame
import random
import math

from entity         import Entity
from settings       import (ANIM_SPEED, TILE_SIZE, NOTICE_COOLDOWN, GCD, SPRITE_SCALE)

class Creature(Entity):

    _SUBBASE = "creatures/"

    ATTACKS             = frozenset()
    ABILITY_STATES      = frozenset()
    COMBAT_STATES       = frozenset()
    NON_COMBAT_STATES   = frozenset()
    ONE_SHOT_STATES     = frozenset()

    # Called: Rat.__init__(), Snake.__init__()
    def __init__(self, x, y, stats, player, home_position = None, returning = False, fleeing = False, *groups):
        super().__init__(x, y, stats, *groups)

        # Basic attr
        self.target                 = player            # It is part of entity class.
        self.last_target            = player
        self.home_position          = home_position
        self.temp_home              = False
        self.returning              = returning
        self.fleeing                = fleeing
        self.home_max_dist          = 0
        self.out_of_energy          = False
        self.notice_cooldown        = NOTICE_COOLDOWN
        self.obstacles              = []
        self.facing_right           = False
        self.exp_dropped            = False

        # Wander attr
        self.wander_timer           = random.uniform(0, 1.0)
        self.wander_interval        = random.uniform(0.9, 1.1)
        self.wander_interval_range  = (0.9, 1.1)
        self.wander_chance          = 0.04
        self.wander_duration        = 0.0
        self.wander_duration_range  = (0.5, 3.0)
        self.wander_elapsed         = 0.0
        self.wander_dx              = 0.0
        self.wander_dy              = 0.0

        # Pathfinder attr
        self.pathfinder             = None      # set by level after spawn
        self.neighbors              = []        # nearby creatures for separation.
        self.path                   = []        # current A* waypoint list
        self.path_update_timer      = random.uniform(0, 1.0)  # staggered start
        self.path_update_interval   = random.uniform(0.8, 1.2)  # slightly different intervals
        self.plan                   = None
        self.move_target            = None
        self.stuck_counter          = 0
        self.last_pos_x             = 0.0
        self.last_pos_y             = 0.0
        self.no_progress_counter    = 0
        self.line_of_sight          = False
        self.los_lock_timer         = 0.0
        self.los_lock_interval      = random.uniform(1.8, 2.2)  # stagger LOS too

        # Sprite / hitbox attr
        self.animations             = {k: self._load(self._SUBBASE + self._SUBBASE2 + v) for k, v in self._ANIM_FILES.items()}
        self.image                  = self.animations["idle_neutral"][0]
        self.rect                   = self.image.get_rect(topleft = (x, y))
        self.hitbox                 = self.rect.inflate(-50, -50)
        self.tile_radius            = SPRITE_SCALE // 2

    # Called: _move_toward(), Rat._update_state(), Snake._update_state()
    def _distance_to(self, target_rect):

        # It calculates and returns the distance to target (player, home_position).
        dx = target_rect.centerx - self.rect.centerx
        dy = target_rect.centery - self.rect.centery
        return (dx**2 + dy**2) ** 0.5

    # Called: _wander(), Rat._update_state(), Snake._update_state().
    def _move_toward(self, dt, target_rect, speed, bounds = None):

        # It calculates the distance to target (player, home_position).
        dist = max(self._distance_to(target_rect), 1)

        # Calculates and updates the new (x,y) position.
        new_x = self.pos_x + ((target_rect.centerx - self.rect.centerx) / dist) * speed * dt
        new_y = self.pos_y + ((target_rect.centery - self.rect.centery) / dist) * speed * dt

        # Imaginary hitbox if creature moves dt.
        new_hitbox = self.hitbox.move(
            round(new_x) - self.rect.x,
            round(new_y) - self.rect.y
        )

        # If creatures future movement hits the player stops it before moving there.
        if new_hitbox.colliderect(self.target.hitbox):
            return

        obs_col = None
        # If creatures future movement hits an obstacle.
        for obs in self.obstacles:
            if new_hitbox.colliderect(obs.hitbox):
                obs_col = obs
                break

        # If nothing of the above set the new coordinates of the creature.
        self.pos_x = new_x
        self.pos_y = new_y
        self.rect.x = round(self.pos_x)
        self.rect.y = round(self.pos_y)
        self.hitbox.center = self.rect.center

        # If creatures movement hits an obstance. Recalculate wander attr.
        if obs_col:

            # If obstacle is hit in the x axes change direction 180 degrees.
            if (self.rect.left < obs_col.rect.left or self.rect.right > obs_col.rect.right):
                self.wander_dx = -self.wander_dx
                self.facing_right = self.wander_dx > 0

            # If obstacle is hit in the y axes change direction 180 degrees.
            if self.rect.top < obs_col.rect.top or self.rect.bottom > obs_col.rect.bottom:
                self.wander_dy = -self.wander_dy

            # Recalculate for wander for random time.
            self.wander_elapsed  = 0.0
            self.wander_duration = random.uniform(*self.wander_duration_range)

        # If creatures movement hits a boundary or an obstance. Recalculate wander attr.
        if bounds and not bounds.contains(self.rect):

            # If bound is hit in the x axes change direction 180 degrees.
            if (self.rect.left < bounds.left or self.rect.right > bounds.right):
                self.wander_dx = -self.wander_dx
                self.facing_right = self.wander_dx > 0

            # If bound is hit in the y axes change direction 180 degrees.
            if self.rect.top < bounds.top or self.rect.bottom > bounds.bottom:
                self.wander_dy = -self.wander_dy

            # Recalculate for wander for random time.
            self.wander_elapsed  = 0.0
            self.wander_duration = random.uniform(*self.wander_duration_range)

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
    def _move_smart(self, dt, target_rect, speed, bounds = None):

        # Tick LOS lock timer every frame.
        if self.los_lock_timer > 0:
            self.los_lock_timer -= dt

        # If creature has no plan and no target to move to.
        if not self.plan and not self.move_target:

            if self.los_lock_timer <= 0:

                # Checks if creature has line of sight of the target.
                self.line_of_sight = self.pathfinder.line_of_sight(
                    (self.rect.centerx, self.rect.centery),
                    (target_rect.centerx, target_rect.centery),
                    tile_radius = self.tile_radius,
                    neighbors=[n for n in self.neighbors
                                   if n is not self and n.state not in ("dead", "dying")])

                if not self.line_of_sight:

                    # Set LOS lock
                    self.los_lock_timer = self.los_lock_interval

            # If line of sight.
            if self.line_of_sight:

                # Direct movement — Empty the path and go straight.
                self.path = []
                self.plan = "move to target"

            # If a path exists.
            elif self.path:

                # First waypoint is reached. Pop it out.
                self.path.pop(0)

                # If more waypoints exist.
                if self.path:
                    self.move_target = pygame.Rect(self.path[0][0], self.path[0][1], 1, 1)

            # If no line of sight and no path.
            else:

                # Time for path finding!!
                self.plan = "path finding"

        # Creature moves directly to the target rect plan.
        elif( self.plan == "move to target"):

            # Get the next coordinates to move.
            coordinates = self.pathfinder.move_to_target(
                (self.rect.centerx, self.rect.centery),
                (target_rect.centerx, target_rect.centery),
                tile_radius = self.tile_radius)

            # If returns different coordinates from the current coordinates of the creature.
            if not ((coordinates[0] == self.rect.centerx) and (coordinates[1] == self.rect.centery)):

                # New target to move to found.
                self.move_target = pygame.Rect(coordinates[0], coordinates[1], 1, 1)
                self.plan = None

            # If the coordinates are the same
            else:

                #  Time for collision handing.
                self.plan = "collision handle"

        # Creature moves to the nearest free space rect plan.
        elif( self.plan == "collision handle"):

            print("COLLISION HANDLE!")
            # Get the next coordinates to move.
            coordinates = self.pathfinder.collision_handle(
                (self.rect.centerx, self.rect.centery),
                tile_radius = self.tile_radius)

            # If returns none empty coordinates.
            if coordinates:

                # New target to move to found.
                self.move_target = pygame.Rect(coordinates[0], coordinates[1], 1, 1)
                self.plan = None

        # Creature calculates a path and moves to its first path waypoint.
        elif( self.plan == "path finding"):

            # Block the player's tile — creatures should never path to it.
            player_r = int(self.target.rect.centerx / TILE_SIZE)
            player_c = int(self.target.rect.centery / TILE_SIZE)

            # Build dynamic blocked from neighbor current positions and the players.
            dynamic_blocked = {(player_r,player_c)}

            # For all creatures.
            for n in self.neighbors:

                # All creature possitions except self that are not dead or dying are added to the dynamic blocked set.
                if n is not self and n.state not in ("dead", "dying"):
                    r = int(n.rect.centerx / TILE_SIZE)
                    c = int(n.rect.centery / TILE_SIZE)
                    dynamic_blocked.add((r, c))

            # Calculate the new path (list of coordinates to move).
            new_path = self.pathfinder.find_path(
                (self.rect.centerx, self.rect.centery),
                (target_rect.centerx, target_rect.centery),
                tile_radius = self.tile_radius,
                dynamic_blocked = dynamic_blocked)

            # If new path is found.
            if new_path:

                self.path = new_path
                self.move_target = pygame.Rect(self.path[0][0], self.path[0][1], 1, 1)
                self.plan = None

            # If not new path is found but has old.
            elif self.path:

                print("PATH FINDING FAILED. SETS OLD PATH!")
                self.plan = None

            # If no path at all!.
            else:

                print("PATH FINDING FAILED. NO PATH!")
                self.plan = None

        # Current plan failed so its changed. Do nothing for that frame.
        if not self.move_target:
            return

        # Check if path exists
        if self.path:
           # Update the path timer.
            self.path_update_timer += dt
            # If time is up.
            if self.path_update_timer >= self.path_update_interval:
                # Time for path finding.
                self.plan = "path finding"
                # Reset the path timer.
                self.path_update_timer = 0.0

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

        # After calculating new_x, new_y — add this before applying:
        new_hitbox = self.hitbox.move(
            round(new_x) - self.rect.x,
            round(new_y) - self.rect.y
        )

        # Check obstacle collisions
        blocked = any(new_hitbox.colliderect(obs.hitbox) for obs in self.obstacles)

        if not blocked:
            self.stuck_counter = 0
            self.pos_x = new_x
            self.pos_y = new_y
            self.rect.x = round(self.pos_x)
            self.rect.y = round(self.pos_y)
            self.hitbox.center = self.rect.center

            # Face the direction of movement, not the player.
            if abs(dx) > abs(dy):
                self.facing_right = dx > 0

        else:

            # Try sliding along x axis only
            new_hitbox_x = self.hitbox.move(round(new_x) - self.rect.x, 0)
            blocked_x = (any(new_hitbox_x.colliderect(obs.hitbox) for obs in self.obstacles))

            # Try sliding along y axis only
            new_hitbox_y = self.hitbox.move(0, round(new_y) - self.rect.y)
            blocked_y = (any(new_hitbox_y.colliderect(obs.hitbox) for obs in self.obstacles))

            if not blocked_x:

                self.stuck_counter = 0
                self.pos_x = new_x
                self.rect.x = round(self.pos_x)

            if not blocked_y:

                self.stuck_counter = 0
                self.pos_y = new_y
                self.rect.y = round(self.pos_y)

            # Only count as stuck when both axes are blocked.
            if blocked_x and blocked_y:

                self.stuck_counter += 1

                if self.stuck_counter > 30:

                    print("STUCK COUNTER ALERT.")
                    self.move_target            = None
                    self.plan                   = "collision handle"
                    self.path                   = []
                    self.stuck_counter          = 0
                    self.no_progress_counter    = 0
                    self.path_update_timer      = random.uniform(0, 0.3)
                    return

            self.hitbox.center = self.rect.center

        # Progress check — catches sliding trap where creature moves
        # but makes no real progress toward its waypoint.
        progress = math.hypot(self.pos_x - self.last_pos_x, self.pos_y - self.last_pos_y)

        if progress < 0.5:
            self.no_progress_counter += 1
        else:
            self.no_progress_counter = 0

        self.last_pos_x = self.pos_x
        self.last_pos_y = self.pos_y

        if self.no_progress_counter > 30:

            print("NO PROGRESS COUNTER ALERT.")
            self.move_target         = None
            self.path                = []
            self.stuck_counter       = 0
            self.no_progress_counter = 0
            self.path_update_timer   = random.uniform(0, 0.3)

            dist_to_target = math.hypot(
                self.target.rect.centerx - self.rect.centerx,
                self.target.rect.centery - self.rect.centery)

            # If close to player — escape first, then replan.
            # If far from player — just replan directly.
            if dist_to_target < TILE_SIZE * 4:
                self.plan = "collision handle"

            else:
                self.plan = "path finding"

        # Soft push — only when physically overlapping another creature and creatures has no path.
        if not self.path:
            for n in self.neighbors:
                if n is self or n.state in ("dead", "dying"):
                    continue
                overlap_x = self.rect.centerx - n.rect.centerx
                overlap_y = self.rect.centery - n.rect.centery
                dist = math.hypot(overlap_x, overlap_y)
                min_dist = TILE_SIZE

                if dist < min_dist and dist > 0:

                    # Push proportionally to how much they overlap.
                    push = (min_dist - dist) / min_dist
                    push_x = (overlap_x / dist) * push * TILE_SIZE * 0.3
                    push_y = (overlap_y / dist) * push * TILE_SIZE * 0.3

                    # Only push if it doesn't go into an obstacle.
                    push_hitbox = self.hitbox.move(round(push_x), round(push_y))
                    if not any(push_hitbox.colliderect(obs.hitbox) for obs in self.obstacles):
                        self.pos_x += push_x
                        self.pos_y += push_y
                        self.rect.x = round(self.pos_x)
                        self.rect.y = round(self.pos_y)
                        self.hitbox.center = self.rect.center

        # If move_target reached — clear it.
        if self.move_target and math.hypot(
                self.move_target[0] - self.rect.centerx,
                self.move_target[1] - self.rect.centery) < TILE_SIZE // 4:
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

    # Called: Rat._update_state(), Snake._update_state()
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

    # Called: Rat._update_state(), Snake._update_state()
    def _update_state(self, dt, target, bounds = None):
        pass


    # Called: update().
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

    # Called: update().
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

    # Called: update().
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

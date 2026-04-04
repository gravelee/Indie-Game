import pygame
import math

from entity     import Entity
from settings   import (TILE_SIZE, ANIM_SPEED, GCD)


class Player(Entity):

    _SUBBASE = "player/"

    # ── Directional animations (loaded per direction) ──────────
    # Each entry here loads 4 variants: _south, _north, _east, _west
    _DIRECTIONAL = [
        "forward_slash",
        "idle_attack",
        "idle_neutral",
        "pull",
        "push",
        "shield_stance",
        "shield_up",
        "starts_walk",
        "walking",
    ]

    # ── Non-directional animations (loaded once) ───────────────
    _NON_DIRECTIONAL = [
        "talking",
        "sits_down",
        "sitting",
        "stands_up",
        "bow",
        "smoke_screen",
        "power_up",
        "acquire",
        "death",
        "spawn",
    ]

    ATTACKS             = frozenset(("player_slash",))
    ABILITY_STATES      = frozenset(("forward_slash",))
    COMBAT_STATES       = frozenset(("idle_attack", "forward_slash"))
    NON_COMBAT_STATES = frozenset((
        "idle_neutral", "walking", "spawn", "sitting",
        "pull", "push", "shield_stance", "starts_walk",
        "talking", "sits_down", "stands_up", "bow",
        "smoke_screen", "power_up", "acquire", "shield_up",
        "death", "dead"
    ))
    ONE_SHOT_STATES     = frozenset((
        "forward_slash", "shield_up", "starts_walk",
        "talking", "sits_down", "stands_up", "bow",
        "smoke_screen", "power_up", "acquire", "death", "spawn"
    ))
    LOOPING_STATES = frozenset((
        "idle_attack", "idle_neutral", "pull", "push",
        "shield_stance", "walking", "sitting"
    ))
    LOOPING_CANT_ATTACK_STATES = frozenset((
        "pull", "push", "sitting"
    ))

    # Direction names — used to build animation keys and snap facing.
    DIRECTIONS = ("south", "north", "east", "west")

    # Called: Level._spawn_entities()
    def __init__(self, x, y, stats, *groups):
        super().__init__(x, y, stats, *groups)

        self.enemies            = []
        self.obstacles          = []
        self.facing_angle       = 0.0
        self.facing             = "south"   # cardinal direction
        self.stopped            = False
        self.player_move_input  = False

        # Load all animations.
        self.animations = {}
        self._load_animations()

        # Start in spawn state.
        self.state       = "spawn"
        self.image       = self._current_frames()[0]
        self.rect        = self.image.get_rect(topleft=(x, y))
        self.hitbox      = self.rect.inflate(-50, -50)

    # Called: __init__()
    def _load_animations(self):

        # Load directional animations — 4 variants each.
        for name in self._DIRECTIONAL:
            for direction in self.DIRECTIONS:
                key      = f"{name}_{direction}"
                self.animations[key] = self._load(f"{self._SUBBASE + key}.png")

        # Load non-directional animations — one variant each.
        for name in self._NON_DIRECTIONAL:
            self.animations[name] = self._load(f"{self._SUBBASE + name}.png")


    # Called: _targets_in_zone()
    def _get_attack_zone(self):
        # Returns list of (rect_x, rect_y) world tile centers in the attack zone.
        r = self.rect.centerx // TILE_SIZE
        c = self.rect.centery // TILE_SIZE
        ts = TILE_SIZE

        if self.facing == "south":
            tiles = [(r-1, c+1), (r, c+1), (r+1, c+1), (r, c+2)]
        elif self.facing == "north":
            tiles = [(r-1, c-1), (r, c-1), (r+1, c-1), (r, c-2)]
        elif self.facing == "east":
            tiles = [(r+1, c-1), (r+1, c), (r+1, c+1), (r+2, c)]
        elif self.facing == "west":
            tiles = [(r-1, c-1), (r-1, c), (r-1, c+1), (r-2, c)]

        return [pygame.Rect(tx * ts, ty * ts, ts, ts) for tx, ty in tiles]

    # Called: attack()
    def _targets_in_zone(self):
        # Returns all enemies whose hitbox overlaps the attack zone.
        zone = self._get_attack_zone()
        return [
            e for e in self.enemies
            if e.state not in ("dead", "dying")
            and any(e.hitbox.colliderect(tile) for tile in zone)
        ]

    # Called: _handle_movement()
    def _update_facing(self, dx, dy):

        # Snap movement vector to closest cardinal direction.
        if abs(dx) >= abs(dy):
            self.facing       = "east" if dx > 0 else "west"
        else:
            self.facing = "south" if dy > 0 else "north"

        # Update facing angle for cone attack.
        self.facing_angle = math.degrees(math.atan2(dy, dx))

    # Called: _animate()
    def _current_key(self):

        # Returns the animation key for the current state and facing direction.
        if self.state in self._NON_DIRECTIONAL or self.state == "dead":
            return self.state
        # Directional state.
        return f"{self.state}_{self.facing}"

    # Called: _animate()
    def _current_frames(self):

        key = self._current_key()
        # Fallback to idle_neutral_south if key somehow missing.
        return self.animations.get(key, self.animations["idle_neutral_south"])


    # Called: Indie_Game._handle_events()
    def attack(self):

        # Cannot attack during one-shot or looping-no-attack animations.
        if self.state in self.ONE_SHOT_STATES or self.state in self.LOOPING_CANT_ATTACK_STATES:
            return False

        # Global cooldown check.
        if self.gcd_timer > 0:
            return False

        # Can attack even with no targets — play animation anyway.
        # Get the list of all the abilities that can be triggered (no cooldown) and are in range and costs exist.
        choices = self._ready_abilities(0.0)
        # If the list is empty returns False.
        if choices is None:
            return False

        # You choose an ability (from the list before) based on max damage output.
        ability = self._pick_ability(choices)

        # Get all targets in zone.
        targets = self._targets_in_zone()

        # This is the footprint the outcome of the ability being used on all targets within an area.
        results = ability.use(self.stats, targets, 0.0)

        # Wake up target creature if in one of its non combat states.
        for t in targets:
            if t.state in t.NON_COMBAT_STATES:
                t._set_state("enter_stance")

        # Store results for combat feedback.
        # last_hit is the full list of result dicts; last_target is the list of targets hit.
        self.last_hit = results
        self.last_target = targets if targets else None

        # Auto-focus the closest hit target if player has no target set.
        if targets and self.target is None:
            self.target = min(targets,
                    key=lambda t: math.hypot(t.rect.centerx - self.rect.centerx, t.rect.centery - self.rect.centery))
            self.set_target_dist()

        self.gcd_timer   = GCD

        # Sets the state to the specific ability used.
        self._set_state(ability.anim)

        return True

    # Called: Player.update()
    def _handle_movement(self, dt, bounds):

        # Block movement during one-shot states.
        if self.state in self.ONE_SHOT_STATES:
            self.player_move_input = False
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

            # Update facing direction from movement vector.
            self._update_facing(dx, dy)

            # Calculate imaginary hitbox and move it to the direction the player is moving
            # If there is collision do not let the player to move at that direction.
            new_rect_x = round(self.pos_x + dx * self.stats.mspd * dt)
            new_rect_y = round(self.pos_y + dy * self.stats.mspd * dt)
            new_hitbox = self.hitbox.move(
                new_rect_x - self.rect.x,
                new_rect_y - self.rect.y
            )

            # Check creature collision.
            blocked = any(
                new_hitbox.colliderect(e.hitbox)
                for e in self.enemies
                if e.state != "dead"
            )

            # Check obstacle collision.
            if not blocked:
                blocked = any(
                    new_hitbox.colliderect(obs.hitbox)
                    for obs in self.obstacles
                )

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

                # We set the center of our hitbox to the center of player rect.
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

        frames = self._current_frames()

        if self.frame_index >= len(frames):
            self.frame_index = 0

        self.anim_timer += dt
        if self.anim_timer >= ANIM_SPEED:
            self.anim_timer = 0.0

            if self.state in self.ONE_SHOT_STATES:
                if self.frame_index < len(frames) - 1:
                    self.frame_index += 1
                else:
                    self.anim_done   = True
                    self.frame_index = 0
            else:
                self.frame_index = (self.frame_index + 1) % len(frames)

        # Directional and Non-directional — no flip needed.
        self.image = frames[self.frame_index]

    # Called: Player.update()
    def _update_state(self, dt):

        # ── Spawn ──────────────────────────────────────────────
        if self.state == "spawn":
            if self.anim_done:
                self._set_state("idle_neutral")

        # ── Idle neutral ───────────────────────────────────────
        elif self.state == "idle_neutral":
            if self.player_move_input and not self.stopped:
                self._set_state("walking")
            elif self.in_combat:
                self._set_state("idle_attack")

        # ── Idle attack ────────────────────────────────────────
        elif self.state == "idle_attack":
            if self.player_move_input and not self.stopped:
                self._set_state("walking")
            elif not self.in_combat:
                self._set_state("idle_neutral")

        # ── Walking ────────────────────────────────────────────
        elif self.state == "walking":
            if self.stopped:
                if self.in_combat:
                    self._set_state("idle_attack")
                else:
                    self._set_state("idle_neutral")
            elif not self.player_move_input:
                if self.in_combat:
                    self._set_state("idle_attack")
                else:
                    self._set_state("idle_neutral")

        # ── Ability states (forward_slash etc) ─────────────────
        elif self.state in self.ABILITY_STATES:
            if self.anim_done:
                self._set_state("idle_attack")

        # ── Death ──────────────────────────────────────────────
        elif self.state == "death":
            if self.anim_done:
                self._set_state("dead")

        # ── Dead ───────────────────────────────────────────────
        elif self.state == "dead":
            self.corpse_alpha = max(0, self.corpse_alpha - 300 * dt)
            self.image.set_alpha(int(self.corpse_alpha))
            if self.corpse_alpha <= 0:
                self.kill()

        # ── Sit sequence ───────────────────────────────────────
        elif self.state == "sits_down":
            if self.anim_done:
                self._set_state("sitting")

        elif self.state == "stands_up":
            if self.anim_done:
                self._set_state("idle_neutral")

        # ── Other one-shots — return to idle after ─────────────
        elif self.state in self.ONE_SHOT_STATES:
            if self.anim_done:
                if self.in_combat:
                    self._set_state("idle_attack")
                else:
                    self._set_state("idle_neutral")

    # Called: Player.update()
    def _update_combat(self):

        # For every creature in the level check if any is in combat and if so so are you.
        self.in_combat = self.enemies and any(
            c.state in c.COMBAT_STATES
            for c in self.enemies
        )

    # Called: Indie_Game._update()
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
        self.target      = None
        self.in_combat   = False
        self.target_dist = 0.0

        # Creature enters death state.
        self._set_state("death")

import math

from creature   import Creature
from settings   import (NOTICE_COOLDOWN, HOME_MAX_DIST, NOTICE_DIRECTION, NOTICE_DIST, CHASE_DIST, ATTACK_DIST, FLEE_SPEED, HOME_DIST, BASE_MOVEMENT_SPEED)

class Rat(Creature):

    _SUBBASE2 = "rat/"
    _ANIM_FILES = {
        "idle_neutral" : "idle_neutral.png",
        "wander"       : "move.png",
        "notice"       : "notice.png",
        "enter_stance" : "enter_stance.png",
        "idle_attack"  : "idle_attack.png",
        "chase"        : "move.png",
        "exit_stance"  : "exit_stance.png",
        "returning"    : "move.png",
        "attack_bite"  : "attack_bite.png",
        "attack_slash" : "attack_slash.png",
        "dying"        : "death.png"
    }

    ATTACKS             = frozenset(("rat_bite","rat_slash"))
    ABILITY_STATES      = frozenset(("attack_bite","attack_slash"))
    COMBAT_STATES       = frozenset(("enter_stance", "idle_attack", "chase", "attack_bite","attack_slash"))
    NON_COMBAT_STATES   = frozenset(("idle_neutral", "wander", "notice", "exit_stance", "returning", "dying"))
    ONE_SHOT_STATES     = frozenset(("notice", "enter_stance", "exit_stance", "attack_bite", "attack_slash", "dying"))

    # Called: Level._spawn_entities()
    def __init__(self, x, y, stats, player, home_position = None, returning = False, fleeing = False, *groups):
        super().__init__(x, y, stats, player, home_position, returning, fleeing, *groups)

        self.stats.exp_multiplier = 2.0

    # Called: Creature.update()
    def _update_state(self, dt, bounds = None):

        # If player is dead or dying enter returning state.
        if self.target.state in ("dying", "dead"):
            if self.state in self.COMBAT_STATES:
                self._set_state("returning")
                return

        # Calculate distance to the player and also direction if the player is close enough.
        dist = self._distance_to(self.target.rect)
        if dist < NOTICE_DIRECTION:
            rad = math.radians(self.camera_angle)
            cos_a = math.cos(rad)
            sin_a = math.sin(rad)
            dx = self.target.rect.centerx - self.rect.centerx
            dy = self.target.rect.centery - self.rect.centery
            screen_dx = dx * cos_a - dy * sin_a
            self.facing_right = screen_dx > 0

        # If creature in idle neutral or wander state.
        if self.state in ("idle_neutral", "wander"):

            # Take wander status.
            signal = self._wander(dt, bounds)

            # Is it time wander or not?
            if signal == "start":
                self._set_state("wander")
            elif signal == "done":
                self._set_state("idle_neutral")

            # If player is close enough and creatures notice cooldown is off then enter notice state.
            if dist < NOTICE_DIST and self.notice_cooldown <= 0:
                self._set_state("notice")

        # If creature in notice state.
        elif self.state == "notice":

            # If player is in attack distance enters enter stance state.
            if dist < ATTACK_DIST:
                self._set_state("enter_stance")
            else:
                # If notice animation has played and player still within notice distance creature enters enter stance state.
                if self.anim_done and dist < NOTICE_DIST:
                    self._set_state("enter_stance")
                # If notice animation has played and the player is out if noticing distance creature enters idle neutral state.
                elif self.anim_done:
                    self._set_state("idle_neutral")

        # If creature in enter stance state.
        elif self.state == "enter_stance":

            # If creature does not have a home he makes a temporary home its position.
            if self.home_position is None:
                self.home_position = self.rect.copy()
                self.temp_home = True

            # If enter stance animation has played.
            if self.anim_done:

                # If player is in attack range creature enters idle_attack state.
                if dist < ATTACK_DIST:
                    self._set_state("idle_attack")
                # If player is still within notice distance enter chase state.
                elif dist < NOTICE_DIST:
                    self._set_state("chase")
                # If player is out of noticing distance enter exit stance state.
                else:
                    self._set_state("exit_stance")

        # If creature in idle attack state.
        elif self.state == "idle_attack":

            # If creature runs out of energy it runs home.
            if self.out_of_energy:
                self._set_state("returning")
            # If player is within attack range creature tries to attack.
            elif dist < ATTACK_DIST:
                self._attack()
            # If player is within chasing distance creature enters chase state.
            elif dist < CHASE_DIST:
                self._set_state("chase")
            # If player is out of chasing distance creature enters exit stance state.
            else:
                self._set_state("exit_stance")

        # If creature in chase state.
        elif self.state == "chase":

            # Calculates distance to home (home is either initial home or temporary home)
            dist_home = self._distance_to(self.home_position)
            # If distance from home is too far aways.
            if dist_home > HOME_MAX_DIST:
                self._set_state("returning")
                self.home_max_dist = True
            # If player is in attack range creature enters idle_attack state.
            elif dist < ATTACK_DIST:
                self._set_state("idle_attack")
            # If player is out of chase range the creature enters exit stance state.
            elif dist > CHASE_DIST:
                self._set_state("exit_stance")
            else:
                # Creature moves towards the player.
                self._move_smart(dt, self.target.rect, BASE_MOVEMENT_SPEED, bounds)

        # If creature in exit stance state.
        elif self.state == "exit_stance":

            # If exit stance animation has played.
            if self.anim_done:

                # If player is within notice distance creature enters enter stance state.
                if dist < NOTICE_DIST:
                    self._set_state("enter_stance")
                # If the creature does not have a home it enters idle neutral state.
                elif self.home_position is None:
                    self._set_state("idle_neutral")
                # If creature does have a home it enters returning state.
                else:
                    self._set_state("returning")

        # If creature in returning state (means it has a home).
        elif self.state == "returning":

            # Calculate distance to home (home is either initial home or temporary home) and direction.
            dist_home = self._distance_to(self.home_position)

            # Returning = If creature is returning home and player enters creatures noticing range
            # the creature will ignore him and will continue running toward home.
            #
            # If creature returning = true or returning = false but player is out of noticing range or home max distance is reached or creature runs out of energy.
            if self.returning or (not self.returning and dist > NOTICE_DIST) or self.home_max_dist or self.out_of_energy:

                # Creature moves towards home.
                self._move_smart(dt, self.home_position, FLEE_SPEED, bounds)

                # If creature is much close to its position snaps to home and enters idle neutra state.
                if dist_home <= HOME_DIST:
                    self._snap_to_home()
                    self._set_state("idle_neutral")
                    self.home_max_dist = False
                    self.notice_cooldown = NOTICE_COOLDOWN
                    self.out_of_energy = False

            # If player is not alive creature is running to home position.
            elif self.target.state == "dying" or self.target.state == "dead":
                self._move_smart(dt, self.home_position, FLEE_SPEED, bounds)

            # Creature returing = false and player is within notice distance.
            else:

                # If player is within attack range creature enters idle attack state.
                if dist < ATTACK_DIST:
                    self._set_state("idle_attack")
                # If creature is not close enough to attack enters enter stance state.
                else:
                    self._set_state("enter_stance")

        elif self.state in self.ABILITY_STATES:
            if self.anim_done:
                self._set_state("idle_attack")

        # If creature is dying.
        elif self.state == "dying":

            # If dying animation has played.
            if self.anim_done:
                self._set_state("dead")

        # If creature is dead.
        elif self.state == "dead":

            # Start fading its corpse.
            self.corpse_alpha = max(0, self.corpse_alpha - 300 * dt)
            self.image.set_alpha(int(self.corpse_alpha))
            if self.corpse_alpha <= 0:
                self.kill()

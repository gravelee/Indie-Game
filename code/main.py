import pygame
import sys
import math

from camera             import YSortCameraGroup
from combat_feedback    import CombatFeedback
from level              import Level
from ui                 import UIManager
from hud                import HUD
from debug_panel        import StatPanel
from settings           import MAP_W, MAP_H, FPS, TILE_SIZE

class Indie_Game():

    def __init__(self):

        pygame.init()
        pygame.display.set_caption("Indie Game")

        # Start the clock.
        self.clock = pygame.time.Clock()
        # Set the screen up.
        self.screen  = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)

        # camera — game owns, level uses
        self.camera  = YSortCameraGroup(
            self.screen, TILE_SIZE, MAP_W, MAP_H
        )

        # groups — game owns these, level populates them
        self.players    = pygame.sprite.Group()
        self.creatures  = pygame.sprite.Group()
        self.obstacles  = pygame.sprite.Group()

        # level — loads assets and spawns entities into camera + groups
        self.level = Level(self.screen, self.camera, "level_01",
            self.players, self.creatures, self.obstacles, MAP_W, MAP_H)

        # ui and feedback — after display is ready
        self.ui = UIManager(self.camera)
        self.feedback = CombatFeedback(self.ui)
        self.hud = HUD(self.screen)

        # Setup the panels.
        self.panel_player   = StatPanel(self.screen,
                                        self.screen.get_width() - 300, 20,
                                        title   = "Player",
                                        pauses_game = True)
        self.panel_creature = StatPanel(self.screen,
                                        20, 20,
                                        title   = "Creature",
                                        pauses_game = False)
        self.panel_player.set_entity(self.level.player)

        # Set other main attr.
        self.running = True
        self.bounds = pygame.Rect(0, 0, MAP_W, MAP_H)

        # ── Camera rotation ────────────────────────────────────
        self.world_angle     = 0.0
        self._rmb_held       = False
        self._rmb_last_mouse = None

    # Called: run()
    def _handle_events(self):

        # ── Right-click drag — rotate world ───────────────────
        if self._rmb_held:
            mx, my = pygame.mouse.get_pos()
            if self._rmb_last_mouse is not None:
                player = self.level.player
                px = player.rect.centerx - int(self.camera.offset.x)
                py = player.rect.centery - int(self.camera.offset.y)

                # Angle from player to last and current mouse positions.
                last_angle = math.degrees(math.atan2(
                    self._rmb_last_mouse[1] - py,
                    self._rmb_last_mouse[0] - px))
                curr_angle = math.degrees(math.atan2(my - py, mx - px))

                delta = curr_angle - last_angle
                # Wrap delta to [-180, 180] to avoid jumps.
                if delta > 180:  delta -= 360
                if delta < -180: delta += 360

                # Only if the change in the delta (camera angle degree) is significant enough (at least 2 degrees).
                if abs(delta) >= 4.0:
                    self.world_angle = (self.world_angle - delta) % 360
                    self.camera.angle = round(self.world_angle / 4) * 4 % 360

            self._rmb_last_mouse = (mx, my)

        # Handle player keyboard and mouse inputs.
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False
                if event.key == pygame.K_SPACE:
                    self.level.player.attack()

                # debugging tools
                if event.key == pygame.K_p:
                    self.panel_player.toggle()


            if event.type == pygame.MOUSEBUTTONDOWN:

                if event.button == 3:   # right click — start rotation drag
                    self._rmb_held = True
                    self._rmb_last_mouse = pygame.mouse.get_pos()

                if event.button == 1:
                    mx, my = pygame.mouse.get_pos()
                    # Convert screen pos to world pos accounting for rotation.
                    wx, wy = self.camera.screen_to_world(mx, my, self.level.player)
                    clicked_creature = None
                    for creature in self.level.creatures:
                        if creature.rect.collidepoint(wx, wy):
                            clicked_creature = creature
                            break
                    if clicked_creature:
                        self.level.player.target = clicked_creature
                        self.level.player.set_target_dist()
                    else:
                        self.level.player.target = None
                        self.level.player.target_dist = 0

            if event.type == pygame.MOUSEBUTTONUP:
                if event.button == 3:   # right click released
                    self._rmb_held = False
                    self._rmb_last_mouse = None

    # Called: run()
    def _update(self, dt):

        # If player panel is openned pause the game.
        if self.panel_player.should_pause:
            return

        # Open the creature panel if the player targets.
        if self.level.player.target:
            self.panel_creature.set_entity(self.level.player.target)
            self.panel_creature.visible = True
        # If no target keep the creature panel closed.
        else:
            self.panel_creature.close()

        # Update the player.
        self.level.player.update(dt, self.bounds, self.world_angle)

        # Update all creatures in the level.
        for creature in self.level.creatures:
            creature.update(dt, self.bounds, self.world_angle)

        # Update all obstacles (e.g. bush death animations).
        # Use the sprite group — dying bushes are removed from obstacle_list
        # on hit but stay in the group until their animation finishes.
        for obstacle in self.obstacles:
            obstacle.update(dt)

        # Update ui and combat feedback for all.
        self.ui.update(dt)
        self.feedback.process_player(self.level.player)
        self.feedback.process_entities(self.level.active_creatures)

    # Called: _draw()
    def _draw_paths(self):
        for creature in self.level.creature_list:
            if not creature.path:
                continue
            # Draw A* waypoints (red).
            for wx, wy in creature.path:
                sx, sy = self.camera.world_to_screen(wx, wy, self.level.player)
                pygame.draw.circle(self.screen, (255, 0, 0), (int(sx), int(sy)), 5)
                pygame.draw.circle(self.screen, (255, 255, 255), (int(sx), int(sy)), 5, 1)

    # Called: run()
    def _draw(self):

        # Draw everything that falls within camera limits.
        self.camera.custom_draw(self.level.player)
        # After camera draw ui and combat feedback.
        self.ui.draw(self.screen, self.camera, self.level.active_creatures)
        # Also draw the player bars.
        self.hud.draw(self.level.player)
        self._draw_paths()
        # Draw the panels if openned.
        self.panel_player.draw()
        self.panel_creature.draw()

        pygame.display.flip()

    # Called: __main__()
    def run(self):



        while self.running:

            print(f"FPS: {self.clock.get_fps():.0f}  angle: {self.world_angle:.0f}  cam: {self.camera.angle:.0f} cache: {len(self.camera._sprite_rot_cache):.0f}")

            # Minimal passed time to update the game.
            dt = min(self.clock.tick(FPS) / 1000.0, 0.05)

            # Handle all player input events.
            self._handle_events()
            # Update all (panels, player, creatuers, ui, combat feedback).
            self._update(dt)
            # After update now draw everything.
            self._draw()

        pygame.quit()
        sys.exit()


if __name__ == "__main__":
    Indie_Game().run()

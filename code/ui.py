import pygame
from settings import (
    COLOR_DMG_PHYSICAL, COLOR_DMG_MAGIC, COLOR_DMG_CRIT,
    COLOR_DMG_DOT, COLOR_DMG_BLOCK, COLOR_DMG_DODGE,
    COLOR_DMG_RESIST, COLOR_EXP,
    COLOR_HP_HIGH, COLOR_HP_MID, COLOR_HP_LOW,
    COLOR_HP_BG, COLOR_HP_BORDER,
    COLOR_ENERGY, COLOR_RAGE, COLOR_MANA,
    HP_BAR_W, HP_BAR_H, SUB_BAR_H, BAR_GAP, HP_BAR_OFFSET,
    DMG_FONT_SIZE, DMG_LIFETIME, DMG_RISE_SPEED,
    DMG_DRIFT_SPEED, DMG_WOBBLE_FREQ
)

class DamageNumber:

    _font = None   # shared font — loaded once

    # Called: UIManager._spawn_text().
    def __init__(self, text, world_x, world_y, color, index = 0):

        self.text     = str(text)
        self.world_x   = float(world_x)
        self.world_y   = float(world_y)
        self.color     = color
        self.elapsed   = 0.0
        self.alive     = True

        self._direction = 1 if index % 2 == 0 else -1
        self._drift_x   = 0.0

        self.screen_offset_y = 0  # extra upward offset in screen space

        font         = self.get_font()
        self._surf   = font.render(self.text, True, color)
        self._w      = self._surf.get_width()
        self._h      = self._surf.get_height()

    # Called: UIManager._draw_numbers().
    def draw(self, surface, camera):

        if not self.alive:
            return

        alpha = max(0, int(255 * (1.0 - self.elapsed / DMG_LIFETIME)))

        surf_copy = self._surf.copy()
        surf_copy.set_alpha(alpha)

        sx, sy = camera.world_to_screen(self.world_x, self.world_y, camera._player)
        screen_x = int(sx) - self._w // 2
        screen_y = int(sy) - self._h // 2 - int(self.elapsed * DMG_RISE_SPEED) - 40

        outline_surf = self.get_font().render(self.text, True, (0, 0, 0))
        outline_surf.set_alpha(alpha)
        for ox, oy in ((-1,0),(1,0),(0,-1),(0,1)):
            surface.blit(outline_surf, (screen_x + ox, screen_y + oy))

        surface.blit(surf_copy, (screen_x, screen_y))

    # Called: UIManager.update().
    def update(self, dt):

        self.elapsed += dt

        if self.elapsed >= DMG_LIFETIME:
            self.alive = False
            return

        half_period = 1.0 / (DMG_WOBBLE_FREQ * 2)
        wobble_phase = self.elapsed % (half_period * 2)
        if wobble_phase > half_period:
            if wobble_phase - dt < half_period:
                self._direction = -self._direction

        self.world_x  += self._direction * DMG_DRIFT_SPEED * dt


    # Called: __init__(), draw().
    @classmethod
    def get_font(cls):

        if cls._font is None:
            cls._font = pygame.font.SysFont(None, DMG_FONT_SIZE)
        return cls._font


class UIManager:

    # Called: Indie_Game.__init__().
    def __init__(self, camera):

        self._numbers       = []     # active DamageNumber instances
        self._spawn_count   = 0      # tracks index for alternating drift
        self._camera        = camera

    # Called: spawn(), CombatFeedback.process_player(), CombatFeedback.process_entities().
    def _spawn_text(self, text, world_x, world_y, color):

        number = DamageNumber(
            text, world_x, world_y, color,
            index = self._spawn_count
        )
        self._numbers.append(number)
        self._spawn_count += 1

    # Called: spawn_from_result(), spawn_dot(), spawn_exp().
    def spawn(self, value, world_x, world_y, kind = "physical"):

        if kind == "block":
            self._spawn_text("BLOCK",  world_x, world_y, COLOR_DMG_BLOCK)
        elif kind == "dodge_physical":
            self._spawn_text("DODGE",  world_x, world_y, COLOR_DMG_PHYSICAL)
        elif kind == "dodge_magic":
            self._spawn_text("DODGE",  world_x, world_y, COLOR_DMG_MAGIC)
        elif kind == "resist":
            self._spawn_text("RESIST", world_x, world_y, COLOR_DMG_RESIST)
        else:
            if value <= 0:
                return

            color = {
                "physical" : COLOR_DMG_PHYSICAL,
                "magic"  : COLOR_DMG_MAGIC,
                "crit"   : COLOR_DMG_CRIT,
                "dot"  : COLOR_DMG_DOT,
            }.get(kind, COLOR_DMG_PHYSICAL)

            self._spawn_text(str(int(value)), world_x, world_y, color)


    # Called: CombatFeedback.process_player(), CombatFeedback.process_entities().
    def spawn_from_result(self, result, world_x, world_y, is_magic = False):

        hit_type = result.get("hit_type", "normal")

        if hit_type == "resist":
            self.spawn(0, world_x, world_y, "resist")
        elif hit_type == "dodge":
            kind = "dodge_magic" if is_magic else "dodge_physical"
            self.spawn(0, world_x, world_y, kind)
        elif hit_type == "block":
            self.spawn(0, world_x, world_y, "block")
        elif result["damage"] > 0:
            if result["crit"]:
                self.spawn(result["damage"], world_x, world_y, "crit")
            elif is_magic:
                self.spawn(result["damage"], world_x, world_y, "magic")
            else:
                    self.spawn(result["damage"], world_x, world_y, "physical")

    # Called: CombatFeedback.process_player(), CombatFeedback.process_entities().
    def spawn_dot(self, value, world_x, world_y):

        self.spawn(value, world_x, world_y, "dot")

    # Called: CombatFeedback.process_entities().
    def spawn_exp(self, amount, world_x, world_y):

        self._spawn_text(f"EXP {int(amount)}", world_x, world_y, COLOR_EXP)


    # Called: draw().
    def _draw_hp_bars(self, surface, camera, entities):

        for entity in entities:

            if not entity.is_alive:
                continue

            if entity.state in ("idle_neutral", "wander", "notice", "exit_stance", "returning", "dying"):
                if entity.stats.hp >= entity.stats.hp_max:
                    continue

            if entity.state == "move" and entity.returning:
                if entity.stats.hp >= entity.stats.hp_max:
                    continue

            stats = entity.stats
            if stats.hp_max <= 0:
                continue

            # Convert entity world position to screen position via camera.
            sx, sy = camera.world_to_screen(
                entity.rect.centerx, entity.rect.centery, camera._player)
            screen_x = int(sx) - HP_BAR_W // 2

            energy_pct = min(1.0, stats.energy / stats.energy_max)
            has_energy = energy_pct < 1.0
            has_rage = stats.rage > 0
            has_mana = stats.spr > 0 and stats.mp_max > 0 and stats.mp < stats.mp_max
            has_sub = has_rage or has_mana

            total_h  = HP_BAR_H
            if has_energy:
                total_h += SUB_BAR_H + BAR_GAP
            if has_sub:
                total_h += BAR_GAP + SUB_BAR_H

            stack_top = int(sy) - HP_BAR_OFFSET - total_h - 40


            def draw_bar(y, h, pct, color):

                border = 1 if pct >= 1.0 else 2
                pygame.draw.rect(surface, COLOR_HP_BORDER,
                    pygame.Rect(screen_x - border, y - border,
                                HP_BAR_W + border * 2, h + border * 2))

                pygame.draw.rect(surface, COLOR_HP_BG,
                    pygame.Rect(screen_x, y, HP_BAR_W, h))

                fill_w = max(0, int(HP_BAR_W * min(1.0, pct)))
                if fill_w > 0:
                    pygame.draw.rect(surface, color,
                        pygame.Rect(screen_x, y, fill_w, h))

            cursor = stack_top

            if has_energy:
                draw_bar(cursor, SUB_BAR_H, energy_pct, COLOR_ENERGY)
                cursor += SUB_BAR_H + BAR_GAP

            hp_pct   = max(0.0, stats.hp / stats.hp_max)
            hp_color = (
                COLOR_HP_HIGH if hp_pct > 0.6 else
                COLOR_HP_MID  if hp_pct > 0.3 else
                COLOR_HP_LOW
            )

            draw_bar(cursor, HP_BAR_H, hp_pct, hp_color)
            cursor += HP_BAR_H + BAR_GAP

            if has_rage:
                draw_bar(cursor, SUB_BAR_H, stats.rage / stats.rage_max, COLOR_RAGE)
            elif has_mana:
                draw_bar(cursor, SUB_BAR_H,
                            max(0.0, stats.mp / stats.mp_max), COLOR_MANA)

    # Called: draw().
    def _draw_numbers(self, surface, camera):

        for number in self._numbers:
            number.draw(surface, camera)

    # Called: Indie_Game._draw().
    def draw(self, surface, camera, entities):

        self._draw_hp_bars(surface, camera, entities)
        self._draw_numbers(surface, camera)

    # Called: Indie_Game._update().
    def update(self, dt):

        for n in self._numbers:
            n.update(dt)
        self._numbers = [n for n in self._numbers if n.alive]

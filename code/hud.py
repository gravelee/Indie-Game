import pygame

from settings import (
    COLOR_HP_HIGH, COLOR_HP_MID, COLOR_HP_LOW, COLOR_HP_BG, COLOR_HP_BORDER,
    COLOR_ENERGY, COLOR_RAGE, COLOR_MANA,
)

# ── HUD layout ─────────────────────────────────────────────────
HUD_BAR_W      = 300    # pixels wide — wider than creature bars
HUD_HP_H       = 18     # HP bar height — tallest, most important
HUD_SUB_H      = 12     # energy and rage/mana bar height
HUD_BAR_GAP    = 6      # pixels between bars
HUD_BOTTOM_PAD = 40     # pixels from bottom of screen
HUD_FONT_SIZE  = 14     # number font size inside bars
HUD_RANK_SIZE  = 18     # rank title font size

# ── First real rank threshold ───────────────────────────────────
# Rank title only shows after player reaches this grade
FIRST_REAL_RANK = "E"   # matches RANKS in stats.py

class HUD:

    # Called: Indie_Game.__init__().
    def __init__(self, screen):

        self.screen   = screen
        self._font    = None
        self._font_rank = None


    # Called: draw()
    def _get_font(self):

        if self._font is None:
            self._font = pygame.font.SysFont(None, HUD_FONT_SIZE)
        return self._font

    # Called: draw()
    def _get_rank_font(self):

        if self._font_rank is None:
            self._font_rank = pygame.font.SysFont(None, HUD_RANK_SIZE)
        return self._font_rank

    # Called: draw()
    def _draw_bar(self, surface, x, y, w, h, pct, color,
                  value=0, show_num=True):
        """
        Draw a single HUD bar with optional centered number.
        Number fades in as bar empties — invisible when full.
        """
        border = 2

        # border
        pygame.draw.rect(surface, COLOR_HP_BORDER,
            pygame.Rect(x - border, y - border,
                        w + border * 2, h + border * 2))
        # background
        pygame.draw.rect(surface, COLOR_HP_BG,
            pygame.Rect(x, y, w, h))
        # fill
        fill_w = max(0, int(w * min(1.0, pct)))
        if fill_w > 0:
            pygame.draw.rect(surface, color,
                pygame.Rect(x, y, fill_w, h))

        # ── centered number — fades out when bar is full ───────
        if show_num and h >= HUD_FONT_SIZE - 2:
            font     = self._get_font()
            text     = str(value)
            surf     = font.render(text, True, (255, 255, 255))
            # outline
            outline  = font.render(text, True, (0, 0, 0))

            # alpha — fades as pct approaches 1.0
            # fully visible below 90%, fades between 90-100%
            if pct < 0.9:
                alpha = 255
            else:
                alpha = int(255 * (1.0 - (pct - 0.9) / 0.1))
                alpha = max(0, alpha)

            surf.set_alpha(alpha)
            outline.set_alpha(alpha)

            tx = x + (w - surf.get_width()) // 2
            ty = y + (h - surf.get_height()) // 2

            for ox, oy in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                surface.blit(outline, (tx + ox, ty + oy))
            surface.blit(surf, (tx, ty))


    # Called: Indie_Game._draw()
    def draw(self, player):

        stats  = player.stats
        screen = self.screen
        sw     = screen.get_width()
        sh     = screen.get_height()

        # ── stack calculation ──────────────────────────────────
        has_rage = stats.rage > 0
        has_mana = stats.spr > 0 and stats.mp_max > 0 and stats.mp < stats.mp_max
        has_sub  = has_rage or has_mana

        total_h  = HUD_SUB_H + HUD_BAR_GAP + HUD_HP_H
        if has_sub:
            total_h += HUD_BAR_GAP + HUD_SUB_H

        # anchor bottom center
        x         = (sw - HUD_BAR_W) // 2
        stack_bot = sh - HUD_BOTTOM_PAD
        stack_top = stack_bot - total_h

        cursor = stack_top

        # ── rank title — only after first real rank ────────────
        grade = stats.rank_grade
        if grade not in ("None",) and grade != "None":
            title_surf = self._get_rank_font().render(
                stats.rank_title, True, (220, 200, 120)
            )
            tx = (sw - title_surf.get_width()) // 2
            ty = cursor - title_surf.get_height() - 4
            screen.blit(title_surf, (tx, ty))

        # ── energy bar (top) ───────────────────────────────────
        display_energy = int(stats.energy)
        energy_pct = min(1.0, display_energy / stats.energy_max)
        self._draw_bar(
            screen, x, cursor, HUD_BAR_W, HUD_SUB_H,
            energy_pct, COLOR_ENERGY,
            value     = int(stats.energy),
            show_num  = energy_pct < 1.0
        )
        cursor += HUD_SUB_H + HUD_BAR_GAP

        # ── HP bar (middle) ────────────────────────────────────
        display_hp = int(stats.hp)
        hp_pct   = max(0.0, display_hp / stats.hp_max) if stats.hp_max > 0 else 0.0
        hp_color = (
            COLOR_HP_HIGH if hp_pct > 0.6 else
            COLOR_HP_MID  if hp_pct > 0.3 else
            COLOR_HP_LOW
        )
        self._draw_bar(
            screen, x, cursor, HUD_BAR_W, HUD_HP_H,
            hp_pct, hp_color,
            value    = int(stats.hp),
            show_num = hp_pct < 1.0
        )
        cursor += HUD_HP_H + HUD_BAR_GAP

        # ── rage or mana bar (bottom) ──────────────────────────
        if has_rage:
            display_rage = int(stats.rage)
            rage_pct = display_rage / stats.rage_max
            self._draw_bar(
                screen, x, cursor, HUD_BAR_W, HUD_SUB_H,
                rage_pct, COLOR_RAGE,
                value    = int(stats.rage),
                show_num = rage_pct < 1.0
            )
        elif has_mana:
            display_mana = int(stats.mp)
            mana_pct = max(0.0, display_mana / stats.mp_max)
            self._draw_bar(
                screen, x, cursor, HUD_BAR_W, HUD_SUB_H,
                mana_pct, COLOR_MANA,
                value    = int(stats.mp),
                show_num = mana_pct < 1.0
            )

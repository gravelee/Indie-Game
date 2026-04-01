# ═══════════════════════════════════════════════════════════════
#  DEBUG_PANEL.PY
#  Live stat inspector for any entity — player or creature.
#  Shows base stats, derived stats, resources, effects, state.
#
#  Player panel  — P key toggles, PAUSES everything when open
#  Creature panel — click to open, click elsewhere to close,
#                   game keeps running while open
# ═══════════════════════════════════════════════════════════════

import pygame

# ── Panel layout ───────────────────────────────────────────────
PANEL_W          = 280
PANEL_PADDING    = 12
PANEL_BG         = (15,  15,  20,  220)
PANEL_BORDER     = (80,  80, 100)
DIVIDER_COLOR    = (50,  50,  65)
LABEL_COLOR      = (140, 140, 160)
VALUE_COLOR      = (255, 255, 255)
TITLE_COLOR      = (200, 180, 100)
STATE_COLOR      = (100, 200, 120)
EFFECT_COLOR     = (255, 180,  50)

FONT_SIZE        = 15
TITLE_FONT_SIZE  = 17
LINE_H           = 18
SECTION_GAP      = 8

BAR_H            = 8
BAR_W            = PANEL_W - PANEL_PADDING * 2

COLOR_HP_HIGH    = (60,  200,  80)
COLOR_HP_MID     = (230, 200,  40)
COLOR_HP_LOW     = (220,  60,  60)
COLOR_ENERGY     = (255, 140,   0)
COLOR_RAGE       = (210,  40,  40)
COLOR_MANA       = ( 80, 120, 255)
COLOR_BAR_BG     = ( 30,  30,  40)
COLOR_BAR_BORDER = ( 60,  60,  80)


class StatPanel:
    """
    A debug stat panel for any entity with .stats, .state, .effects.

    pauses_game=True  → used for player panel (P key)
    pauses_game=False → used for creature panel (mouse click)
    """

    def __init__(self, screen, x, y, title="Entity", pauses_game = False):
        self.screen      = screen
        self.x           = x
        self.y           = y
        self.title       = title
        self.pauses_game = pauses_game
        self.entity      = None
        self.visible     = False
        self._font       = None
        self._font_title = None


    def _get_font(self):
        if self._font is None:
            self._font = pygame.font.SysFont("monospace", FONT_SIZE)
        return self._font

    def _get_title_font(self):
        if self._font_title is None:
            self._font_title = pygame.font.SysFont("monospace", TITLE_FONT_SIZE, bold=True)
        return self._font_title


    def set_entity(self, entity):
        self.entity = entity

    def toggle(self):
        self.visible = not self.visible

    def close(self):
        self.visible = False

    @property
    def is_open(self):
        return self.visible and self.entity is not None

    @property
    def should_pause(self):
        return self.is_open and self.pauses_game


    # ─────────────────────────────────────────────────────────
    #  DRAW
    # ─────────────────────────────────────────────────────────
    def draw(self):
        if not self.is_open:
            return

        # if entity died — auto close creature panel
        if hasattr(self.entity, 'dying') and self.entity.dying:
            self.close()
            return

        entity = self.entity
        stats  = entity.stats
        lines  = self._build_lines(entity, stats)
        panel_h = self._calc_height(lines)

        # background
        surf = pygame.Surface((PANEL_W, panel_h), pygame.SRCALPHA)
        surf.fill(PANEL_BG)
        self.screen.blit(surf, (self.x, self.y))

        # border
        pygame.draw.rect(self.screen, PANEL_BORDER,
            pygame.Rect(self.x, self.y, PANEL_W, panel_h), 1)

        # render lines
        cursor_y = self.y + PANEL_PADDING
        font  = self._get_font()
        tfont = self._get_title_font()

        for item in lines:
            kind = item[0]

            if kind == "title":
                s = tfont.render(item[1], True, TITLE_COLOR)
                self.screen.blit(s, (self.x + PANEL_PADDING, cursor_y))
                cursor_y += TITLE_FONT_SIZE + 4

            elif kind == "divider":
                pygame.draw.line(self.screen, DIVIDER_COLOR,
                    (self.x + PANEL_PADDING, cursor_y + 3),
                    (self.x + PANEL_W - PANEL_PADDING, cursor_y + 3))
                cursor_y += SECTION_GAP

            elif kind == "row":
                label = item[1]
                value = str(item[2])
                color = item[3] if len(item) > 3 else VALUE_COLOR
                ls = font.render(label, True, LABEL_COLOR)
                vs = font.render(value, True, color)
                self.screen.blit(ls, (self.x + PANEL_PADDING, cursor_y))
                self.screen.blit(vs, (self.x + PANEL_W - PANEL_PADDING - vs.get_width(), cursor_y))
                cursor_y += LINE_H

            elif kind == "bar":
                _, label, pct, color, cur, mx = item
                ls = font.render(label, True, LABEL_COLOR)
                self.screen.blit(ls, (self.x + PANEL_PADDING, cursor_y))
                val_txt = f"{int(cur)}/{int(mx)}"
                vs = font.render(val_txt, True, VALUE_COLOR)
                self.screen.blit(vs, (self.x + PANEL_W - PANEL_PADDING - vs.get_width(), cursor_y))
                cursor_y += LINE_H - 4
                bx = self.x + PANEL_PADDING
                by = cursor_y
                pygame.draw.rect(self.screen, COLOR_BAR_BORDER,
                    pygame.Rect(bx-1, by-1, BAR_W+2, BAR_H+2))
                pygame.draw.rect(self.screen, COLOR_BAR_BG,
                    pygame.Rect(bx, by, BAR_W, BAR_H))
                fw = max(0, int(BAR_W * min(1.0, max(0.0, pct))))
                if fw > 0:
                    pygame.draw.rect(self.screen, color,
                        pygame.Rect(bx, by, fw, BAR_H))
                cursor_y += BAR_H + 6

            elif kind == "text":
                color = item[2] if len(item) > 2 else VALUE_COLOR
                ts = font.render(item[1], True, color)
                self.screen.blit(ts, (self.x + PANEL_PADDING, cursor_y))
                cursor_y += LINE_H


    # ─────────────────────────────────────────────────────────
    #  PANEL HEIGHT CALCULATION
    # ─────────────────────────────────────────────────────────
    def _calc_height(self, lines):
        h = PANEL_PADDING * 2
        for item in lines:
            kind = item[0]
            if kind == "title":   h += TITLE_FONT_SIZE + 4
            elif kind == "divider": h += SECTION_GAP
            elif kind == "row":   h += LINE_H
            elif kind == "bar":   h += (LINE_H - 4) + BAR_H + 6
            elif kind == "text":  h += LINE_H
        return h


    # ─────────────────────────────────────────────────────────
    #  LINE BUILDER
    # ─────────────────────────────────────────────────────────
    def _build_lines(self, entity, stats):
        lines = []

        # ── title ─────────────────────────────────────────────
        name      = getattr(entity, 'name', self.title)
        grade     = stats.rank_grade
        line1     = f"{name}  Lv{stats.level}"
        line2     = f"{grade} {stats.rank_title}"
        lines.append(("title", line1))
        lines.append(("title", line2))
        lines.append(("divider",))

        # ── resources ─────────────────────────────────────────
        hp_pct = stats.hp / stats.hp_max if stats.hp_max > 0 else 0.0
        hp_col = (
            COLOR_HP_HIGH if hp_pct > 0.6 else
            COLOR_HP_MID  if hp_pct > 0.3 else
            COLOR_HP_LOW
        )
        lines.append(("bar", "HP",     hp_pct,
                       hp_col, stats.hp, stats.hp_max))
        lines.append(("bar", "Energy",
                       stats.energy / max(1, stats.energy_max),
                       COLOR_ENERGY, stats.energy, stats.energy_max))
        if stats.rage > 0:
            lines.append(("bar", "Rage",
                           stats.rage / max(1, stats.rage_max),
                           COLOR_RAGE, stats.rage, stats.rage_max))
        if stats.spr > 0 and stats.mp_max > 0:
            lines.append(("bar", "Mana",
                           stats.mp / max(1, stats.mp_max),
                           COLOR_MANA, stats.mp, stats.mp_max))

        lines.append(("divider",))

        # ── base stats ────────────────────────────────────────
        lines.append(("row", "STR", stats.str_))
        lines.append(("row", "AGI", stats.agi))
        lines.append(("row", "STA", stats.sta))
        lines.append(("row", "INT", stats.int_))
        lines.append(("row", "SPR", stats.spr))
        lines.append(("row", "RES", stats.res))
        lines.append(("row", "DEF", stats.def_))
        lines.append(("divider",))

        # ── derived stats ─────────────────────────────────────
        lines.append(("row", "PATK",   f"{stats.patk:.1f}"))
        lines.append(("row", "MATK",   f"{stats.matk:.1f}"))
        lines.append(("row", "PDEF",   f"{stats.pdef:.1f}"))
        lines.append(("row", "MDEF",   f"{stats.mdef:.1f}"))
        lines.append(("row", "CRIT",   f"{stats.crit:.1f}%"))
        lines.append(("row", "MCRIT",  f"{stats.mcrit:.1f}%"))
        lines.append(("row", "DODGE",  f"{stats.dodge:.1f}%"))
        lines.append(("row", "BLOCK",  f"{stats.block:.1f}%"))
        lines.append(("row", "RESIST", f"{stats.resist:.1f}%"))
        lines.append(("row", "MSPD",   f"{stats.mspd:.1f}"))
        lines.append(("divider",))

        # ── combat state ──────────────────────────────────────
        state     = getattr(entity, 'state', 'N/A')
        in_combat = getattr(entity, 'in_combat', None)
        lines.append(("row", "STATE", state, STATE_COLOR))
        if in_combat is not None:
            lines.append(("row", "IN COMBAT",
                           "YES" if in_combat else "NO",
                           (220, 60, 60) if in_combat else (100, 200, 120)))
        lines.append(("divider",))

        # ── exp and rank ──────────────────────────────────────
        lines.append(("row", "EXP",      stats.exp))
        lines.append(("row", "LIFETIME", stats.lifetime_exp))
        lines.append(("divider",))

        # ── active effects ────────────────────────────────────
        effects = getattr(entity, 'effects', None)
        if effects and len(effects) > 0:
            for eff in effects:
                txt = f"{eff.name}  x{eff.stacks}  {eff.time_remaining:.1f}s"
                lines.append(("text", txt, EFFECT_COLOR))
        else:
            lines.append(("text", "No active effects", LABEL_COLOR))

        return lines

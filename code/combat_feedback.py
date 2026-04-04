from settings import COLOR_EFFECT_TEXT, COLOR_EFFECT_FADE

class CombatFeedback():

    # Called: Indie_Game.__init__().
    def __init__(self, ui):

        self.ui = ui

    # Called: Indie_Game._update()
    def process_player(self, player):

        # ── attack result — damage numbers on target ──────────
        if player.last_hit and player.last_target:

            targets = player.last_target if isinstance(player.last_target, list) else [player.last_target]
            results = player.last_hit if isinstance(player.last_hit, list) else [player.last_hit]

            # Pair each result with its target (zip stops at the shorter one).
            for r, t in zip(results, targets):

                self.ui.spawn_from_result(
                    r, t.rect.centerx,
                    t.rect.top - 20,
                    is_magic = r.get("is_magic", False)
                )

                if r.get("effect"):
                    self.ui._spawn_text(
                        f"{r["effect"].split("_")[-1].capitalize()}",
                        t.rect.centerx,
                        t.rect.top - 35,
                        COLOR_EFFECT_TEXT
                    )

            player.last_hit    = None
            player.last_target = None

        # ── DoT ticks on player ───────────────────────────────
        if player.dot_damage > 0:
            self.ui.spawn_dot(
                player.dot_damage,
                player.rect.centerx,
                player.rect.top - 20
            )

        # ── effect fade text on player ────────────────────────
        for name in player.expired_effects:
            self.ui._spawn_text(
                f"{name.split("_")[-1].capitalize()}",
                player.rect.centerx,
                player.rect.top - 30,
                COLOR_EFFECT_FADE
            )

    # Called: Indie_Game._update()
    def process_entities(self, entities):

        # We give all active creatures here and interpret everyone.
        for entity in entities:

            # ── creature attack result — damage on player ─────
            if entity.last_hit:

                r = entity.last_hit
                target_rect = entity.target.rect
                self.ui.spawn_from_result(
                    r,
                    target_rect.centerx,
                    target_rect.top - 20,
                    is_magic = r.get("is_magic", False)
                )

                if r.get("effect"):
                    self.ui._spawn_text(
                        f"{r["effect"].split("_")[-1].capitalize()}",
                        target_rect.centerx,
                        target_rect.top - 35,
                        COLOR_EFFECT_TEXT
                    )
                entity.last_hit = None

            # ── EXP drop on death ─────────────────────────────
            if (entity.state =="dying") and not entity.exp_dropped and entity.stats.exp_reward > 0:
                self.ui.spawn_exp(
                    entity.stats.exp_reward,
                    entity.rect.centerx,
                    entity.rect.top - 20
                )
                entity.exp_dropped = True

            # ── DoT ticks on creature ─────────────────────────
            if entity.dot_damage > 0:
                self.ui.spawn_dot(
                    entity.dot_damage,
                    entity.rect.centerx,
                    entity.rect.top - 20
                )

            # ── effect fade text on creature ──────────────────
            for name in entity.expired_effects:
                self.ui._spawn_text(
                    f"{name.split("_")[-1].capitalize()}",
                    entity.rect.centerx,
                    entity.rect.top - 30,
                    COLOR_EFFECT_FADE
                )

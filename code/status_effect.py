import random
from statuses import STATUS_DATA

# Called: Ability.use(), Effect.update()
def roll(chance):
    return random.random() * 100 <= chance

class Effect:

    # Called: EffectManager.apply().
    def __init__(self, status_data, source = None):

        self.name       = status_data["name"]
        self.type       = status_data["type"]
        self.is_magic   = status_data["is_magic"]
        self.tick_dmg   = status_data["tick_dmg"]
        self.tick_rate  = status_data["tick_rate"]
        self.duration   = status_data["duration"]
        self.max_stacks = status_data["max_stacks"]
        self.color      = status_data["color"]
        self.flag       = status_data["flag"]
        self.stat       = status_data["stat"]
        self.modifier   = status_data["modifier"]

        self.source     = source

        self.stacks          = 1
        self.expired         = False
        self.tick_timer      = 0.0
        self.time_remaining  = self.duration
        self._original_value = None

    # Called EffectManager.apply()
    def reapply(self):

        self.time_remaining = self.duration
        if self.stacks < self.max_stacks:
            self.stacks += 1

    # Called EffectManager.apply()
    def on_apply(self, target_stats):

        if self.type == "modifier" and self.stat:
            self._original_value = getattr(target_stats, self.stat, None)
            if self._original_value is not None:
                setattr(target_stats, self.stat, self._original_value * self.modifier)

        elif self.type == "flag" and self.flag:
            setattr(target_stats, self.flag, True)

    # Called EffectManager.update(), EffectManager.cleanse(), EffectManager.cleanse_all()
    def on_remove(self, target_stats):

        if self.type == "modifier" and self.stat:
            if self._original_value is not None:
                setattr(target_stats, self.stat, self._original_value)

        elif self.type == "flag" and self.flag:
            setattr(target_stats, self.flag, False)

    # Called EffectManager.update()
    def update(self, dt, target_stats):

        if self.expired:
            return 0

        self.time_remaining -= dt
        damage_dealt = 0

        if self.type == "dot":
            self.tick_timer += dt
            if self.tick_timer >= self.tick_rate:
                self.tick_timer -= self.tick_rate

                tick = self.tick_dmg * self.stacks
                target_stats.hp = max(0, target_stats.hp - tick)
                damage_dealt = tick

        if self.time_remaining <= 0:
            self.expired = True
            self.on_remove(target_stats)

        return damage_dealt


    # Called: None.
    @property
    def duration_pct(self):

        return max(0.0, self.time_remaining / self.duration)


class EffectManager:

    # Called: EffectManager.apply().
    def __init__(self):

        self._active = []

    # Called: StatPanel._build_lines().
    def __iter__(self):
        return iter(self._active)

    # Called: StatPanel._build_lines().
    def __len__(self):
        return len(self._active)

    # Called: has(), apply(), cleanse()
    def _find(self, effect_name):
        for effect in self._active:
            if effect.name == effect_name:
                return effect
        return None

    # Called: None.
    def has(self, effect_name):

        return self._find(effect_name) is not None

    # Called: Ability.use()
    def apply(self, effect_name, target_stats, source = None):

        data = STATUS_DATA.get(effect_name)
        if data is None:
            return False

        existing = self._find(data["name"])
        if existing:
            existing.reapply()
            return True

        effect = Effect(data, source = source)
        effect.on_apply(target_stats)
        self._active.append(effect)
        return True

    # Called: None.
    def cleanse(self, effect_name, target_stats):

        effect = self._find(effect_name)
        if effect:
            effect.on_remove(target_stats)
            effect.expired = True
            self._active = [e for e in self._active if not e.expired]

    # Called: Creature._begin_death()
    def cleanse_all(self, target_stats):

        for effect in self._active:
            effect.on_remove(target_stats)
        self._active = []

    # Called: Creature.update(), Player.update()
    def update(self, dt, target_stats):

        total_damage = 0
        expired_names = []
        for effect in self._active:
            total_damage += effect.update(dt, target_stats)
            if effect.expired:
                expired_names.append(effect.name)

        self._active = [effect for effect in self._active if not effect.expired]

        return total_damage, expired_names

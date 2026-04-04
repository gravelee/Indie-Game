from status_effect import roll
from abilities import ABILITY_DATA

class Ability:

    # Called: get_ability()
    def __init__(self, name, level, damage_mult, cooldown, range_ , mp_cost,
        rage_cost, energy_cost, effect_name, effect_chance, anim, is_magic, description):

        self.name          = name
        self.level         = level
        self.damage_mult   = damage_mult
        self.cooldown      = cooldown
        self.range_        = range_
        self.mp_cost       = mp_cost
        self.rage_cost     = rage_cost
        self.energy_cost   = energy_cost
        self.effect_name   = effect_name
        self.effect_chance = effect_chance
        self.anim          = anim
        self.is_magic      = is_magic
        self.description   = description

        self._timer        = 0.0

    # Called: Entity._update_cooldowns().
    def tick(self, dt):

        # If the abilities cooldown is on update the timer.
        if self._timer > 0:
            self._timer = max(0.0, self._timer - dt)

    # Called: use(), Entity._ready_abilities().
    def can_use(self, user_stats, dist):

        return (
            self.ready
            and dist <= self.range_
            and user_stats.mp          >= self.mp_cost
            and user_stats.rage        >= self.rage_cost
            and user_stats.energy      >= self.energy_cost
        )

    # Called: Creature._attack(), Player.attack().
    def use(self, user_stats, targets, dist):

        # If out of range.
        if not self.can_use(user_stats, dist):
            return None

        # User pays the costs.
        user_stats.mp       -= self.mp_cost
        user_stats.rage     -= self.rage_cost
        user_stats.energy   -= self.energy_cost

        results = []

        # For every target in zone.
        for t in targets:

            result = {
                "damage"   : 0,
                "crit"     : False,
                "effect"   : None,
                "hit_type" : "normal",  # "normal", "dodge", "block", "resist" "miss"
                "is_magic": self.is_magic
            }

            # If attack is resisted.
            if self.is_magic and roll(t.stats.resist):
                result["hit_type"] = "resist"
                results.append(result)
                continue

            # If attack dodged.
            if roll(t.stats.dodge):
                result["hit_type"] = "dodge"
                results.append(result)
                continue

            # If attack blocked.
            if not self.is_magic and roll(t.stats.block):
                result["hit_type"] = "block"
                results.append(result)
                continue

            # Calculates the raw damage.
            base      = user_stats.matk if self.is_magic else user_stats.patk
            raw       = base * self.damage_mult

            # Check for critical damage.
            crit_stat = user_stats.mcrit if self.is_magic else user_stats.crit
            if roll(crit_stat):

                # Updates damage (x2).
                raw          *= 2.0
                result["crit"] = True

                # Update users rage.
                user_stats.rage = min(user_stats.rage_max, user_stats.rage + 2.0)
            else:
                user_stats.rage = min(user_stats.rage_max, user_stats.rage + 1.0)

            # Update damage based of targets defences.
            actual           = t.stats.take_damage(raw, self.is_magic, is_crit = result["crit"])
            result["damage"] = actual

            # Update targets rage.
            t.stats.rage = min(t.stats.rage_max, t.stats.rage + 1.0)

            # Calculate effects if exists.
            if self.effect_name and self.effect_chance > 0:

                # If attack succeed in effect roll.
                if roll(self.effect_chance):

                    # If ability not magical apply the effect immediatelly.
                    # If magical roll resist chance.
                    if not self.is_magic or not roll(t.stats.res):
                        t.effects.apply(
                            self.effect_name,
                            t.stats,
                            source = user_stats
                        )
                        result["effect"] = self.effect_name

            results.append(result)

        self._timer = self.cooldown
        return results


    # Called: can_use().
    @property
    def ready(self):

        return self._timer <= 0.0

    # Called: None.
    @property
    def cooldown_pct(self):

        return self._timer / self.cooldown if self.cooldown > 0 else 0.0


# Called: Creature.init(), Player.init().
def get_ability(ability_name, level = 1):

    data = ABILITY_DATA[ability_name]
    if data is None:
        return

    scale_fields = data.get("scale",[])
    scale_values = data.get("scale_value",[])

    damage_mult   = data["damage_mult"]
    cooldown      = data["cooldown"]
    range_        = data["range_"]
    mp_cost       = data["mp_cost"]
    rage_cost     = data["rage_cost"]
    energy_cost   = data["energy_cost"]
    effect_name   = data["effect_name"]
    effect_chance = data["effect_chance"]
    anim          = data["anim"]

    for field, value in zip(scale_fields, scale_values):
        gain = value * (level - 1)/ 99 # level 1 = no gain, level 100 = full gain

        if field == "damage_mult":
            damage_mult   += gain
        elif field == "cooldown":
            cooldown       = max(1.0, cooldown - gain)
        elif field == "range_":
            range_        += int(gain)
        elif field == "mp_cost":
            mp_cost       += gain
        elif field == "rage_cost":
            rage_cost     += gain
        elif field == "energy_cost":
            energy_cost   += gain
        elif field == "effect_chance":
            effect_chance += gain
        elif field == "effect_name":
            effect_name    = value        # string swap — no interpolation
        elif field == "anim":
            anim           = value        # string swap — no interpolation

    return Ability(
        name            = data["name"],
        level           = level,
        damage_mult     = damage_mult,
        cooldown        = cooldown,
        range_          = range_,
        mp_cost         = mp_cost,
        rage_cost       = rage_cost,
        energy_cost     = energy_cost,
        effect_name     = effect_name,
        effect_chance   = effect_chance,
        anim            = anim,
        is_magic        = data["is_magic"],
        description     = data["description"]
    )

import math
from settings import (
    W_STR, W_AGI, W_STA, W_INT,
    W_SPR, W_RES, W_DEF, LEVEL_DIVISOR,
    PLAYER_MOVEMENT_SPEED, BASE_MOVEMENT_SPEED
)

RANKS = [
    (0,    "None",  "Unranked"),
    (500,   "E",  "Novice"),
    (2000,  "D",  "Wanderer"),
    (8000,  "D+",  "Recruit"),
    (24000,  "C",  "Apprentice"),
    (72000,  "C+",  "Scout"),
    (150000, "B",  "Hunter"),
    (300000, "B+",  "Captain"),
    (900000, "A",  "General"),
    (3000000, "A+",  "Champion"),
    (12000000, "A++", "Elite"),
    (50000000, "S", "Master"),
    (250000000, "SS", "Legend"),
    (1250000000, "SSS", "Kami"),
]


class Stats:

    def __init__(self, str_, agi, sta, int_, spr, res, def_, is_player = False,
        energy = 0, hp = 0, rage = 0, mp = 0, exp = 0, lifetime_exp = 0):

        self.str_           = str_          # physical power
        self.agi            = agi           # speed, evasion, crit
        self.sta            = sta           # hp pool, dodge, block
        self.int_           = int_          # magical power
        self.spr            = spr           # mp pool, magic defense, magic crit — gates magic use
        self.res            = res           # magic resistance component
        self.def_           = def_          # physical defense, block component

        self.energy         = energy        # current energy. Cannot exceed max energy.
        self.hp             = hp            # current health. Cannot exceed max hp.
        self.rage           = rage          # current rage. Cannot exceed max rage.
        self.mp             = mp            # current mana. Cannot exceed max mana.
        self.exp            = exp           # exp resource - used to upgrade abilities.
        self.lifetime_exp   = lifetime_exp  # combat experience points. Determines Rank.

        if is_player:
            self.bms        = PLAYER_MOVEMENT_SPEED + 100   # cheat for testing
        else:
            self.bms        = BASE_MOVEMENT_SPEED   # base movement speed — race dependent floor (future update)

        self._recalculate_all()

        self.energy = (energy if energy > 0 else self.energy_max)   if energy < self.energy_max else self.energy_max
        self.hp     = (hp if hp > 0 else self.hp_max)               if hp < self.hp_max else self.hp_max
        self.rage   = (rage if rage > 0 else 0)                     if rage < self.rage_max else self.rage_max
        self.mp     = (mp if mp > 0 else self.mp_max)               if mp < self.mp_max else self.mp_max

        self.upgrade_history = []

    #   Called: _recalculate_all()
    def _calc_level(self):

        weighted = (
            self.str_ * W_STR +
            self.agi  * W_AGI +
            self.sta  * W_STA +
            self.int_ * W_INT +
            self.spr  * W_SPR +
            self.res  * W_RES +
            self.def_ * W_DEF
        )
        return 1 + int(weighted / LEVEL_DIVISOR)

    # Called: _recalculate_all()
    def _calc_energy_max(self):

        return 10 + (self.level * 1)

    # Called: _recalculate_all()
    def _calc_hp_max(self):

        return 20 + (self.sta * 2) + (self.level * 2)

    # Called: _recalculate_all()
    def _calc_rage_max(self):

        return 10 + (self.level * 1)

    # Called: _recalculate_all()
    def _calc_mp_max(self):

        return (self.spr * 2) + (self.level * 2)

    # Called: _recalculate_all()
    def _calc_patk(self):

        return (self.str_ * 3) + (self.level * 2)

    # Called: _recalculate_all()
    def _calc_matk(self):

        return (self.int_ * 3) + (self.level * 2)

    # Called: _recalculate_all()
    def _calc_pdef(self):

        return (self.def_ * 1) + (self.agi * 0.5)

    # Called: _recalculate_all()
    def _calc_mdef(self):

        return (self.res * 1) + (self.spr * 0.5)

    # Called: _recalculate_all()
    def _calc_crit(self):

        return self.agi * 0.1

    # Called: _recalculate_all()
    def _calc_mcrit(self):

        return self.spr * 0.1


    # Called: _recalculate_all()
    def _calc_dodge(self):

        raw = (self.agi * 0.1) + (self.sta * 0.1)
        return raw

    # Called: _recalculate_all()
    def _calc_block(self):

        raw = (self.def_ * 0.1) + (self.sta * 0.1)
        return raw

    # Called: _recalculate_all()
    def _calc_resist(self):

        return self.res * 0.1

    # Called: _recalculate_all()
    def _calc_mspd(self):

        return self.bms + (self.agi * 0.5)

    # Called: init()
    def _recalculate_all(self):

        self.level      = self._calc_level()

        self.energy_max = self._calc_energy_max()
        self.hp_max     = self._calc_hp_max()
        self.rage_max   = self._calc_rage_max()
        self.mp_max     = self._calc_mp_max()

        self.patk       = self._calc_patk()
        self.matk       = self._calc_matk()
        self.pdef       = self._calc_pdef()
        self.mdef       = self._calc_mdef()
        self.crit       = self._calc_crit()
        self.mcrit      = self._calc_mcrit()
        self.dodge      = self._calc_dodge()
        self.block      = self._calc_block()
        self.resist     = self._calc_resist()
        self.mspd       = self._calc_mspd()

    # Called: update_stat()
    def recalculate(self):

        old_energy  = self.energy
        old_hp      = self.hp
        old_rage    = self.rage
        old_mp      = self.mp

        self._recalculate_all()

        self.energy = old_energy
        self.hp     = old_hp
        self.rage   = old_rage
        self.mp     = old_mp

    # Called: restore_resource()
    def recalculate_max(self):

        if self.energy > self.energy_max:
            self.energy = self.energy_max

        if self.hp > self.hp_max:
            self.hp = self.hp_max

        if self.rage > self.rage_max:
            self.rage = self.rage_max

        if self.mp > self.mp_max:
            self.mp = self.mp_max

    # Called: None
    def restore_resource(self, resource_name, amount):

        acceptable_resources = ["energy","hp","rage","mp"]
        resource = getattr(self, resource_name)

        if resource_name not in acceptable_resources:
            return False

        if amount <= 0:
            return False

        setattr(self, resource_name, resource + amount)
        self.recalculate_max()
        return True

    # Called: upgrade_stat()
    def spend_resource(self, resource_name, amount):

        acceptable_resources = ["energy","hp","rage","mp","exp"]
        resource = getattr(self, resource_name)

        if resource_name not in acceptable_resources:
            return False

        if resource < amount:
            return False

        setattr(self, resource_name, resource - amount)
        return True

    # Called: Creature._begin_death()
    def gain_exp(self, amount):

        self.exp          += amount
        self.lifetime_exp += amount

    # Called: Ability.use()
    def take_damage(self, raw_damage, is_magic = False, is_crit = False):

        defense = self.mdef if is_magic else self.pdef
        actual    = max(2 if is_crit else 1, raw_damage - defense)
        actual = math.floor(actual + 0.4999)
        self.hp = max(0, self.hp - actual)

        return actual

    # Called: None
    def upgrade_stat(self, stat_name, exp_cost = None):

        valid = ('str_', 'agi', 'sta', 'int_', 'spr', 'res', 'def_')
        if stat_name not in valid:
            return False

        if stat_name in self.upgrade_history[-2:]:
            return False

        cost = exp_cost if exp_cost is not None else 0

        if not self.spend_resource("exp", cost):
            return False

        current = getattr(self, stat_name)
        setattr(self, stat_name, current + 1)

        self.upgrade_history.append(stat_name)
        if len(self.upgrade_history) > 2:
            self.upgrade_history.pop(0)

        self.recalculate()
        return True

    # Called: None
    def available_upgrades(self):

        valid = ('str_', 'agi', 'sta', 'int_', 'spr', 'res', 'def_')
        blocked = self.upgrade_history[-2:]
        return [s for s in valid if s not in blocked]

    @property
    def is_alive(self):

        return self.hp > 0

    @property
    def energy_pct(self):

        return self.energy / self.energy_max

    @property
    def hp_pct(self):

        return self.hp / self.hp_max

    @property
    def rage_pct(self):

        return self.rage / self.rage_max

    @property
    def mp_pct(self):

        return self.mp / self.mp_max if self.mp_max > 0 else 0.0

    @property
    def rank(self):

        result = (RANKS[0][1], RANKS[0][2])
        for threshold, grade, title in RANKS:
            if self.lifetime_exp >= threshold:
                result = (grade, title)
        return result

    @property
    def rank_grade(self):

        return self.rank[0]

    @property
    def rank_title(self):

        return self.rank[1]

    @property
    def exp_reward(self):

        mult = getattr(self, 'exp_multiplier', 1.0)
        return max(1, int(self.level * mult))

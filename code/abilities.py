from settings import MELEE_ATTACK_RANGE

ABILITY_DATA = {

    "player_slash": {
        "name": "Forward Slash",
        "damage_mult": 1.0,
        "cooldown": 2.0,
        "range_": MELEE_ATTACK_RANGE,
        "mp_cost": 0,
        "rage_cost": 0,
        "energy_cost": 1,
        "effect_name": None,
        "effect_chance": 0.0,
        "anim": "forward_slash",
        "is_magic": False,
        "description": "Physical attack damage x1.0, 2.0 sec cooldown, melee range, costs 1 energy, no effect, physical ability. Scales for damage +0.5 and cooldown -0.5 sec.",
        "scale": ["damage_mult", "cooldown"],
        "scale_value": [0.5, 0.5]
    },

    "rat_bite": {
        "name": "Bite",
        "damage_mult": 1.0,
        "cooldown": 2.0,
        "range_": MELEE_ATTACK_RANGE,
        "mp_cost": 0,
        "rage_cost": 0,
        "energy_cost": 1,
        "effect_name": "rat_bite_bleed",
        "effect_chance": 5.0,
        "anim": "attack_bite",
        "is_magic": False,
        "description": "Phisical attack damage x1, 2 sec cooldown, melee range, costs 1 energy, effect bleed, chance 5%, phisical ability. Scales for effect chance +10%.",
        "scale": ["effect_chance"],
        "scale_value": [10.0]
    },

    "rat_slash": {
        "name": "Slash",
        "damage_mult": 1.5,
        "cooldown": 6.0,
        "range_": MELEE_ATTACK_RANGE,
        "mp_cost": 0,
        "rage_cost": 0,
        "energy_cost": 1,
        "effect_name": None,
        "effect_chance": 0.0,
        "anim": "attack_slash",
        "is_magic": False,
        "description": "Phisical attack damage x1.5, 6.0 sec cooldown, melee range, costs 1 energy, no effects, phisical ability. Scales for cooldown -1 sec.",
        "scale": ["cooldown"],
        "scale_value": [1.0]
    },

    "snake_bite": {
        "name": "Bite",
        "damage_mult": 1.3,
        "cooldown": 2.5,
        "range_": MELEE_ATTACK_RANGE,
        "mp_cost": 0,
        "rage_cost": 1,
        "energy_cost": 1,
        "effect_name": "snake_bite_poison",
        "effect_chance": 5.0,
        "anim": "attack_bite",
        "is_magic": False,
        "description": "Phisical attack damage x1.3, 2.5 sec cooldown, melee range, costs 1 energy and 1 rage, effect poison, chance 5%, phisical ability. Scales for effect chance +5%.",
        "scale": ["effect_chance"],
        "scale_value": [5.0]
    },

    "snake_tail slam": {
        "name": "Tail Slam",
        "damage_mult": 1.8,
        "cooldown": 10,
        "range_": MELEE_ATTACK_RANGE,
        "mp_cost": 0,
        "rage_cost": 0,
        "energy_cost": 1,
        "effect_name": None,
        "effect_chance": 0.0,
        "anim": "attack_tail slam",
        "is_magic": False,
        "description": "Phisical attack damage x1.8, 10.0 sec cooldown, melee range, costs 1 energy, no effect, phisical ability. Scales for phisical attack damage +0.2% and cooldown - 2.0 sec.",
        "scale": ["damage_mult","cooldown"],
        "scale_value": [0.2,2.0]
    },


}

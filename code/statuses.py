
STATUS_DATA = {

    "rat_bite_bleed": {
        "name"       : "bleed",
        "type"       : "dot",
        "is_magic"   : False,
        "tick_dmg"   : 1,
        "tick_rate"  : 3.0,
        "duration"   : 15.0,
        "max_stacks" : 2,
        "color"      : (180, 30, 30),
        "flag"       : None,
        "stat"       : None,
        "modifier"   : 1.0
    },

    "snake_bite_poison": {
        "name"       : "poison",
        "type"       : "dot",
        "is_magic"   : False,
        "tick_dmg"   : 1,
        "tick_rate"  : 1.5,
        "duration"   : 15.0,
        "max_stacks" : 1,
        "color"      : (80, 180, 40),
        "flag"       : None,
        "stat"       : None,
        "modifier"   : 1.0
    },

    "creature_ability_burn": {
        "name"       : "burn",
        "type"       : "dot",
        "is_magic"   : True,
        "tick_dmg"   : 3,
        "tick_rate"  : 3.0,
        "duration"   : 12.0,
        "max_stacks" : 2,
        "color"      : (220, 100, 20),
        "flag"       : None,
        "stat"       : None,
        "modifier"   : 1.0
    },

    "creature_ability_stan": {
        "name"       : "stun",
        "type"       : "flag",
        "is_magic"   : False,
        "tick_dmg"   : 0,
        "tick_rate"  : 0,
        "duration"   : 2.0,
        "max_stacks" : 1,
        "color"      : (220, 220, 50),
        "flag"       : "stunned",
        "stat"       : None,
        "modifier"   : 1.0
     },

    "creature_ability_slow": {
        "name"       : "slow",
        "type"       : "modifier",
        "is_magic"   : True,
        "tick_dmg"   : 0,
        "tick_rate"  : 0,
        "duration"   : 4.0,
        "max_stacks" : 1,
        "color"      : (100, 100, 220),
        "flag"       : None,
        "stat"       : "mspd",
        "modifier"   : 0.5
    },

    "creature_ability_silence": {
        "name"       : "silence",
        "type"       : "flag",
        "is_magic"   : True,
        "tick_dmg"   : 0,
        "tick_rate"  : 0,
        "duration"   : 3.0,
        "max_stacks" : 1,
        "color"      : (160, 80, 200),
        "flag"       : "silenced",
        "stat"       : None,
        "modifier"   : 1.0
    },

    "creature_ability_weaken": {
        "name"       : "weaken",
        "type"       : "modifier",
        "is_magic"   : True,
        "tick_dmg"   : 0,
        "tick_rate"  : 0,
        "duration"   : 4.0,
        "max_stacks" : 1,
        "color"      : (180, 130, 50),
        "flag"       : None,
        "stat"       : "patk",
        "modifier"   : 0.8
    },

    "creature_ability_freeze": {
        "name"       : "freeze",
        "type"       : "flag",
        "is_magic"   : True,
        "tick_dmg"   : 0,
        "tick_rate"  : 0,
        "duration"   : 2.5,
        "max_stacks" : 1,
        "color"      : (150, 220, 255),
        "flag"       : "frozen",
        "stat"       : None,
        "modifier"   : 1.0
    },

    "creature_ability_blind": {
        "name"       : "blind",
        "type"       : "modifier",
        "is_magic"   : True,
        "tick_dmg"   : 0,
        "tick_rate"  : 0,
        "duration"   : 3.0,
        "max_stacks" : 1,
        "color"      : (80, 80, 80),
        "flag"       : None,
        "stat"       : "crit",
        "modifier"   : 0.0,           # removes crit entirely while blind
    },



}

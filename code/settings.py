# ═══════════════════════════════════════════════════════════════
#  SETTINGS.PY
#  All game constants in one place.
#  Change values here — they propagate everywhere automatically.
# ═══════════════════════════════════════════════════════════════

# ── Display ────────────────────────────────────────────────────
SCREEN_W     = 1920
SCREEN_H     = 1080
FPS          = 60

# ── World ──────────────────────────────────────────────────────
MAP_W        = 3200
MAP_H        = 3200
TILE_SIZE    = 32

# ── Sprite scale ───────────────────────────────────────────────
# 1 = native 32px  |  2 = 64px  |  3 = 96px
SPRITE_SCALE = 3

# ── Animation ──────────────────────────────────────────────────
ANIM_SPEED   = 0.10

# ── Obstacle ───────────────────────────────────────────────────
# TILE_SIZE x SPRITE_SCALE <=> OBSTACLE_SIZE (ex. 32x32 tile x scale = 3 => obstacle size = 1, scale = 5 => size = 2)
OBSTACLE_SIZE_MAX   = 2

# ── AI distances Creature ──────────────────────────────────────
# Must be CHASE_DIST >= NOTICE_DIST
NOTICE_COOLDOWN     = 3.0
HOME_MAX_DIST       = 2000
# Creature faces player in range.
NOTICE_DIRECTION    = 450
NOTICE_DIST         = 400
CHASE_DIST          = 900
ATTACK_DIST         = 60
HOME_DIST           = 16
FLEE_SPEED          = 200.0
BASE_MOVEMENT_SPEED = 100
# TILE_SIZE x SPRITE_SCALE <=> CREATURE_SIZE (ex. 32x32 tile x scale = 3 => creature size = 1, scale = 5 => size = 2)
CREATURE_SIZE_MAX   = 2

# ── Player ──────────────────────────────────────────────-------
FACING_CONE  = 180
PLAYER_MOVEMENT_SPEED = 120

# ── Global Ability Cooldown ────────────────────────────────────
GCD         = 1.0           # global cooldown in seconds

# ── Ability ranges ─────────────────────────────────────────────
MELEE_ATTACK_RANGE  = 60   # close combat
RANGED_SHORT        = 300   # short range (daggers, short bow)
RANGED_MEDIUM       = 600   # medium range (bow)
RANGED_LARGE        = 1000  # long range (sniper, magic bolt)
BUFF_RANGE          = 0     # self-cast, no range check needed

# ── Creature regen ─────────────────────────────────────────────
HP_REGEN      = 1.0
ENERGY_REGEN  = 1.0
RAGE_DECREASE = 1.0

# ── Stats weights ──────────────────────────────────────────────
W_STR         = 1.0
W_AGI         = 1.0
W_STA         = 1.0
W_INT         = 1.0
W_SPR         = 1.0
W_RES         = 1.0
W_DEF         = 1.0
LEVEL_DIVISOR = 7

# ── HP bars ────────────────────────────────────────────────────
HP_BAR_W      = 60    # pixels wide
HP_BAR_H      = 5     # pixels tall
SUB_BAR_H     = 3     # pixels tall — energy, rage, mana
BAR_GAP       = 3     # pixels between bars
HP_BAR_OFFSET = 12     # pixels above the sprite top edge

# ── Damage numbers ─────────────────────────────────────────────
DMG_FONT_SIZE    = 28
DMG_LIFETIME     = 1.2    # seconds before fully faded
DMG_RISE_SPEED   = 40     # pixels per second upward
DMG_DRIFT_SPEED  = 14     # pixels per second sideways
DMG_WOBBLE_FREQ  = 3.0    # how many direction changes per second

# ── Colors — damage numbers ────────────────────────────────────
COLOR_DMG_PHYSICAL = (255, 255, 255)   # white  — normal physical hit
COLOR_DMG_MAGIC    = (100, 160, 255)   # purple — magic hit
COLOR_DMG_CRIT     = (200, 50,  50)    # red — critical hit
COLOR_DMG_DOT      = (255, 220, 50)    # yellow — DoT tick
COLOR_DMG_BLOCK    = (255, 255, 255)   # white  — blocked physical hit
COLOR_DMG_DODGE    = (255, 255, 255)   # same color as attack type — shown as "dodge"
COLOR_DMG_RESIST   = (80,  120, 255)   # blue   — effect resisted
COLOR_EXP          = (130, 0, 220)     # purple — EXP reward on kill


# ── Colors — HP bars ───────────────────────────────────────────
COLOR_HP_HIGH     = (60,  200, 80)    # green  — above 60% HP
COLOR_HP_MID      = (230, 200, 40)    # yellow — 30–60% HP
COLOR_HP_LOW      = (220, 60,  60)    # red    — below 30%
COLOR_HP_BG       = (40,  40,  40)    # dark background of HP bar
COLOR_HP_BORDER   = (10,  10,  10)    # border around HP bar

# ── Colors — resource bars ─────────────────────────────────────
COLOR_ENERGY      = (255, 140, 0)     # orange — energy bar
COLOR_RAGE        = (210, 40,  40)    # red    — rage bar
COLOR_MANA        = (80,  120, 255)   # blue   — mana bar

# ── Colors — combat feedback text ──────────────────────────────
COLOR_EFFECT_TEXT = (200, 180, 50)
COLOR_EFFECT_FADE = (160, 160, 160)

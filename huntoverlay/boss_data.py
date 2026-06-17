"""Boss / bounty reference data (pure data, no Qt).

Hunt: Showdown 1896 lair bosses. Only fields the community broadly agrees
on are included — fire/poison resistance and practical tips. Banish-time
seconds and exact HP are intentionally omitted: they differ across sources
and shift between patches, so listing a wrong number would mislead.

Display labels go through i18n keys; this module stays language-agnostic
by exposing stable keys, and the UI layer translates them.

Verify against in-game text / current patch before trusting blindly.
"""

# Resistance markers used by the UI to pick an icon/label.
WEAK = "weak"        # takes extra damage from this type
IMMUNE = "immune"    # immune / no effect
NORMAL = "normal"    # no special interaction / unconfirmed

# Boss order for display.
BOSS_ORDER = ["butcher", "spider", "assassin", "scrapbeak"]

# Each boss: canonical English name + per-type resistance + tip keys.
# `fire` / `poison` are one of WEAK / IMMUNE / NORMAL.
# `name` is the English display name (also an i18n key for zh).
# `tips` are i18n keys describing how to fight it.
BOSSES = {
    "butcher": {
        "name": "Butcher",
        "fire": IMMUNE,
        "poison": NORMAL,
        "tips": [
            "Immune to fire — do not waste fire ammo.",
            "Weak to explosives and close-range shotguns.",
            "Slow mover; keep distance and lead with explosives.",
            "Enters a rage phase after heavy damage.",
        ],
    },
    "spider": {
        "name": "Spider",
        "fire": WEAK,
        "poison": IMMUNE,
        "tips": [
            "Weak to fire — molotovs, fire ammo, burning lamps.",
            "Immune to poison; antidote counters its poison spit.",
            "Dynamite is effective, especially while it clings to walls/ceiling.",
            "Can be bled out at low health.",
        ],
    },
    "assassin": {
        "name": "Assassin",
        "fire": WEAK,
        "poison": NORMAL,
        "tips": [
            "Weak to fire — burns even while split into a swarm.",
            "Use heavy melee (axe/hammer) during its swarm form.",
            "Watch its teleport pattern; strike when it reforms.",
        ],
    },
    "scrapbeak": {
        "name": "Scrapbeak",
        "fire": NORMAL,
        "poison": NORMAL,
        "tips": [
            "Scrap armor blocks part of firearm damage.",
            "Heavy melee bypasses the armor; weaker after losing armor pieces.",
            "Avoid his barbed wire — it slows and damages you.",
            "Enters a rage phase after heavy damage.",
        ],
    },
}


def boss_keys():
    """Boss keys in display order."""
    return list(BOSS_ORDER)


def get_boss(key: str):
    """Return the boss record for a key, or None if unknown."""
    return BOSSES.get(key)

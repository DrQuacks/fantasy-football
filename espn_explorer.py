from espn_api.football import League
import os
import pprint

# Load credentials
league = League(
    league_id=57220027,  # your league ID
    year=2022,
    espn_s2=os.getenv("ESPN_S2"),
    swid=os.getenv("ESPN_SWID")
)

# Helper to explore dictionary keys recursively
def explore(obj, depth=0):
    indent = "  " * depth
    if isinstance(obj, dict):
        for k, v in obj.items():
            print(f"{indent}{k}: {type(v).__name__}")
            if isinstance(v, (dict, list)):
                explore(v, depth + 1)
    elif isinstance(obj, list):
        for i, item in enumerate(obj[:5]):  # show only first 5 items
            print(f"{indent}[{i}] {type(item).__name__}")
            explore(item, depth + 1)

# Choose a player to inspect
target_name = "justin jefferson"

# Try to find the player object
players = league.player_info()
player = next((p for p in players.values() if target_name in p.name.lower()), None)

if not player:
    print(f"Player {target_name} not found.")
    exit()

print(f"\n🎯 Found player: {player.name}\n")

# Explore top-level attributes of the player
print("🔍 Top-level Player attributes:")
for attr in dir(player):
    if not attr.startswith("_") and not callable(getattr(player, attr)):
        print(f" - {attr}")

# Show weekly stats dictionary keys
print("\n📅 Available weekly stats keys:")
for week, stat in sorted(player.stats.items()):
    if isinstance(stat, dict):
        print(f"\nWeek {week}:")
        for k, v in stat.items():
            print(f"  {k}: {v}")
    else:
        print(f"Week {week}: {type(stat)}")

# Deep explore one week's stats
week_to_inspect = 1
print(f"\n🔬 Deep dive into week {week_to_inspect} stat object:")
pprint.pprint(player.stats.get(week_to_inspect, {}))

# Optional: Inspect `player.__dict__` for internal data
print("\n🧠 Internal player data (sanitized):")
for k, v in player.__dict__.items():
    if not callable(v) and not k.startswith("_"):
        print(f"{k}: {type(v).__name__}")

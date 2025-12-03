from ytdlp_jsc import solve

challenge_type = "n"
challenge = "ZdZIqFPQK-Ty8wId"
player_path = "players/3d3ba064-phone"

with open(player_path, "r", encoding="utf-8") as f:
    player = f.read()

result = solve(player=player, challenge_type=challenge_type, challenge=challenge)

print(result)

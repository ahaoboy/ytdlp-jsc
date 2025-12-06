#!/usr/bin/env python3
"""Command line interface for ytdlp-jsc."""

import sys
try:
    from ytdlp_jsc import solve_json
except ImportError:
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parents[1]))
    try:
        from ytdlp_jsc import solve_json
    except ImportError:
        solve_json = None


def main():
    if solve_json is None:
        print("ERROR: ytdlp_jsc module not found", file=sys.stderr)
        sys.exit(1)

    args = sys.argv[1:]

    if len(args) < 2:
        print(
            f"ERROR: Missing argument\n"
            f"usage: {sys.argv[0]} <player> [<type>:<request> ...]\n"
            f"  type: 'n' or 'sig'\n"
            f"example: ytdlp-jsc players/3d3ba064-phone n:ZdZIqFPQK-Ty8wId sig:xxxx",
            file=sys.stderr,
        )
        sys.exit(1)

    player_path = args[0]
    challenges = args[1:]

    # Read player file
    try:
        with open(player_path, "r", encoding="utf-8") as f:
            player = f.read()
    except FileNotFoundError:
        print(f"ERROR: Player file not found: {player_path}", file=sys.stderr)
        sys.exit(1)
    except IOError as e:
        print(f"ERROR: Failed to read player file: {e}", file=sys.stderr)
        sys.exit(1)

    # Call solve with player content and challenge list
    results = solve_json(player, challenges)
    print(results)


if __name__ == "__main__":
    main()

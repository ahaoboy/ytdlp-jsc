#!/usr/bin/env python3
"""Command line interface for ytdlp-jsc."""

import json
import sys
from ytdlp_jsc import solve


def main():
    args = sys.argv[1:]

    if len(args) < 2:
        print(
            f"ERROR: Missing argument\n"
            f"usage: {sys.argv[0]} <player> [<type>:<request> ...]\n"
            f"  type: 'n' or 'sig'\n"
            f"example: ytdlp-jsc players/3d3ba064-phone n:ZdZIqFPQK-Ty8wId sig:xxxx",
            file=sys.stderr
        )
        sys.exit(1)

    player_path = args[0]

    # Parse requests
    requests = {"n": [], "sig": []}

    for request in args[1:]:
        if ":" not in request:
            print(f"ERROR: Invalid request format: {request}", file=sys.stderr)
            print("Expected format: <type>:<challenge>", file=sys.stderr)
            sys.exit(1)

        req_type, challenge = request.split(":", 1)

        if req_type not in ("n", "sig"):
            print(f"ERROR: Unsupported request type: {req_type}", file=sys.stderr)
            sys.exit(1)

        requests[req_type].append(challenge)

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

    # Process each request type and collect results
    results = []

    for challenge_type in ("n", "sig"):
        for challenge in requests[challenge_type]:
            result = solve(player=player, challenge_type=challenge_type, challenge=challenge)
            results.append(json.loads(result))

    # Output combined results
    print(json.dumps(results))


if __name__ == "__main__":
    main()

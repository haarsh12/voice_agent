"""Plan or apply the reusable LiveKit resources for Exotel inbound calling."""

from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

import aiohttp


BACKEND_DIRECTORY = Path(__file__).resolve().parents[1]
if str(BACKEND_DIRECTORY) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIRECTORY))

from app.config.settings import MissingConfigurationError, get_settings  # noqa: E402
from app.telephony.livekit_exotel import sync_exotel_livekit  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Create or update LiveKit resources. Omit for a read-only plan.",
    )
    return parser.parse_args()


async def main() -> int:
    args = parse_args()
    try:
        result = await sync_exotel_livekit(get_settings(), apply=args.apply)
    except (MissingConfigurationError, ValueError, RuntimeError, aiohttp.ClientError) as error:
        print(f"Configuration failed: {error}", file=sys.stderr)
        return 2
    action = "Applied" if args.apply else "Planned"
    status = "changes required" if result.changed else "already up to date"
    print(
        f"{action}: {status}. trunk={result.trunk_id} "
        f"dispatch_rule={result.dispatch_rule_id}"
    )
    if not args.apply and result.changed:
        print("Review the values, then rerun with --apply to change LiveKit Cloud.")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))

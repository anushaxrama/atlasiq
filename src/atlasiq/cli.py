import argparse
import json
import logging

from .config import DEFAULT_LIMIT, DEFAULT_MONTH
from .db import bootstrap
from .ingest import ingest
from .operations import dbt, months, publish, validate


def main() -> None:
    parser = argparse.ArgumentParser(description="AtlasIQ reproducible batch warehouse")
    parser.add_argument(
        "command",
        choices=[
            "bootstrap",
            "ingest",
            "backfill",
            "transform",
            "validate",
            "publish",
            "serve",
            "demo",
            "insights",
        ],
    )
    parser.add_argument("--month", default=DEFAULT_MONTH)
    parser.add_argument("--start", default=DEFAULT_MONTH)
    parser.add_argument("--end", default=DEFAULT_MONTH)
    parser.add_argument(
        "--limit",
        type=int,
        default=DEFAULT_LIMIT,
        help="Deterministic bottom-k fingerprint sample; 0 loads full partition",
    )
    parser.add_argument("--refresh", action="store_true")
    parser.add_argument("--port", type=int, default=8020)
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    if args.command == "bootstrap":
        bootstrap()
    elif args.command == "ingest":
        print(json.dumps(ingest(args.month, args.limit, args.refresh)))
    elif args.command == "backfill":
        for month in months(args.start, args.end):
            print(json.dumps(ingest(month, args.limit, args.refresh)))
        dbt()
        publish()
    elif args.command == "transform":
        dbt()
    elif args.command == "validate":
        print(json.dumps(validate(), indent=2))
    elif args.command == "publish":
        publish()
    elif args.command == "serve":
        import uvicorn

        uvicorn.run("atlasiq.api:app", host="0.0.0.0", port=args.port)
    elif args.command == "demo":
        print(json.dumps(ingest(args.month, args.limit, args.refresh)))
        dbt()
        publish()
        print("Warehouse ready. Run: atlasiq serve")
    elif args.command == "insights":
        from .report import generate

        generate()


if __name__ == "__main__":
    main()

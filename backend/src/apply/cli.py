import sys

import uvicorn

from apply.config import get_settings


def cmd_dev() -> None:
    settings = get_settings()
    uvicorn.run(
        "apply.api.main:app",
        host="0.0.0.0",
        port=settings.apply_port,
        reload=True,
    )


def cmd_migrate() -> None:
    import subprocess

    result = subprocess.run(
        ["alembic", "-c", "src/apply/db/alembic.ini", "upgrade", "head"],
        check=False,
    )
    sys.exit(result.returncode)


def main() -> None:
    if len(sys.argv) < 2:
        print("usage: apply <dev|migrate>", file=sys.stderr)
        sys.exit(2)

    cmd = sys.argv[1]
    if cmd == "dev":
        cmd_dev()
    elif cmd == "migrate":
        cmd_migrate()
    else:
        print(f"unknown command: {cmd}", file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    main()

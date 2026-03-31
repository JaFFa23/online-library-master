from __future__ import annotations

import argparse
import asyncio
import sys

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.db import AsyncSessionMaker
from app.models.user import User, UserRole


EXIT_OK = 0
EXIT_ERROR = 1
EXIT_USAGE = 2        # argparse обычно использует 2
EXIT_NOT_FOUND = 3    # пользователя нет


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m app.cli",
        description="Online Library CLI tools",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    set_role = subparsers.add_parser(
        "set-role",
        help="Set user role by email",
    )
    set_role.add_argument(
        "--email",
        required=True,
        help="User email (unique)",
    )
    set_role.add_argument(
        "--role",
        required=True,
        choices=[r.value for r in UserRole],  # admin|client
        help="Role to set: admin|client",
    )

    return parser


async def cmd_set_role(email: str, role: str) -> int:
    email_norm = email.strip().lower()
    role_enum = UserRole(role)

    if not settings.database_url:
        print("ERROR: DATABASE_URL is not set", file=sys.stderr)
        return EXIT_ERROR

    async with AsyncSessionMaker() as session:  # type: AsyncSession
        res = await session.execute(select(User).where(User.email == email_norm))
        user = res.scalar_one_or_none()

        if user is None:
            print(f"User not found: {email_norm}", file=sys.stderr)
            return EXIT_NOT_FOUND

        old_role = user.role
        if old_role == role_enum:
            print(f"Role unchanged for {user.email}: {user.role.value}")
            return EXIT_OK

        user.role = role_enum
        await session.commit()
        await session.refresh(user)

        print(f"Role updated for {user.email}: {old_role.value} -> {user.role.value}")
        return EXIT_OK


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        if args.command == "set-role":
            return asyncio.run(cmd_set_role(email=args.email, role=args.role))

        print(f"Unknown command: {args.command}", file=sys.stderr)
        return EXIT_USAGE

    except SystemExit as e:
        # argparse может бросать SystemExit(2)
        code = int(getattr(e, "code", EXIT_USAGE))
        return code
    except KeyboardInterrupt:
        print("Interrupted", file=sys.stderr)
        return EXIT_ERROR
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return EXIT_ERROR


if __name__ == "__main__":
    raise SystemExit(main())

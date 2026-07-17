"""Compatibility entry point for running the Multicam CLI from the repository."""

from app.__main__ import main

if __name__ == "__main__":
    raise SystemExit(main())

"""Django development entry point; independent from camera processing."""

import os
import sys


def main() -> None:
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "app.web.settings")
    try:
        from django.core.management import execute_from_command_line
    except ImportError as error:
        raise SystemExit(
            "Django não está instalado neste ambiente. Use o Conda smart-environment e "
            'execute: python -m pip install -e ".[web]"'
        ) from error
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()

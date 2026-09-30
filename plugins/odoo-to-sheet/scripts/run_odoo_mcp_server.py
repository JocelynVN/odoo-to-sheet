"""Prepare the plugin's private Python runtime, then launch the MCP server."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


PLUGIN_DIR = Path(__file__).resolve().parents[1]
REPOSITORY_ROOT = PLUGIN_DIR.parents[1]
PROJECT_ROOT = REPOSITORY_ROOT if (REPOSITORY_ROOT / ".git").exists() else PLUGIN_DIR
ENV_DIR = PROJECT_ROOT / ".odoo2shet-env"
REQUIREMENTS = PLUGIN_DIR / "requirements.txt"


def runtime_python() -> Path:
    return ENV_DIR / ("Scripts/python.exe" if os.name == "nt" else "bin/python")


def run(command: list[str], *, quiet: bool = False) -> None:
    stdout = subprocess.DEVNULL if quiet else sys.stderr
    subprocess.run(command, check=True, stdout=stdout)


def main() -> None:
    python = runtime_python()
    if not python.is_file():
        ENV_DIR.parent.mkdir(parents=True, exist_ok=True)
        run([sys.executable, "-m", "venv", str(ENV_DIR)])
        python = runtime_python()

    try:
        run([str(python), "-m", "pip", "--version"], quiet=True)
    except subprocess.CalledProcessError:
        run([str(python), "-m", "ensurepip", "--upgrade"])

    # pip is idempotent: keep the existing venv, leave satisfied packages in place,
    # and install only dependencies missing from this exact requirements file.
    run([
        str(python), "-m", "pip", "install", "--disable-pip-version-check", "-q",
        "-r", str(REQUIREMENTS),
    ])

    child_env = os.environ.copy()
    child_env["ODOO2SHEET_ENV_DIR"] = str(ENV_DIR.resolve())
    child_env["ODOO2SHEET_PROJECT_ROOT"] = str(PROJECT_ROOT.resolve())
    server = PLUGIN_DIR / "scripts" / "odoo_mcp_server.py"
    return_code = subprocess.call(
        [str(python), str(server)], cwd=PLUGIN_DIR, env=child_env
    )
    raise SystemExit(return_code)


if __name__ == "__main__":
    try:
        main()
    except (OSError, subprocess.CalledProcessError) as exc:
        print(
            f"Odoo To Sheet could not prepare .odoo2shet-env: {exc}",
            file=sys.stderr,
            flush=True,
        )
        raise SystemExit(1) from None

"""Prepare the private Python runtime, then launch the Odoo To Sheet MCP server."""

from __future__ import annotations

import hashlib
import os
import subprocess
import sys
from pathlib import Path

from odoo_runtime import platform_details, runtime_python, select_runtime_env


PLUGIN_DIR = Path(__file__).resolve().parents[1]
REQUIREMENTS = PLUGIN_DIR / "requirements.txt"
ENV_DIR, ENV_LOCATION = select_runtime_env()
STAMP_NAME = ".odoo2sheet-requirements.sha256"


def run(command: list[str], *, quiet: bool = False) -> None:
    stdout = subprocess.DEVNULL if quiet else sys.stderr
    subprocess.run(command, check=True, stdout=stdout)


def declared_requirements() -> list[str]:
    if not REQUIREMENTS.is_file():
        return []
    return [
        line.strip()
        for line in REQUIREMENTS.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    ]


def requirements_digest() -> str:
    data = REQUIREMENTS.read_bytes() if REQUIREMENTS.is_file() else b""
    return hashlib.sha256(data).hexdigest()


def prepare_runtime() -> tuple[Path, str, str]:
    python = runtime_python(ENV_DIR)
    action = "reused"
    if not python.is_file():
        if ENV_DIR.exists():
            raise OSError(f"Runtime path exists but is not a valid Python environment: {ENV_DIR}")
        ENV_DIR.parent.mkdir(parents=True, exist_ok=True)
        run([sys.executable, "-m", "venv", str(ENV_DIR)])
        python = runtime_python(ENV_DIR)
        action = "created"

    digest = requirements_digest()
    stamp = ENV_DIR / STAMP_NAME
    previous_digest = stamp.read_text(encoding="utf-8").strip() if stamp.is_file() else ""
    requirements = declared_requirements()
    if requirements and previous_digest != digest:
        try:
            run([str(python), "-m", "pip", "--version"], quiet=True)
        except subprocess.CalledProcessError:
            run([str(python), "-m", "ensurepip", "--upgrade"])
        run([
            str(python), "-m", "pip", "install", "--disable-pip-version-check", "-q",
            "-r", str(REQUIREMENTS),
        ])
        action = "created_and_installed" if action == "created" else "dependencies_updated"
    if previous_digest != digest:
        stamp.write_text(digest + "\n", encoding="utf-8")
    return python, action, digest


def main() -> None:
    python, action, digest = prepare_runtime()
    details = platform_details()

    child_env = os.environ.copy()
    child_env["ODOO2SHEET_ENV_DIR"] = str(ENV_DIR.resolve())
    child_env["ODOO2SHEET_ENV_LOCATION"] = ENV_LOCATION
    child_env["ODOO2SHEET_RUNTIME_ACTION"] = action
    child_env["ODOO2SHEET_PLATFORM"] = details["display_name"]
    child_env["ODOO2SHEET_REQUIREMENTS_DIGEST"] = digest
    server = PLUGIN_DIR / "scripts" / "odoo_mcp_server.py"
    return_code = subprocess.call(
        [str(python), str(server)], cwd=PLUGIN_DIR, env=child_env
    )
    raise SystemExit(return_code)


if __name__ == "__main__":
    try:
        main()
    except (OSError, subprocess.CalledProcessError) as exc:
        details = platform_details()
        print(
            "Odoo To Sheet could not prepare its Python runtime "
            f"for {details['display_name']} at {ENV_DIR}: {exc}",
            file=sys.stderr,
            flush=True,
        )
        raise SystemExit(1) from None

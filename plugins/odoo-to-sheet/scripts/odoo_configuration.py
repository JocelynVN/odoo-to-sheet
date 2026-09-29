"""Create per-user Odoo connection profiles without printing credentials."""

from __future__ import annotations

import argparse
import getpass
from pathlib import Path
from urllib.parse import urlsplit

from odoo_connection import DEFAULT_OUTPUT_DIR, config_path, read_config, write_config


def save_profiles(profiles: dict) -> None:
    config = read_config(allow_missing=True)
    config["profiles"] = profiles
    write_config(config)


def read_existing_profiles() -> dict:
    return read_config(allow_missing=True)["profiles"]


def add_profile() -> None:
    profiles = read_existing_profiles()
    name = input("Profile name (for example company-prod): ").strip()
    if not name or any(char in name for char in "/\\\x00"):
        raise SystemExit("Choose a short profile name without slashes.")
    url = input("Odoo base URL (for example https://company.odoo.com): ").strip().rstrip("/")
    parsed = urlsplit(url)
    if parsed.scheme not in ("http", "https") or not parsed.hostname or parsed.username or parsed.password or parsed.query or parsed.fragment:
        raise SystemExit("Enter a valid http:// or https:// Odoo base URL without credentials or query parameters.")
    username = input("Odoo login/email: ").strip()
    if not username:
        raise SystemExit("Odoo login/email cannot be empty.")
    database = input("Database name (required for XML-RPC; often optional on Odoo 19): ").strip()
    print("Authentication: [1] API key  [2] password")
    auth_choice = input("Choose 1 or 2: ").strip()
    if auth_choice not in ("1", "2"):
        raise SystemExit("Choose 1 for API key or 2 for password.")
    auth_type = "api_key" if auth_choice == "1" else "password"
    secret = getpass.getpass("API key/password (input hidden): ")
    if not secret:
        raise SystemExit("Credential cannot be empty.")
    output_dir = input(f"CSV output folder [{DEFAULT_OUTPUT_DIR}]: ").strip()
    if not output_dir:
        output_dir = str(DEFAULT_OUTPUT_DIR)
    if name in profiles and input(f"Profile `{name}` exists. Replace it? [y/N]: ").strip().lower() != "y":
        raise SystemExit("No profile was changed.")
    profiles[name] = {
        "url": url,
        "database": database,
        "username": username,
        "auth_type": auth_type,
        "secret": secret,
        "output_dir": str(Path(output_dir).expanduser().resolve()),
    }
    save_profiles(profiles)
    print(f"Saved profile `{name}` in {config_path()}. The credential was not displayed.")
    print("Use the `list_connections` and `describe_model` plugin tools to confirm access.")


def list_profiles() -> None:
    profiles = read_existing_profiles()
    if not profiles:
        print("No Odoo connections are configured.")
        return
    for name, profile in sorted(profiles.items()):
        print(
            f"{name}: {profile.get('url', '')} | db={profile.get('database') or '(auto)'} "
            f"| auth={profile.get('auth_type', 'unknown')} | CSV={profile.get('output_dir', '')}"
        )


def remove_profile(name: str) -> None:
    profiles = read_existing_profiles()
    if name not in profiles:
        raise SystemExit(f"No profile named `{name}` exists.")
    if input(f"Remove local profile `{name}`? [y/N]: ").strip().lower() != "y":
        print("No profile was removed.")
        return
    del profiles[name]
    save_profiles(profiles)
    print(f"Removed local profile `{name}`.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Configure local Odoo connection profiles for Odoo To Sheet.")
    subparsers = parser.add_subparsers(dest="action", required=True)
    subparsers.add_parser("add", help="Add or replace a connection profile using a hidden credential prompt")
    subparsers.add_parser("list", help="List configured profile names and non-secret settings")
    remove_parser = subparsers.add_parser("remove", help="Remove a local connection profile")
    remove_parser.add_argument("name")
    args = parser.parse_args()
    if args.action == "add":
        add_profile()
    elif args.action == "list":
        list_profiles()
    else:
        remove_profile(args.name)


if __name__ == "__main__":
    main()

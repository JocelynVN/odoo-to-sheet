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
    name = input("Tên hồ sơ (ví dụ cong-ty-prod): ").strip()
    if not name or any(char in name for char in "/\\\x00"):
        raise SystemExit("Hãy chọn tên hồ sơ ngắn và không có dấu gạch chéo.")
    url = input("URL Odoo (ví dụ https://congty.odoo.com): ").strip().rstrip("/")
    parsed = urlsplit(url)
    if parsed.scheme not in ("http", "https") or not parsed.hostname or parsed.username or parsed.password or parsed.query or parsed.fragment:
        raise SystemExit("Hãy nhập URL Odoo hợp lệ bắt đầu bằng http:// hoặc https://, không kèm thông tin đăng nhập hay tham số truy vấn.")
    username = input("Email đăng nhập Odoo: ").strip()
    if not username:
        raise SystemExit("Email đăng nhập Odoo không được để trống.")
    database = input("Tên cơ sở dữ liệu (bắt buộc với XML-RPC; thường không cần trên Odoo 19): ").strip()
    print("Cách xác thực: [1] API key  [2] mật khẩu")
    auth_choice = input("Chọn 1 hoặc 2: ").strip()
    if auth_choice not in ("1", "2"):
        raise SystemExit("Hãy chọn 1 cho API key hoặc 2 cho mật khẩu.")
    auth_type = "api_key" if auth_choice == "1" else "password"
    secret = getpass.getpass("API key/mật khẩu (nội dung được ẩn): ")
    if not secret:
        raise SystemExit("Thông tin xác thực không được để trống.")
    output_dir = input(f"Thư mục lưu CSV [{DEFAULT_OUTPUT_DIR}]: ").strip()
    if not output_dir:
        output_dir = str(DEFAULT_OUTPUT_DIR)
    if name in profiles and input(f"Hồ sơ `{name}` đã tồn tại. Thay thế? [c/K]: ").strip().lower() != "c":
        raise SystemExit("Không thay đổi hồ sơ nào.")
    profiles[name] = {
        "url": url,
        "database": database,
        "username": username,
        "auth_type": auth_type,
        "secret": secret,
        "output_dir": str(Path(output_dir).expanduser().resolve()),
    }
    save_profiles(profiles)
    print(f"Đã lưu hồ sơ `{name}` tại {config_path()}. Thông tin xác thực không được hiển thị.")
    print("Dùng công cụ plugin `list_connections` và `check_connection` để kiểm tra đăng nhập; dùng `describe_model` để kiểm tra quyền truy cập model.")


def list_profiles() -> None:
    profiles = read_existing_profiles()
    if not profiles:
        print("Chưa cấu hình kết nối Odoo nào.")
        return
    for name, profile in sorted(profiles.items()):
        print(
            f"{name}: {profile.get('url', '')} | db={profile.get('database') or '(auto)'} "
            f"| auth={profile.get('auth_type', 'unknown')} | CSV={profile.get('output_dir', '')}"
        )


def remove_profile(name: str) -> None:
    profiles = read_existing_profiles()
    if name not in profiles:
        raise SystemExit(f"Không tìm thấy hồ sơ `{name}`.")
    if input(f"Xóa hồ sơ cục bộ `{name}`? [c/K]: ").strip().lower() != "c":
        print("Không xóa hồ sơ nào.")
        return
    del profiles[name]
    save_profiles(profiles)
    print(f"Đã xóa hồ sơ cục bộ `{name}`.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Cấu hình hồ sơ kết nối Odoo cục bộ cho Odoo To Sheet.")
    subparsers = parser.add_subparsers(dest="action", required=True)
    subparsers.add_parser("add", help="Thêm hoặc thay thế hồ sơ kết nối; thông tin xác thực được nhập ẩn")
    subparsers.add_parser("list", help="Liệt kê tên hồ sơ và thông tin cài đặt không bí mật")
    remove_parser = subparsers.add_parser("remove", help="Xóa hồ sơ kết nối cục bộ")
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

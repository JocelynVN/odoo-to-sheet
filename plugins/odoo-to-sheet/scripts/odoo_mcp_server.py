"""Small stdio MCP server exposing read-only Odoo discovery, metadata, and CSV export."""

from __future__ import annotations

import csv
import hashlib
import json
import os
import re
import shutil
import sys
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

from odoo_connection import (
    DEFAULT_OUTPUT_DIR,
    OdooClient,
    OdooError,
    config_path,
    get_profile,
    read_config,
    write_config,
)


SERVER_VERSION = "0.2.0"
PAGE_SIZE = 500
DEFAULT_MAX_RECORDS = 10_000
MAX_RECORDS = 50_000
CLEANUP_PREVIEW_LIMIT = 200
CLEANUP_ENV_NAME = ".odoo2shet-env"


TOOLS = [
    {
        "name": "discover_databases",
        "description": "Tìm tên database trên máy chủ Odoo sau khi người dùng cung cấp auth. Dùng hồ sơ đã lưu hoặc URL/API key của kết nối mới. Chỉ đọc danh sách; không sửa dữ liệu Odoo.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "profile": {"type": "string", "description": "Tên hồ sơ Odoo đã lưu; dùng thay cho URL và API key khi sửa hồ sơ hiện có."},
                "url": {"type": "string", "description": "URL gốc Odoo cho kết nối mới."},
                "api_key": {"type": "string", "writeOnly": True, "description": "API key Odoo cho kết nối mới; không hiển thị trong kết quả hoặc log."},
                "allow_http": {"type": "boolean", "description": "Chỉ đặt true sau khi người dùng xác nhận dùng HTTP không mã hóa."},
            },
            "additionalProperties": False,
        },
        "annotations": {"readOnlyHint": True, "destructiveHint": False, "openWorldHint": True},
    },
    {
        "name": "save_connection",
        "description": "Tạo hồ sơ kết nối Odoo mới trong tệp cấu hình cục bộ. Không bao giờ trả về hoặc ghi log API key. Ưu tiên HTTPS; chỉ lưu HTTP sau khi người dùng xác nhận.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "profile": {"type": "string", "description": "Tên hồ sơ ngắn, ví dụ cong-ty-prod."},
                "url": {"type": "string", "description": "URL gốc Odoo, không chứa thông tin đăng nhập hoặc tham số truy vấn."},
                "database": {"type": "string", "description": "Tên cơ sở dữ liệu; bắt buộc với XML-RPC và thường không cần với JSON-2 của Odoo 19."},
                "username": {"type": "string", "description": "Email đăng nhập Odoo."},
                "api_key": {"type": "string", "writeOnly": True, "description": "API key Odoo. Chỉ lưu trong tệp cấu hình cục bộ; không nhắc lại trong kết quả hoặc log."},
                "output_dir": {"type": "string", "description": "Thư mục CSV cục bộ (không bắt buộc). Mặc định ~/odoo2sheet-output."},
                "allow_http": {"type": "boolean", "description": "Chỉ đặt true sau khi người dùng xác nhận cố ý dùng kết nối HTTP không mã hóa."},
                "replace_existing": {"type": "boolean", "description": "Chỉ đặt true sau khi người dùng xác nhận thay thế hồ sơ cùng tên."},
                "confirm_clear_preferences": {"type": "boolean", "description": "Chỉ đặt true sau khi người dùng xác nhận xóa bộ lọc/cột đã lưu vì URL hoặc database thay đổi."},
            },
            "required": ["profile", "url", "username", "api_key"],
            "additionalProperties": False,
        },
        "annotations": {"readOnlyHint": False, "destructiveHint": False, "openWorldHint": True},
    },
    {
        "name": "update_connection",
        "description": "Cập nhật thông tin xác thực, URL, database hoặc thư mục CSV của hồ sơ Odoo đã lưu. Không bao giờ trả lại hoặc ghi log API key.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "profile": {"type": "string", "description": "Tên hồ sơ cục bộ cần cập nhật."},
                "url": {"type": "string", "description": "URL gốc Odoo mới."},
                "username": {"type": "string", "description": "Email đăng nhập Odoo mới."},
                "api_key": {"type": "string", "writeOnly": True, "description": "API key mới. Không hiển thị hoặc ghi log giá trị này."},
                "database": {"type": "string", "description": "Tên database mới. Để trống nếu người dùng muốn xóa giá trị hiện có."},
                "output_dir": {"type": "string", "description": "Thư mục CSV mới. Để trống để dùng ~/odoo2sheet-output."},
                "allow_http": {"type": "boolean", "description": "Chỉ đặt true sau khi người dùng xác nhận dùng HTTP không mã hóa."},
                "confirm_clear_preferences": {"type": "boolean", "description": "Chỉ đặt true sau khi người dùng xác nhận xóa bộ lọc/cột đã lưu vì đổi URL hoặc database."},
            },
            "required": ["profile"],
            "additionalProperties": False,
        },
        "annotations": {"readOnlyHint": False, "destructiveHint": False, "openWorldHint": False},
    },
    {
        "name": "remove_connection",
        "description": "Xóa một hồ sơ kết nối Odoo cục bộ và tùy chọn báo cáo đã lưu sau khi người dùng xác nhận rõ ràng. Không xóa các CSV đã xuất.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "profile": {"type": "string", "description": "Tên hồ sơ kết nối Odoo cục bộ cần xóa."},
                "confirm": {"type": "boolean", "description": "Chỉ đặt true sau khi người dùng xác nhận xóa."},
            },
            "required": ["profile", "confirm"],
            "additionalProperties": False,
        },
        "annotations": {"readOnlyHint": False, "destructiveHint": True, "openWorldHint": False},
    },
    {
        "name": "preview_local_cleanup",
        "description": "Xem trước cấu hình Odoo To Sheet, các tệp CSV trong thư mục output và thư mục môi trường cục bộ sẽ bị xóa khi dọn plugin. Không thay đổi dữ liệu.",
        "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False},
        "annotations": {"readOnlyHint": True, "destructiveHint": False, "openWorldHint": False},
    },
    {
        "name": "clean_local_data",
        "description": "Xóa cấu hình/tùy chọn Odoo To Sheet, các tệp CSV trong thư mục output đã xem trước và thư mục .odoo2shet-env của repo. Chỉ gọi sau preview và khi người dùng xác nhận đã sao lưu output cùng việc dọn dữ liệu.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "cleanup_id": {"type": "string", "minLength": 64, "maxLength": 64, "description": "Mã kế hoạch mới nhất do preview_local_cleanup trả về."},
                "backup_confirmed": {"type": "boolean", "description": "Chỉ đặt true sau khi người dùng xác nhận đã sao lưu output hoặc xác nhận rằng không có output cần sao lưu."},
                "confirm_cleanup": {"type": "boolean", "description": "Chỉ đặt true sau khi người dùng xác nhận xóa dữ liệu trong kế hoạch xem trước."},
            },
            "required": ["cleanup_id", "backup_confirmed", "confirm_cleanup"],
            "additionalProperties": False,
        },
        "annotations": {"readOnlyHint": False, "destructiveHint": True, "openWorldHint": False},
    },
    {
        "name": "list_connections",
        "description": "Liệt kê hồ sơ Odoo và trạng thái có URL, email, API key, database hay chưa. Không trả về email hoặc giá trị thông tin xác thực.",
        "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False},
        "annotations": {"readOnlyHint": True, "destructiveHint": False, "openWorldHint": False},
    },
    {
        "name": "check_connection",
        "description": "Kiểm tra xác thực và kết nối với Odoo bằng hồ sơ đã lưu, không đọc dữ liệu nghiệp vụ.",
        "inputSchema": {
            "type": "object",
            "properties": {"profile": {"type": "string", "description": "Tên hồ sơ kết nối Odoo cần kiểm tra."}},
            "required": ["profile"],
            "additionalProperties": False,
        },
        "annotations": {"readOnlyHint": True, "destructiveHint": False, "openWorldHint": True},
    },
    {
        "name": "get_report_preferences",
        "description": "Lấy domain và các cột được chọn lần gần nhất cho model Odoo và hồ sơ cục bộ, không trả về thông tin xác thực.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "profile": {"type": "string", "description": "Tên hồ sơ kết nối cục bộ đã cấu hình."},
                "model": {"type": "string", "description": "Tên kỹ thuật của model Odoo, ví dụ sale.report."},
            },
            "required": ["profile", "model"],
            "additionalProperties": False,
        },
        "annotations": {"readOnlyHint": True, "destructiveHint": False, "openWorldHint": False},
    },
    {
        "name": "save_report_preferences",
        "description": "Lưu domain và các cột đã chọn để dùng lại trên máy này. Trường được kiểm tra với metadata trực tiếp của model trước khi lưu.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "profile": {"type": "string", "description": "Tên hồ sơ kết nối cục bộ đã cấu hình."},
                "model": {"type": "string", "description": "Tên kỹ thuật của model Odoo, ví dụ sale.report."},
                "domain": {"type": "array", "items": {}, "description": "Domain ORM Odoo đầy đủ theo lựa chọn của người dùng."},
                "fields": {"type": "array", "minItems": 1, "items": {"type": "string"}, "description": "Tên kỹ thuật các trường đã chọn từ describe_model."},
                "order": {"type": "string", "description": "Thứ tự trường phân cách bằng dấu phẩy; có thể kèm asc/desc."},
                "max_records": {"type": "integer", "minimum": 1, "maximum": MAX_RECORDS, "description": "Số dòng tối đa cho mỗi lần xuất."},
            },
            "required": ["profile", "model", "domain", "fields"],
            "additionalProperties": False,
        },
        "annotations": {"readOnlyHint": False, "destructiveHint": False, "openWorldHint": False},
    },
    {
        "name": "find_models",
        "description": "Tìm model Odoo theo tên kỹ thuật hoặc tên hiển thị. Tra cứu ir.model và trả về danh sách ngắn để xác định model trước khi đọc dữ liệu nghiệp vụ.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "profile": {"type": "string", "description": "Tên hồ sơ kết nối Odoo cục bộ đã cấu hình."},
                "query": {"type": "string", "description": "Từ hoặc cụm từ trong tên kỹ thuật/tên hiển thị của model (không bắt buộc). Để trống để xem các model có sẵn."},
                "max_results": {"type": "integer", "minimum": 1, "maximum": 100, "description": "Số model tối đa trả về (mặc định 30, giới hạn cứng 100)."},
            },
            "required": ["profile"],
            "additionalProperties": False,
        },
        "annotations": {"readOnlyHint": True, "destructiveHint": False, "openWorldHint": False},
    },
    {
        "name": "describe_model",
        "description": "Đọc tên trường, nhãn, kiểu dữ liệu, quan hệ và lựa chọn của model ORM Odoo bằng fields_get.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "profile": {"type": "string", "description": "Tên hồ sơ kết nối cục bộ đã cấu hình."},
                "model": {"type": "string", "description": "Tên kỹ thuật model Odoo, ví dụ sale.order."},
            },
            "required": ["profile", "model"],
            "additionalProperties": False,
        },
        "annotations": {"readOnlyHint": True, "destructiveHint": False, "openWorldHint": False},
    },
    {
        "name": "export_csv",
        "description": "Đọc bản ghi từ một model Odoo bằng search_read rồi lưu các trường đã chọn thành CSV UTF-8 trong thư mục xuất cục bộ của hồ sơ. Công cụ không gọi các phương thức write/create/unlink của Odoo.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "profile": {"type": "string", "description": "Tên hồ sơ kết nối cục bộ đã cấu hình."},
                "model": {"type": "string", "description": "Tên kỹ thuật model Odoo, ví dụ sale.order."},
                "fields": {"type": "array", "items": {"type": "string"}, "description": "Một hoặc nhiều tên kỹ thuật trường trực tiếp trả về từ describe_model."},
                "domain": {"type": "array", "items": {}, "description": "Mảng domain Odoo, có toán tử tiền tố khi cần; mặc định []."},
                "order": {"type": "string", "description": "Danh sách trường phân cách bằng dấu phẩy, có thể kèm asc/desc; mặc định id asc."},
                "max_records": {"type": "integer", "minimum": 1, "maximum": MAX_RECORDS, "description": f"Số dòng tối đa (mặc định {DEFAULT_MAX_RECORDS}, giới hạn cứng {MAX_RECORDS})."},
                "filename": {"type": "string", "description": "Tên tệp CSV tùy chọn; thành phần thư mục bị bỏ qua. Nếu không nhập, tên có dấu thời gian sẽ được tạo."},
            },
            "required": ["profile", "model", "fields"],
            "additionalProperties": False,
        },
    },
]


def _text_result(value: Any, *, is_error: bool = False) -> dict[str, Any]:
    return {"content": [{"type": "text", "text": json.dumps(value, ensure_ascii=False, default=str)}], "isError": is_error}


def _require_plugin_runtime() -> None:
    configured_env = os.environ.get("ODOO2SHEET_ENV_DIR")
    if not configured_env:
        raise OdooError("Môi trường tool chưa được khởi tạo. Hãy khởi động lại plugin để chuẩn bị .odoo2shet-env.")
    env_dir = Path(configured_env).expanduser().resolve()
    if not env_dir.is_dir() or Path(sys.prefix).resolve() != env_dir:
        raise OdooError("Tool chưa chạy trong .odoo2shet-env. Hãy khởi động lại plugin để dùng đúng môi trường đã cài.")


def _handle_list_connections() -> dict[str, Any]:
    profiles = read_config(allow_missing=True)["profiles"]
    items = []
    for name, profile in sorted(profiles.items()):
        items.append({
            "name": name,
            "url": profile.get("url", ""),
            "database": profile.get("database") or None,
            "auth_type": profile.get("auth_type", "unknown"),
            "has_url": bool(profile.get("url")),
            "has_email": bool(profile.get("username")),
            "has_api_key": bool(profile.get("secret")) and profile.get("auth_type") == "api_key",
            "has_database": bool(profile.get("database")),
            "output_dir": profile.get("output_dir") or str(DEFAULT_OUTPUT_DIR.resolve()),
        })
    return {"connections": items}


def _handle_check_connection(args: dict[str, Any]) -> dict[str, Any]:
    profile_name = args.get("profile")
    if not isinstance(profile_name, str) or not profile_name.strip():
        raise OdooError("Hãy chọn tên hồ sơ từ kết quả list_connections.")
    profile_name = profile_name.strip()
    profile = get_profile(profile_name)
    try:
        OdooClient(profile_name, profile).check_connection()
    except OdooError as exc:
        message = str(exc)
        authentication_error = (
            "Xác thực Odoo thất bại" in message
            or "HTTP 401" in message
            or "từ chối xác thực" in message.lower()
        )
        return {
            "connected": False,
            "authentication_error": authentication_error,
            "profile": profile_name,
            "database": profile.get("database") or None,
            "message": message,
        }
    return {
        "connected": True,
        "authentication_error": False,
        "profile": profile_name,
        "database": profile.get("database") or None,
        "message": "Đăng nhập Odoo thành công.",
    }


def _handle_discover_databases(args: dict[str, Any]) -> dict[str, Any]:
    profile_name = args.get("profile")
    if isinstance(profile_name, str) and profile_name.strip():
        if "url" in args or "api_key" in args:
            raise OdooError("Dùng hồ sơ đã lưu hoặc thông tin kết nối mới, không kết hợp cả hai cách.")
        profile = dict(get_profile(profile_name.strip()))
    else:
        url = args.get("url")
        api_key = args.get("api_key")
        if not isinstance(url, str) or not isinstance(api_key, str) or not api_key.strip():
            raise OdooError("Cung cấp hồ sơ đã lưu hoặc URL Odoo cùng API key để tìm database.")
        url = url.strip().rstrip("/")
        parsed = urlsplit(url)
        if parsed.scheme not in ("http", "https") or not parsed.hostname or parsed.username or parsed.password or parsed.query or parsed.fragment:
            raise OdooError("Hãy nhập URL gốc Odoo hợp lệ, không kèm thông tin đăng nhập hoặc tham số truy vấn.")
        if parsed.scheme == "http" and args.get("allow_http") is not True:
            raise OdooError("URL này dùng HTTP không mã hóa. Hãy giải thích rủi ro và chờ người dùng xác nhận trước khi tiếp tục.")
        profile = {
            "url": url,
            "database": "",
            "username": "",
            "auth_type": "api_key",
            "secret": api_key.strip(),
            "output_dir": str(DEFAULT_OUTPUT_DIR.resolve()),
        }

    # Database discovery must not constrain JSON-2 to an already selected database.
    profile["database"] = ""
    try:
        databases = OdooClient(profile_name or "database-discovery", profile).list_databases()
    except OdooError as exc:
        return {"available": False, "databases": [], "message": str(exc)}
    return {"available": True, "databases": databases, "count": len(databases)}


def _handle_save_connection(args: dict[str, Any]) -> dict[str, Any]:
    profile_name = args.get("profile")
    url = args.get("url")
    username = args.get("username")
    api_key = args.get("api_key")
    database = args.get("database", "")
    if not isinstance(profile_name, str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,63}", profile_name.strip()):
        raise OdooError("Tên hồ sơ chỉ được gồm chữ cái, chữ số, dấu chấm, gạch dưới hoặc gạch ngang (tối đa 64 ký tự).")
    profile_name = profile_name.strip()
    if not isinstance(url, str):
        raise OdooError("Vui lòng cung cấp URL dịch vụ Odoo.")
    url = url.strip().rstrip("/")
    parsed = urlsplit(url)
    if parsed.scheme not in ("https", "http") or not parsed.hostname or parsed.username or parsed.password or parsed.query or parsed.fragment:
        raise OdooError("Hãy nhập URL gốc Odoo hợp lệ (ưu tiên https://), không chứa thông tin đăng nhập hoặc tham số truy vấn.")
    if parsed.scheme == "http" and args.get("allow_http") is not True:
        raise OdooError("URL này dùng HTTP không mã hóa. Hãy giải thích rủi ro và chờ người dùng xác nhận trước khi lưu với allow_http=true.")
    if not isinstance(username, str) or not username.strip():
        raise OdooError("Vui lòng cung cấp email đăng nhập Odoo.")
    if not isinstance(api_key, str) or not api_key.strip():
        raise OdooError("Vui lòng cung cấp API key Odoo. Giá trị trống nên chưa được lưu.")
    if not isinstance(database, str):
        raise OdooError("Tên cơ sở dữ liệu phải là văn bản.")

    config = read_config(allow_missing=True)
    profiles = config["profiles"]
    if profile_name in profiles and args.get("replace_existing") is not True:
        raise OdooError(f"Hồ sơ `{profile_name}` đã tồn tại. Hãy hỏi người dùng muốn thay thế hay chọn tên khác.")
    output_dir = args.get("output_dir", "")
    if not isinstance(output_dir, str):
        raise OdooError("Thư mục lưu CSV phải là văn bản.")
    profile = {
        "url": url,
        "database": database.strip(),
        "username": username.strip(),
        "auth_type": "api_key",
        "secret": api_key.strip(),
        "output_dir": str(Path(output_dir).expanduser().resolve()) if output_dir.strip() else str(DEFAULT_OUTPUT_DIR.resolve()),
    }
    previous = profiles.get(profile_name)
    previous_database = str(previous.get("database", "")).strip() if isinstance(previous, dict) else ""
    connection_changed = isinstance(previous, dict) and (
        str(previous.get("url", "")).rstrip("/") != profile["url"]
        or bool(previous_database and previous_database != profile["database"])
    )
    preferences_exist = bool(config["report_preferences"].get(profile_name))
    report_preferences_cleared = bool(connection_changed and preferences_exist)
    if report_preferences_cleared and args.get("confirm_clear_preferences") is not True:
        raise OdooError("Đổi URL hoặc database sẽ xóa bộ lọc/cột báo cáo đã lưu cho hồ sơ này. Hãy hỏi người dùng xác nhận trước khi lưu thay đổi.")
    if report_preferences_cleared:
        config["report_preferences"].pop(profile_name, None)
    profiles[profile_name] = profile
    write_config(config)
    return {
        "saved": True,
        "profile": profile_name,
        "url": url,
        "database": database.strip() or None,
        "output_dir": profile["output_dir"],
        "config_file": str(config_path()),
        "credential": "đã lưu cục bộ; không hiển thị trong kết quả",
        "report_preferences_cleared": bool(report_preferences_cleared),
    }


def _handle_update_connection(args: dict[str, Any]) -> dict[str, Any]:
    profile_name = args.get("profile")
    if not isinstance(profile_name, str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,63}", profile_name.strip()):
        raise OdooError("Hãy chọn tên hồ sơ kết nối hợp lệ.")
    profile_name = profile_name.strip()

    has_url = "url" in args
    has_username = "username" in args
    has_api_key = "api_key" in args
    has_database = "database" in args
    has_output_dir = "output_dir" in args
    if not any((has_url, has_username, has_api_key, has_database, has_output_dir)):
        raise OdooError("Hãy cung cấp ít nhất một giá trị cần cập nhật.")
    if has_url and not isinstance(args["url"], str):
        raise OdooError("URL Odoo phải là văn bản.")
    if has_username and (not isinstance(args["username"], str) or not args["username"].strip()):
        raise OdooError("Email đăng nhập Odoo không được để trống.")
    if has_api_key and (not isinstance(args["api_key"], str) or not args["api_key"].strip()):
        raise OdooError("API key Odoo không được để trống; giá trị trống chưa được lưu.")
    if has_database and not isinstance(args["database"], str):
        raise OdooError("Tên database phải là văn bản.")
    if has_output_dir and not isinstance(args["output_dir"], str):
        raise OdooError("Thư mục CSV phải là văn bản.")

    config = read_config()
    profile = config["profiles"].get(profile_name)
    if not isinstance(profile, dict):
        raise OdooError(f"Không tìm thấy hồ sơ Odoo `{profile_name}`.")

    updated_fields: list[str] = []
    connection_identity_changed = False
    report_preferences_cleared = False
    if has_url:
        url = args["url"].strip().rstrip("/")
        parsed = urlsplit(url)
        if parsed.scheme not in ("https", "http") or not parsed.hostname or parsed.username or parsed.password or parsed.query or parsed.fragment:
            raise OdooError("Hãy nhập URL gốc Odoo hợp lệ, không chứa thông tin đăng nhập hoặc tham số truy vấn.")
        if parsed.scheme == "http" and args.get("allow_http") is not True:
            raise OdooError("URL này dùng HTTP không mã hóa. Hãy giải thích rủi ro và chờ người dùng xác nhận trước khi tiếp tục.")
        if str(profile.get("url", "")).rstrip("/") != url:
            connection_identity_changed = bool(profile.get("url"))
            profile["url"] = url
            updated_fields.append("url")

    if has_username:
        username = args["username"].strip()
        if profile.get("username") != username:
            profile["username"] = username
            updated_fields.append("username")

    if has_api_key:
        api_key = args["api_key"].strip()
        if profile.get("secret") != api_key or profile.get("auth_type") != "api_key":
            profile["secret"] = api_key
            profile["auth_type"] = "api_key"
            updated_fields.append("api_key")

    if has_database:
        database = args["database"].strip()
        previous_database = str(profile.get("database", "")).strip()
        if previous_database != database:
            connection_identity_changed = connection_identity_changed or bool(previous_database)
            profile["database"] = database
            updated_fields.append("database")

    if has_output_dir:
        output_dir_value = args["output_dir"].strip()
        output_dir = (
            str(Path(output_dir_value).expanduser().resolve())
            if output_dir_value
            else str(DEFAULT_OUTPUT_DIR.resolve())
        )
        if str(profile.get("output_dir", "")) != output_dir:
            profile["output_dir"] = output_dir
            updated_fields.append("output_dir")

    preferences_exist = bool(config["report_preferences"].get(profile_name))
    report_preferences_cleared = bool(connection_identity_changed and preferences_exist)
    if report_preferences_cleared and args.get("confirm_clear_preferences") is not True:
        raise OdooError("Đổi URL hoặc database sẽ xóa bộ lọc/cột báo cáo đã lưu cho hồ sơ này. Hãy hỏi người dùng xác nhận trước khi cập nhật.")

    if report_preferences_cleared:
        config["report_preferences"].pop(profile_name, None)
    if updated_fields:
        write_config(config)

    return {
        "updated": bool(updated_fields),
        "profile": profile_name,
        "updated_fields": updated_fields,
        "has_url": bool(profile.get("url")),
        "has_email": bool(profile.get("username")),
        "has_api_key": bool(profile.get("secret")) and profile.get("auth_type") == "api_key",
        "has_database": bool(profile.get("database")),
        "database": profile.get("database") or None,
        "output_dir": profile.get("output_dir") or str(DEFAULT_OUTPUT_DIR.resolve()),
        "config_file": str(config_path()),
        "credential": "được lưu cục bộ và không hiển thị",
        "report_preferences_cleared": report_preferences_cleared,
    }


def _handle_remove_connection(args: dict[str, Any]) -> dict[str, Any]:
    profile_name = args.get("profile")
    if not isinstance(profile_name, str) or not profile_name.strip():
        raise OdooError("Hãy chọn tên hồ sơ trong kết quả list_connections.")
    if args.get("confirm") is not True:
        raise OdooError("Người dùng chưa xác nhận xóa. Hãy hỏi trước khi xóa hồ sơ này.")
    config = read_config()
    profile_name = profile_name.strip()
    if profile_name not in config["profiles"]:
        raise OdooError(f"Không tìm thấy hồ sơ kết nối Odoo `{profile_name}`.")
    del config["profiles"][profile_name]
    config["report_preferences"].pop(profile_name, None)
    write_config(config)
    return {
        "removed": True,
        "profile": profile_name,
        "config_file": str(config_path()),
        "csv_files_removed": False,
    }


def _cleanup_config_state() -> tuple[dict[str, Any], dict[str, Any] | None]:
    path = config_path().expanduser()
    state: dict[str, Any] = {
        "path": str(path),
        "exists": path.exists() or path.is_symlink(),
        "symlink": path.is_symlink(),
        "profiles": [],
        "report_preference_profiles": [],
        "report_preference_count": 0,
        "other_keys": [],
        "size": None,
        "mtime_ns": None,
    }
    raw: dict[str, Any] | None = None
    if not state["exists"] or state["symlink"]:
        return state, raw
    try:
        stat = path.stat()
        parsed = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise OdooError(f"Không thể xem trước tệp cấu hình Odoo To Sheet tại {path}: {exc}") from None
    if not isinstance(parsed, dict):
        raise OdooError(f"Tệp cấu hình Odoo To Sheet tại {path} không phải đối tượng JSON.")
    profiles = parsed.get("profiles", {})
    preferences = parsed.get("report_preferences", {})
    if not isinstance(profiles, dict) or not isinstance(preferences, dict):
        raise OdooError(f"Tệp cấu hình Odoo To Sheet tại {path} có cấu trúc profiles/report_preferences không hợp lệ.")
    state.update({
        "profiles": sorted(str(name) for name in profiles),
        "report_preference_profiles": sorted(str(name) for name in preferences),
        "report_preference_count": len(preferences),
        "other_keys": sorted(str(key) for key in parsed if key not in {"profiles", "report_preferences"}),
        "size": stat.st_size,
        "mtime_ns": stat.st_mtime_ns,
    })
    raw = parsed
    return state, raw


def _cleanup_environment_path() -> Path:
    configured = os.environ.get("ODOO2SHEET_ENV_DIR")
    if configured:
        return Path(configured).expanduser()
    root = Path(__file__).resolve().parents[3]
    return root / CLEANUP_ENV_NAME


def _absolute_path(path: Path) -> Path:
    return Path(os.path.abspath(str(path.expanduser())))


def _build_cleanup_plan() -> dict[str, Any]:
    config_state, raw_config = _cleanup_config_state()
    config = raw_config or {"profiles": {}, "report_preferences": {}}
    profiles = config.get("profiles", {})
    if not isinstance(profiles, dict):
        profiles = {}

    output_paths = {_absolute_path(DEFAULT_OUTPUT_DIR)}
    for profile in profiles.values():
        if isinstance(profile, dict) and isinstance(profile.get("output_dir"), str) and profile["output_dir"].strip():
            output_paths.add(_absolute_path(Path(profile["output_dir"])))

    output_dirs: list[dict[str, Any]] = []
    planned_files: list[dict[str, Any]] = []
    for directory in sorted(output_paths, key=str):
        info: dict[str, Any] = {
            "path": str(directory),
            "exists": directory.exists() or directory.is_symlink(),
            "symlink": directory.is_symlink(),
            "csv_count": 0,
            "csv_bytes": 0,
            "csv_files": [],
            "listed_files_truncated": False,
            "skipped": False,
        }
        if info["exists"] and (info["symlink"] or not directory.is_dir()):
            info["skipped"] = True
        elif info["exists"]:
            try:
                files = sorted(
                    (item for item in directory.iterdir() if item.suffix.lower() == ".csv" and not item.is_symlink() and item.is_file()),
                    key=lambda item: item.name.casefold(),
                )
                for item in files:
                    stat = item.stat()
                    entry = {"path": str(item), "size": stat.st_size, "mtime_ns": stat.st_mtime_ns}
                    planned_files.append(entry)
                    info["csv_count"] += 1
                    info["csv_bytes"] += stat.st_size
                    if len(info["csv_files"]) < CLEANUP_PREVIEW_LIMIT:
                        info["csv_files"].append({"name": item.name, "size": stat.st_size})
                info["listed_files_truncated"] = len(files) > CLEANUP_PREVIEW_LIMIT
            except OSError as exc:
                raise OdooError(f"Không thể xem trước thư mục output {directory}: {exc}") from None
        output_dirs.append(info)

    env_path = _cleanup_environment_path()
    env_state = {
        "path": str(env_path),
        "exists": env_path.exists() or env_path.is_symlink(),
        "symlink": env_path.is_symlink(),
        "directory": env_path.is_dir() if not env_path.is_symlink() else False,
        "mtime_ns": env_path.stat().st_mtime_ns if env_path.exists() and not env_path.is_symlink() else None,
    }
    env_state["deletable"] = bool(env_state["exists"] and env_state["directory"] and env_path.name == CLEANUP_ENV_NAME)

    fingerprint_data = {
        "config": config_state,
        "output_dirs": output_dirs,
        "files": planned_files,
        "environment": env_state,
    }
    fingerprint = hashlib.sha256(
        json.dumps(fingerprint_data, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    return {
        "cleanup_id": fingerprint,
        "config": config_state,
        "output_dirs": output_dirs,
        "files": planned_files,
        "environment": env_state,
        "raw_config": raw_config,
    }


def _handle_preview_local_cleanup() -> dict[str, Any]:
    plan = _build_cleanup_plan()
    return {
        "cleanup_id": plan["cleanup_id"],
        "config": plan["config"],
        "output_dirs": plan["output_dirs"],
        "total_csv_files": len(plan["files"]),
        "total_csv_bytes": sum(item["size"] for item in plan["files"]),
        "environment": plan["environment"],
        "scope": "Chỉ xóa các CSV ngay trong những thư mục được liệt kê; không xóa thư mục con hoặc tệp không phải CSV.",
    }


def _handle_clean_local_data(args: dict[str, Any]) -> dict[str, Any]:
    if args.get("backup_confirmed") is not True or args.get("confirm_cleanup") is not True:
        raise OdooError("Chỉ dọn dữ liệu sau khi người dùng xác nhận đã sao lưu output (hoặc xác nhận không có output cần sao lưu) và xác nhận xóa kế hoạch đã xem trước.")
    cleanup_id = args.get("cleanup_id")
    if not isinstance(cleanup_id, str) or not re.fullmatch(r"[a-f0-9]{64}", cleanup_id):
        raise OdooError("Thiếu mã kế hoạch hợp lệ. Hãy gọi preview_local_cleanup trước.")
    plan = _build_cleanup_plan()
    if plan["cleanup_id"] != cleanup_id:
        raise OdooError("Dữ liệu đã thay đổi sau khi xem trước. Chưa xóa gì; hãy gọi preview_local_cleanup lại rồi hỏi người dùng xác nhận lần nữa.")

    removed_csvs: list[str] = []
    errors: list[dict[str, str]] = []
    for entry in plan["files"]:
        path = Path(entry["path"])
        try:
            current = path.stat()
            if path.is_symlink() or current.st_size != entry["size"] or current.st_mtime_ns != entry["mtime_ns"]:
                errors.append({"path": str(path), "error": "Tệp thay đổi sau khi xem trước; được giữ lại."})
                continue
            path.unlink()
            removed_csvs.append(str(path))
        except FileNotFoundError:
            errors.append({"path": str(path), "error": "Tệp không còn tồn tại; hãy xem trước lại để xác nhận trạng thái."})
        except OSError as exc:
            errors.append({"path": str(path), "error": str(exc)})

    for directory in plan["output_dirs"]:
        path = Path(directory["path"])
        if directory["skipped"]:
            errors.append({"path": str(path), "error": "Không thể xem/xóa thư mục output an toàn; dữ liệu được giữ lại."})
        if path == _absolute_path(DEFAULT_OUTPUT_DIR) and path.is_dir() and not path.is_symlink():
            try:
                path.rmdir()
            except OSError:
                pass

    env_state = plan["environment"]
    removed_env = False
    if env_state["exists"]:
        env_path = Path(env_state["path"])
        if env_state["deletable"] and not env_path.is_symlink():
            try:
                shutil.rmtree(env_path)
                removed_env = True
            except OSError as exc:
                errors.append({"path": str(env_path), "error": f"Không thể xóa môi trường đang dùng: {exc}"})
        else:
            errors.append({"path": str(env_path), "error": "Đường dẫn môi trường không phải thư mục an toàn có tên .odoo2shet-env; được giữ lại."})

    config_state = plan["config"]
    removed_config = False
    preserved_other_config = False
    config_path_value = Path(config_state["path"])
    if config_state["exists"]:
        if config_state["symlink"]:
            errors.append({"path": str(config_path_value), "error": "Tệp cấu hình là symbolic link; được giữ lại để tránh xóa đích không rõ."})
        else:
            raw_config = plan["raw_config"] or {}
            try:
                if config_state["other_keys"]:
                    raw_config["profiles"] = {}
                    raw_config["report_preferences"] = {}
                    write_config(raw_config)
                    preserved_other_config = True
                else:
                    config_path_value.unlink()
                    removed_config = True
                    if config_path_value.parent.name == "odoo2sheet":
                        try:
                            config_path_value.parent.rmdir()
                        except OSError:
                            pass
            except OSError as exc:
                errors.append({"path": str(config_path_value), "error": str(exc)})

    return {
        "cleanup_completed": not errors,
        "config_file_removed": removed_config,
        "other_config_keys_preserved": preserved_other_config,
        "csv_files_removed": len(removed_csvs),
        "removed_paths_preview": removed_csvs[:CLEANUP_PREVIEW_LIMIT],
        "removed_paths_truncated": len(removed_csvs) > CLEANUP_PREVIEW_LIMIT,
        "environment_removed": removed_env,
        "errors": errors,
    }


def _handle_get_report_preferences(args: dict[str, Any]) -> dict[str, Any]:
    profile_name = args.get("profile")
    model = args.get("model")
    if not isinstance(profile_name, str) or not profile_name.strip():
        raise OdooError("Hãy chọn hồ sơ kết nối từ kết quả list_connections.")
    if not isinstance(model, str) or not re.fullmatch(r"[A-Za-z0-9_.]+", model):
        raise OdooError("Vui lòng cung cấp tên model Odoo hợp lệ.")
    config = read_config(allow_missing=True)
    if profile_name not in config["profiles"]:
        raise OdooError(f"Không tìm thấy hồ sơ kết nối Odoo `{profile_name}`.")
    preference = config["report_preferences"].get(profile_name, {}).get(model)
    if not isinstance(preference, dict):
        return {"found": False, "profile": profile_name, "model": model}
    return {"found": True, "profile": profile_name, "model": model, **preference}


def _handle_save_report_preferences(args: dict[str, Any]) -> dict[str, Any]:
    profile_name, client = _get_client(args)
    model = args.get("model")
    fields = args.get("fields")
    domain = args.get("domain")
    if not isinstance(model, str) or not re.fullmatch(r"[A-Za-z0-9_.]+", model):
        raise OdooError("Vui lòng cung cấp tên model Odoo hợp lệ.")
    if not isinstance(fields, list) or not fields or any(not isinstance(field, str) or not field.strip() for field in fields):
        raise OdooError("Hãy chọn ít nhất một trường trong kết quả describe_model.")
    if not isinstance(domain, list):
        raise OdooError("Domain Odoo phải là một mảng JSON.")
    metadata = client.fields_get(model)
    normalized_fields = list(dict.fromkeys(field.strip() for field in fields))
    unknown_fields = [field for field in normalized_fields if field not in metadata]
    if unknown_fields:
        raise OdooError(f"Các trường sau không có trong `{model}`: {', '.join(unknown_fields)}. Hãy gọi describe_model trước.")
    order = args.get("order", "id asc")
    if not isinstance(order, str) or not order.strip():
        order = "id asc"
    max_records = args.get("max_records", DEFAULT_MAX_RECORDS)
    if not isinstance(max_records, int) or isinstance(max_records, bool) or not 1 <= max_records <= MAX_RECORDS:
        raise OdooError(f"max_records phải nằm trong khoảng từ 1 đến {MAX_RECORDS}.")

    config = read_config()
    preferences = config["report_preferences"].setdefault(profile_name, {})
    preferences[model] = {
        "domain": domain,
        "fields": normalized_fields,
        "order": order,
        "max_records": max_records,
        "updated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
    }
    write_config(config)
    return {
        "saved": True,
        "profile": profile_name,
        "model": model,
        "field_count": len(normalized_fields),
        "config_file": str(config_path()),
    }


def _get_client(args: dict[str, Any]) -> tuple[dict[str, Any], OdooClient]:
    profile_name = args.get("profile")
    if not isinstance(profile_name, str) or not profile_name.strip():
        raise OdooError("Hãy chọn hồ sơ kết nối từ kết quả list_connections.")
    profile = get_profile(profile_name.strip())
    return profile, OdooClient(profile_name.strip(), profile)


def _handle_describe_model(args: dict[str, Any]) -> dict[str, Any]:
    _, client = _get_client(args)
    model = args.get("model")
    metadata = client.fields_get(model)
    fields = []
    for name, info in sorted(metadata.items()):
        item = {"name": name, "label": info.get("string") or name, "type": info.get("type")}
        if info.get("relation"):
            item["relation"] = info["relation"]
        if info.get("selection"):
            item["selection"] = info["selection"]
        fields.append(item)
    return {"model": model, "fields": fields}


def _handle_find_models(args: dict[str, Any]) -> dict[str, Any]:
    _, client = _get_client(args)
    query = args.get("query", "")
    if not isinstance(query, str):
        raise OdooError("Nội dung tìm model phải là văn bản.")
    query = query.strip()
    limit = args.get("max_results", 30)
    if not isinstance(limit, int) or isinstance(limit, bool) or not 1 <= limit <= 100:
        raise OdooError("max_results must be between 1 and 100.")

    domain: list[Any] = [["transient", "=", False]]
    if query:
        domain.extend(["|", ["model", "ilike", query], ["name", "ilike", query]])
    try:
        records = client.search_read("ir.model", domain, ["model", "name"], limit, 0, "name asc")
    except OdooError as exc:
        raise OdooError(
            "Không thể tìm trong ir.model. Người dùng Odoo có thể chưa được cấp quyền xem metadata model. "
            f"Hãy nhờ quản trị viên cấp quyền đọc hoặc cung cấp tên kỹ thuật model. Chi tiết: {exc}"
        ) from None
    return {
        "query": query or None,
        "models": [{"model": row.get("model"), "name": row.get("name")} for row in records],
        "max_results_reached": len(records) == limit,
    }


def _csv_value(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, list) and len(value) == 2 and isinstance(value[0], int):
        return f"{value[1]} (id: {value[0]})"
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False, separators=(",", ":"), default=str)
    return str(value)


def _safe_filename(value: str | None, model: str) -> str:
    if value:
        raw = Path(value).name
        stem = raw[:-4] if raw.lower().endswith(".csv") else raw
    else:
        stem = f"odoo2sheet-{model.replace('.', '-')}-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    stem = re.sub(r"[^A-Za-z0-9._-]+", "-", stem).strip(".-_") or "odoo2sheet"
    return stem + ".csv"


def _unique_path(folder: Path, filename: str) -> Path:
    candidate = folder / filename
    if not candidate.exists():
        return candidate
    stem, suffix = candidate.stem, candidate.suffix
    counter = 2
    while True:
        candidate = folder / f"{stem}-{counter}{suffix}"
        if not candidate.exists():
            return candidate
        counter += 1


def _handle_export_csv(args: dict[str, Any]) -> dict[str, Any]:
    profile, client = _get_client(args)
    model = args.get("model")
    fields = args.get("fields")
    if not isinstance(fields, list) or not fields or any(not isinstance(field, str) for field in fields):
        raise OdooError("Hãy chọn một hoặc nhiều tên trường kỹ thuật trong kết quả describe_model.")
    fields = list(dict.fromkeys(field.strip() for field in fields if field.strip()))
    metadata = client.fields_get(model)
    unknown_fields = [field for field in fields if field not in metadata]
    if unknown_fields:
        raise OdooError(f"Các trường sau không có trong `{model}`: {', '.join(unknown_fields)}. Hãy gọi describe_model trước.")

    domain = args.get("domain", [])
    if not isinstance(domain, list):
        raise OdooError("Domain phải là một mảng JSON. Dùng [] nếu không cần lọc.")
    order = args.get("order", "id asc")
    if not isinstance(order, str) or not order.strip():
        order = "id asc"
    max_records = args.get("max_records", DEFAULT_MAX_RECORDS)
    if not isinstance(max_records, int) or isinstance(max_records, bool) or not 1 <= max_records <= MAX_RECORDS:
        raise OdooError(f"max_records phải nằm trong khoảng từ 1 đến {MAX_RECORDS}.")

    output_dir = Path(str(profile["output_dir"])).expanduser()
    try:
        output_dir.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        raise OdooError(f"Không thể tạo thư mục lưu CSV đã cấu hình: {exc}") from None
    if not output_dir.is_dir():
        raise OdooError("Đường dẫn CSV đã cấu hình không phải là thư mục.")
    final_path = _unique_path(output_dir, _safe_filename(args.get("filename"), model))
    headers = [str(metadata[field].get("string") or field) for field in fields]
    temp_path: Path | None = None
    count = 0
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8-sig", newline="", prefix=".odoo2sheet-", suffix=".tmp",
            dir=output_dir, delete=False,
        ) as stream:
            temp_path = Path(stream.name)
            writer = csv.writer(stream)
            writer.writerow(headers)
            while count < max_records:
                limit = min(PAGE_SIZE, max_records - count)
                batch = client.search_read(model, domain, fields, limit, count, order)
                if not batch:
                    break
                for record in batch:
                    writer.writerow([_csv_value(record.get(field)) for field in fields])
                count += len(batch)
                if len(batch) < limit:
                    break
        os.replace(temp_path, final_path)
    except OdooError:
        raise
    except OSError as exc:
        raise OdooError(f"Không thể ghi tệp CSV: {exc}") from None
    finally:
        if temp_path and temp_path.exists():
            try:
                temp_path.unlink()
            except OSError:
                pass
    return {
        "file": str(final_path.resolve()),
        "rows_exported": count,
        "columns": headers,
        "model": model,
        "max_records_reached": count >= max_records,
        "output_format": "CSV UTF-8 with BOM",
    }


def _call_tool(name: str, args: Any) -> dict[str, Any]:
    _require_plugin_runtime()
    if not isinstance(args, dict):
        raise OdooError("Tham số công cụ phải là một đối tượng JSON.")
    if name == "preview_local_cleanup":
        return _handle_preview_local_cleanup()
    if name == "clean_local_data":
        return _handle_clean_local_data(args)
    if name == "list_connections":
        return _handle_list_connections()
    if name == "discover_databases":
        return _handle_discover_databases(args)
    if name == "check_connection":
        return _handle_check_connection(args)
    if name == "save_connection":
        return _handle_save_connection(args)
    if name == "update_connection":
        return _handle_update_connection(args)
    if name == "remove_connection":
        return _handle_remove_connection(args)
    if name == "get_report_preferences":
        return _handle_get_report_preferences(args)
    if name == "save_report_preferences":
        return _handle_save_report_preferences(args)
    if name == "find_models":
        return _handle_find_models(args)
    if name == "describe_model":
        return _handle_describe_model(args)
    if name == "export_csv":
        return _handle_export_csv(args)
    raise OdooError(f"Không tìm thấy công cụ Odoo To Sheet `{name}`.")


def _respond(request_id: Any, result: Any = None, error: dict[str, Any] | None = None) -> None:
    response: dict[str, Any] = {"jsonrpc": "2.0", "id": request_id}
    if error is not None:
        response["error"] = error
    else:
        response["result"] = result
    sys.stdout.write(json.dumps(response, ensure_ascii=False, separators=(",", ":")) + "\n")
    sys.stdout.flush()


def _handle_message(message: Any) -> None:
    if not isinstance(message, dict) or message.get("jsonrpc") != "2.0":
        _respond(None, error={"code": -32600, "message": "Yêu cầu JSON-RPC không hợp lệ"})
        return
    method = message.get("method")
    request_id = message.get("id")
    if not isinstance(method, str):
        _respond(request_id, error={"code": -32600, "message": "Thiếu phương thức JSON-RPC"})
        return
    if request_id is None:
        return
    params = message.get("params") if isinstance(message.get("params"), dict) else {}
    if method == "initialize":
        requested_version = params.get("protocolVersion", "2024-11-05")
        _respond(request_id, {
            "protocolVersion": requested_version,
            "capabilities": {"tools": {"listChanged": False}},
            "serverInfo": {"name": "odoo2sheet", "version": SERVER_VERSION},
            "instructions": "Trả lời bằng tiếng Việt trừ khi người dùng yêu cầu ngôn ngữ khác. Plugin tự chạy scripts/run_odoo_mcp_server.py trước khi mở MCP: kiểm tra và dùng lại .odoo2shet-env, không tạo lại nếu đã có; pip kiểm tra requirements.txt và chỉ cài gói còn thiếu vào đúng môi trường đó. Mỗi lời gọi tool được chặn nếu MCP server không chạy trong môi trường này. Không yêu cầu người dùng tạo env, cài thư viện bằng Terminal hoặc lặp lại thiết lập. Khi người dùng bắt đầu kết nối bằng /odoo2sheet-start, dùng HITL trong chat để thu thập URL, email và API key còn thiếu; kiểm tra trạng thái bằng list_connections, tự tìm database bằng discover_databases, tự lưu nếu chỉ có một và chỉ hỏi chọn nếu có nhiều; sau đó gọi check_connection. Nếu sai thông tin đăng nhập, hỏi người dùng nhập lại email/API key rồi cập nhật hồ sơ và kiểm tra lại. Khi kết nối thành công, báo hoàn tất và đưa lựa chọn các skill tiếp theo. Không yêu cầu xác nhận lại việc lưu cấu hình mà người dùng vừa yêu cầu; vẫn phải xin xác nhận trước khi thay thế/xóa hồ sơ, xóa tùy chọn đã lưu, xuất CSV hoặc lưu tùy chọn báo cáo. Trước khi nói chưa có hồ sơ, gọi list_connections. Không hiển thị hay nhắc lại API key. API key được lưu cục bộ; dữ liệu nghiệp vụ Odoo chỉ được đọc.",
        })
        return
    if method == "ping":
        _respond(request_id, {})
        return
    if method == "tools/list":
        _respond(request_id, {"tools": TOOLS})
        return
    if method == "tools/call":
        name = params.get("name")
        try:
            result = _call_tool(name, params.get("arguments", {}))
            _respond(request_id, _text_result(result))
        except OdooError as exc:
            _respond(request_id, _text_result({"error": str(exc)}, is_error=True))
        except Exception as exc:
            print(f"odoo2sheet internal error: {type(exc).__name__}", file=sys.stderr, flush=True)
            _respond(request_id, _text_result({"error": "Lỗi cục bộ không mong đợi. Hãy kiểm tra cấu hình plugin và log; thông tin xác thực không được ghi vào log."}, is_error=True))
        return
    _respond(request_id, error={"code": -32601, "message": f"Không tìm thấy phương thức: {method}"})


def main() -> None:
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            _handle_message(json.loads(line))
        except json.JSONDecodeError:
            _respond(None, error={"code": -32700, "message": "Parse error"})
        except BrokenPipeError:
            return


if __name__ == "__main__":
    main()

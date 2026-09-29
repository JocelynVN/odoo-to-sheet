"""Small stdio MCP server exposing read-only Odoo model metadata and CSV export."""

from __future__ import annotations

import csv
import json
import os
import re
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
CONNECTION_FORM_URI = "ui://odoo2sheet/connect/v1.html"


TOOLS = [
    {
        "name": "open_connection_form",
        "description": "Mở biểu mẫu tiếng Việt để nhập thông tin kết nối Odoo theo từng trường. Dùng khi cần thêm một dịch vụ Odoo mới.",
        "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False},
        "_meta": {"ui": {"resourceUri": CONNECTION_FORM_URI}},
        "annotations": {"readOnlyHint": True, "destructiveHint": False, "openWorldHint": False},
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
        "description": "Cập nhật database hoặc thư mục CSV của hồ sơ Odoo đã lưu mà không yêu cầu hay đọc lại API key. Dùng khi người dùng cung cấp giá trị cần cập nhật.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "profile": {"type": "string", "description": "Tên hồ sơ cục bộ cần cập nhật."},
                "database": {"type": "string", "description": "Tên database mới. Để trống nếu người dùng muốn xóa giá trị hiện có."},
                "output_dir": {"type": "string", "description": "Thư mục CSV mới. Để trống để dùng ~/odoo2sheet-output."},
                "confirm_clear_preferences": {"type": "boolean", "description": "Chỉ đặt true sau khi người dùng xác nhận xóa bộ lọc/cột đã lưu vì đổi database."},
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
        "name": "list_connections",
        "description": "Liệt kê hồ sơ kết nối Odoo cục bộ và thư mục CSV, không trả về tên đăng nhập hoặc thông tin xác thực.",
        "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False},
        "annotations": {"readOnlyHint": True, "destructiveHint": False, "openWorldHint": False},
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


def _handle_list_connections() -> dict[str, Any]:
    profiles = read_config(allow_missing=True)["profiles"]
    items = []
    for name, profile in sorted(profiles.items()):
        items.append({
            "name": name,
            "url": profile.get("url", ""),
            "database": profile.get("database") or None,
            "auth_type": profile.get("auth_type", "unknown"),
            "output_dir": profile.get("output_dir") or str(DEFAULT_OUTPUT_DIR.resolve()),
        })
    return {"connections": items}


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

    has_database = "database" in args
    has_output_dir = "output_dir" in args
    if not has_database and not has_output_dir:
        raise OdooError("Hãy cung cấp database hoặc thư mục CSV cần cập nhật.")
    if has_database and not isinstance(args["database"], str):
        raise OdooError("Tên database phải là văn bản.")
    if has_output_dir and not isinstance(args["output_dir"], str):
        raise OdooError("Thư mục CSV phải là văn bản.")

    config = read_config()
    profile = config["profiles"].get(profile_name)
    if not isinstance(profile, dict):
        raise OdooError(f"Không tìm thấy hồ sơ Odoo `{profile_name}`.")

    updated_fields: list[str] = []
    database_changed = False
    report_preferences_cleared = False
    if has_database:
        database = args["database"].strip()
        previous_database = str(profile.get("database", "")).strip()
        database_changed = previous_database != database
        preferences_exist = bool(config["report_preferences"].get(profile_name))
        report_preferences_cleared = bool(previous_database and database_changed and preferences_exist)
        if report_preferences_cleared and args.get("confirm_clear_preferences") is not True:
            raise OdooError("Đổi database sẽ xóa bộ lọc và cột báo cáo đã lưu cho hồ sơ này. Hãy hỏi người dùng xác nhận trước khi cập nhật.")
        if database_changed:
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

    if report_preferences_cleared:
        config["report_preferences"].pop(profile_name, None)
    if updated_fields:
        write_config(config)

    return {
        "updated": bool(updated_fields),
        "profile": profile_name,
        "updated_fields": updated_fields,
        "database": profile.get("database") or None,
        "output_dir": profile.get("output_dir") or str(DEFAULT_OUTPUT_DIR.resolve()),
        "config_file": str(config_path()),
        "credential": "được giữ nguyên và không hiển thị",
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
    if not isinstance(args, dict):
        raise OdooError("Tham số công cụ phải là một đối tượng JSON.")
    if name == "list_connections":
        return _handle_list_connections()
    if name == "open_connection_form":
        return {"form": "Biểu mẫu kết nối Odoo đã mở để người dùng nhập theo từng trường. Không yêu cầu họ gõ lại thông tin trong biểu mẫu. Nếu giao diện không hỗ trợ hoặc không hiển thị biểu mẫu, hãy hỏi từng trường riêng bằng tiếng Việt."}
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
            "capabilities": {"tools": {"listChanged": False}, "resources": {"listChanged": False}},
            "serverInfo": {"name": "odoo2sheet", "version": SERVER_VERSION},
            "instructions": "Trả lời bằng tiếng Việt trừ khi người dùng yêu cầu ngôn ngữ khác. Khi cần kết nối mới, gọi open_connection_form trước khi hỏi thông tin; chỉ hỏi từng trường trong hội thoại nếu giao diện không hỗ trợ hoặc không hiển thị biểu mẫu. Không gom thông tin vào một đoạn yêu cầu. Diễn giải lỗi sang tiếng Việt. Trước khi nói chưa có hồ sơ, gọi list_connections. Tạo hồ sơ trong luồng hội thoại dùng save_connection; cập nhật database/thư mục của hồ sơ đã lưu dùng update_connection, không xin lại API key. Không hiển thị thông tin xác thực. Truy cập Odoo chỉ đọc; CSV và thiết lập lưu cục bộ.",
        })
        return
    if method == "ping":
        _respond(request_id, {})
        return
    if method == "tools/list":
        _respond(request_id, {"tools": TOOLS})
        return
    if method == "resources/list":
        _respond(request_id, {
            "resources": [{
                "uri": CONNECTION_FORM_URI,
                "name": "Biểu mẫu kết nối Odoo",
                "mimeType": "text/html;profile=mcp-app",
            }],
        })
        return
    if method == "resources/read":
        uri = params.get("uri")
        if uri != CONNECTION_FORM_URI:
            _respond(request_id, error={"code": -32602, "message": "Không tìm thấy tài nguyên giao diện được yêu cầu."})
            return
        resource_path = Path(__file__).resolve().parent.parent / "ui" / "connect.html"
        try:
            html = resource_path.read_text(encoding="utf-8")
        except OSError as exc:
            _respond(request_id, error={"code": -32603, "message": f"Không thể đọc biểu mẫu kết nối: {exc}"})
            return
        _respond(request_id, {
            "contents": [{
                "uri": CONNECTION_FORM_URI,
                "mimeType": "text/html;profile=mcp-app",
                "text": html,
                "_meta": {"ui": {"prefersBorder": True}},
            }],
        })
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

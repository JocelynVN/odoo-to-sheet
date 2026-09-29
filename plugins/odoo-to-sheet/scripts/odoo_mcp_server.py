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


TOOLS = [
    {
        "name": "save_connection",
        "description": "Save an Odoo service URL, login email, and API key in the user's local Odoo To Sheet config file. Never returns or logs the API key. Prefer HTTPS; HTTP requires explicit user acknowledgement.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "profile": {"type": "string", "description": "Short profile name such as company-prod."},
                "url": {"type": "string", "description": "Odoo base URL without credentials or query parameters."},
                "database": {"type": "string", "description": "Database name; required by XML-RPC connections and optional for Odoo JSON-2."},
                "username": {"type": "string", "description": "Odoo login email."},
                "api_key": {"type": "string", "writeOnly": True, "description": "Odoo API key. Store only in the local config file; never repeat it in the result or logs."},
                "output_dir": {"type": "string", "description": "Optional local CSV output folder. Defaults to ~/odoo2sheet-output."},
                "allow_http": {"type": "boolean", "description": "Set true only after the user confirms that this non-HTTPS connection is intentional."},
                "replace_existing": {"type": "boolean", "description": "Set true only after the user confirms replacing a profile with the same name."},
            },
            "required": ["profile", "url", "username", "api_key"],
            "additionalProperties": False,
        },
        "annotations": {"readOnlyHint": False, "destructiveHint": False, "openWorldHint": True},
    },
    {
        "name": "remove_connection",
        "description": "Remove one local Odoo connection profile and its saved report preferences after explicit user confirmation. This does not delete exported CSV files.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "profile": {"type": "string", "description": "Local Odoo connection profile to remove."},
                "confirm": {"type": "boolean", "description": "Must be true only after the user confirms removal."},
            },
            "required": ["profile", "confirm"],
            "additionalProperties": False,
        },
        "annotations": {"readOnlyHint": False, "destructiveHint": True, "openWorldHint": False},
    },
    {
        "name": "list_connections",
        "description": "List local Odoo connection profiles and CSV destinations without exposing usernames or credentials.",
        "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False},
        "annotations": {"readOnlyHint": True, "destructiveHint": False, "openWorldHint": False},
    },
    {
        "name": "get_report_preferences",
        "description": "Get the last saved domain and selected columns for an Odoo model and local connection profile, without returning credentials.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "profile": {"type": "string", "description": "Configured local connection profile name."},
                "model": {"type": "string", "description": "Odoo model technical name, for example sale.report."},
            },
            "required": ["profile", "model"],
            "additionalProperties": False,
        },
        "annotations": {"readOnlyHint": True, "destructiveHint": False, "openWorldHint": False},
    },
    {
        "name": "save_report_preferences",
        "description": "Save the chosen Odoo domain and columns for reuse on this machine. Fields are checked against live model metadata first.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "profile": {"type": "string", "description": "Configured local connection profile name."},
                "model": {"type": "string", "description": "Odoo model technical name, for example sale.report."},
                "domain": {"type": "array", "items": {}, "description": "Complete Odoo ORM domain selected by the user."},
                "fields": {"type": "array", "minItems": 1, "items": {"type": "string"}, "description": "Selected technical field names from describe_model."},
                "order": {"type": "string", "description": "Comma-separated field order with optional asc/desc."},
                "max_records": {"type": "integer", "minimum": 1, "maximum": MAX_RECORDS, "description": "Maximum rows per export."},
            },
            "required": ["profile", "model", "domain", "fields"],
            "additionalProperties": False,
        },
        "annotations": {"readOnlyHint": False, "destructiveHint": False, "openWorldHint": False},
    },
    {
        "name": "find_models",
        "description": "Find Odoo models by their technical name or display name. Searches ir.model and returns a short list with model technical names for confirmation before reading business data.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "profile": {"type": "string", "description": "Configured local Odoo connection profile name."},
                "query": {"type": "string", "description": "Optional word or phrase from the model's technical or display name. Leave blank to browse available models."},
                "max_results": {"type": "integer", "minimum": 1, "maximum": 100, "description": "Maximum models to return (default 30, hard maximum 100)."},
            },
            "required": ["profile"],
            "additionalProperties": False,
        },
        "annotations": {"readOnlyHint": True, "destructiveHint": False, "openWorldHint": False},
    },
    {
        "name": "describe_model",
        "description": "Read field names, labels, types, relations, and selections for an Odoo ORM model using fields_get.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "profile": {"type": "string", "description": "Configured local connection profile name."},
                "model": {"type": "string", "description": "Odoo model technical name, such as sale.order."},
            },
            "required": ["profile", "model"],
            "additionalProperties": False,
        },
        "annotations": {"readOnlyHint": True, "destructiveHint": False, "openWorldHint": False},
    },
    {
        "name": "export_csv",
        "description": "Read records from one Odoo model with search_read and save selected fields as a UTF-8 CSV in the profile's configured local output folder. This tool never invokes Odoo write/create/unlink methods.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "profile": {"type": "string", "description": "Configured local connection profile name."},
                "model": {"type": "string", "description": "Odoo model technical name, such as sale.order."},
                "fields": {"type": "array", "items": {"type": "string"}, "description": "One or more direct technical field names returned by describe_model."},
                "domain": {"type": "array", "items": {}, "description": "Odoo domain array, including prefix operators where needed; defaults to []."},
                "order": {"type": "string", "description": "Comma-separated field names with optional asc/desc; defaults to id asc."},
                "max_records": {"type": "integer", "minimum": 1, "maximum": MAX_RECORDS, "description": f"Maximum rows to export (default {DEFAULT_MAX_RECORDS}, hard maximum {MAX_RECORDS})."},
                "filename": {"type": "string", "description": "Optional CSV filename; directory components are discarded. A timestamped filename is generated when omitted."},
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
        raise OdooError("Choose a profile name using letters, numbers, dot, underscore, or dash (up to 64 characters).")
    profile_name = profile_name.strip()
    if not isinstance(url, str):
        raise OdooError("Provide the Odoo service URL.")
    url = url.strip().rstrip("/")
    parsed = urlsplit(url)
    if parsed.scheme not in ("https", "http") or not parsed.hostname or parsed.username or parsed.password or parsed.query or parsed.fragment:
        raise OdooError("Enter a valid Odoo base URL (https:// preferred), without login details or query parameters.")
    if parsed.scheme == "http" and args.get("allow_http") is not True:
        raise OdooError("This URL uses unencrypted HTTP. Ask the user to confirm this is intentional before saving, then set allow_http=true.")
    if not isinstance(username, str) or not username.strip():
        raise OdooError("Provide the Odoo login email.")
    if not isinstance(api_key, str) or not api_key.strip():
        raise OdooError("Provide the Odoo API key. It was not saved because the value is empty.")
    if not isinstance(database, str):
        raise OdooError("The database name must be text.")

    config = read_config(allow_missing=True)
    profiles = config["profiles"]
    if profile_name in profiles and args.get("replace_existing") is not True:
        raise OdooError(f"Profile `{profile_name}` already exists. Ask the user whether to replace it or choose another name.")
    output_dir = args.get("output_dir", "")
    if not isinstance(output_dir, str):
        raise OdooError("The CSV output folder must be text.")
    profile = {
        "url": url,
        "database": database.strip(),
        "username": username.strip(),
        "auth_type": "api_key",
        "secret": api_key.strip(),
        "output_dir": str(Path(output_dir).expanduser().resolve()) if output_dir.strip() else str(DEFAULT_OUTPUT_DIR.resolve()),
    }
    previous = profiles.get(profile_name)
    if isinstance(previous, dict) and (
        str(previous.get("url", "")).rstrip("/") != profile["url"]
        or str(previous.get("database", "")).strip() != profile["database"]
    ):
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
        "credential": "stored locally; omitted from this response",
    }


def _handle_remove_connection(args: dict[str, Any]) -> dict[str, Any]:
    profile_name = args.get("profile")
    if not isinstance(profile_name, str) or not profile_name.strip():
        raise OdooError("Choose a profile name returned by list_connections.")
    if args.get("confirm") is not True:
        raise OdooError("Removal was not confirmed. Ask the user before deleting this profile.")
    config = read_config()
    profile_name = profile_name.strip()
    if profile_name not in config["profiles"]:
        raise OdooError(f"No Odoo connection profile named `{profile_name}` exists.")
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
        raise OdooError("Choose a connection profile from list_connections.")
    if not isinstance(model, str) or not re.fullmatch(r"[A-Za-z0-9_.]+", model):
        raise OdooError("Provide a valid Odoo model name.")
    config = read_config(allow_missing=True)
    if profile_name not in config["profiles"]:
        raise OdooError(f"Unknown Odoo connection profile `{profile_name}`.")
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
        raise OdooError("Provide a valid Odoo model name.")
    if not isinstance(fields, list) or not fields or any(not isinstance(field, str) or not field.strip() for field in fields):
        raise OdooError("Choose one or more fields returned by describe_model.")
    if not isinstance(domain, list):
        raise OdooError("The Odoo domain must be a JSON array.")
    metadata = client.fields_get(model)
    normalized_fields = list(dict.fromkeys(field.strip() for field in fields))
    unknown_fields = [field for field in normalized_fields if field not in metadata]
    if unknown_fields:
        raise OdooError(f"Fields not available on `{model}`: {', '.join(unknown_fields)}. Call describe_model first.")
    order = args.get("order", "id asc")
    if not isinstance(order, str) or not order.strip():
        order = "id asc"
    max_records = args.get("max_records", DEFAULT_MAX_RECORDS)
    if not isinstance(max_records, int) or isinstance(max_records, bool) or not 1 <= max_records <= MAX_RECORDS:
        raise OdooError(f"max_records must be between 1 and {MAX_RECORDS}.")

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
        raise OdooError("Choose a connection profile from list_connections.")
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
        raise OdooError("The model search query must be text.")
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
            "Could not search ir.model. This Odoo user may not have permission to list model metadata. "
            f"Ask an administrator to grant read access or provide the model technical name. Details: {exc}"
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
        raise OdooError("Choose one or more technical field names from describe_model.")
    fields = list(dict.fromkeys(field.strip() for field in fields if field.strip()))
    metadata = client.fields_get(model)
    unknown_fields = [field for field in fields if field not in metadata]
    if unknown_fields:
        raise OdooError(f"Fields not available on `{model}`: {', '.join(unknown_fields)}. Call describe_model first.")

    domain = args.get("domain", [])
    if not isinstance(domain, list):
        raise OdooError("The domain must be a JSON array. Use [] when no filters are needed.")
    order = args.get("order", "id asc")
    if not isinstance(order, str) or not order.strip():
        order = "id asc"
    max_records = args.get("max_records", DEFAULT_MAX_RECORDS)
    if not isinstance(max_records, int) or isinstance(max_records, bool) or not 1 <= max_records <= MAX_RECORDS:
        raise OdooError(f"max_records must be between 1 and {MAX_RECORDS}.")

    output_dir = Path(str(profile["output_dir"])).expanduser()
    try:
        output_dir.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        raise OdooError(f"Cannot create the configured CSV output folder: {exc}") from None
    if not output_dir.is_dir():
        raise OdooError("The configured CSV output path is not a folder.")
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
        raise OdooError(f"Could not write the CSV file: {exc}") from None
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
        raise OdooError("Tool arguments must be a JSON object.")
    if name == "list_connections":
        return _handle_list_connections()
    if name == "save_connection":
        return _handle_save_connection(args)
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
    raise OdooError(f"Unknown Odoo To Sheet tool `{name}`.")


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
        _respond(None, error={"code": -32600, "message": "Invalid JSON-RPC request"})
        return
    method = message.get("method")
    request_id = message.get("id")
    if not isinstance(method, str):
        _respond(request_id, error={"code": -32600, "message": "Missing JSON-RPC method"})
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
            "instructions": "For setup use save_connection; local credentials are written to the configured Odoo To Sheet config file and never returned. For reports use list_connections, get_report_preferences, find_models, describe_model, export_csv, and save_report_preferences. Odoo business data access is read-only; CSV output is saved on the local machine.",
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
            _respond(request_id, _text_result({"error": "Unexpected local error. Check the plugin setup and logs; credentials are not logged."}, is_error=True))
        return
    _respond(request_id, error={"code": -32601, "message": f"Method not found: {method}"})


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

"""Read-only Odoo client supporting legacy XML-RPC and Odoo 19+ JSON-2."""

from __future__ import annotations

import json
import os
import re
import tempfile
import urllib.error
import urllib.parse
import urllib.request
import xmlrpc.client
from pathlib import Path
from typing import Any


DEFAULT_CONFIG = Path.home() / ".config" / "odoo2sheet" / "config.json"
DEFAULT_OUTPUT_DIR = Path.home() / "odoo2sheet-output"
CONFIG_PATH = Path(
    os.environ.get("ODOO2SHEET_CONFIG")
    or os.environ.get("ODOO_REPORTS_CONFIG")
    or str(DEFAULT_CONFIG)
).expanduser()
HTTP_TIMEOUT_SECONDS = 35
MODEL_RE = re.compile(r"^[A-Za-z0-9_.]+$")
FIELD_RE = re.compile(r"^[A-Za-z0-9_]+$")
ORDER_RE = re.compile(
    r"^[A-Za-z0-9_]+(?:\s+(?:asc|desc))?(?:\s*,\s*[A-Za-z0-9_]+(?:\s+(?:asc|desc))?)*$",
    re.IGNORECASE,
)


class OdooError(Exception):
    """An actionable, credential-safe connection or query error."""


class _TimeoutTransport(xmlrpc.client.Transport):
    def __init__(self, timeout: int):
        super().__init__(use_builtin_types=True)
        self.timeout = timeout

    def make_connection(self, host: str):
        connection = super().make_connection(host)
        connection.timeout = self.timeout
        return connection


class _TimeoutSafeTransport(xmlrpc.client.SafeTransport):
    def __init__(self, timeout: int):
        super().__init__(use_builtin_types=True)
        self.timeout = timeout

    def make_connection(self, host: str):
        connection = super().make_connection(host)
        connection.timeout = self.timeout
        return connection


def _xmlrpc_proxy(url: str) -> xmlrpc.client.ServerProxy:
    parsed = urllib.parse.urlsplit(url)
    transport: xmlrpc.client.Transport
    if parsed.scheme == "https":
        transport = _TimeoutSafeTransport(HTTP_TIMEOUT_SECONDS)
    else:
        transport = _TimeoutTransport(HTTP_TIMEOUT_SECONDS)
    return xmlrpc.client.ServerProxy(url, transport=transport, allow_none=True, use_builtin_types=True)


def _secure_permissions(path: Path) -> None:
    if os.name == "nt":
        return
    try:
        path.parent.chmod(0o700)
        if path.exists():
            path.chmod(0o600)
    except OSError:
        pass


def read_config(*, allow_missing: bool = False) -> dict[str, Any]:
    if not CONFIG_PATH.exists():
        if allow_missing:
            return {"profiles": {}, "report_preferences": {}}
        raise OdooError(
            "No Odoo connection is configured yet. Start `/odoo2sheet-connect` to add one."
        )
    _secure_permissions(CONFIG_PATH)
    try:
        config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise OdooError(f"Cannot read Odoo To Sheet config at {CONFIG_PATH}: {exc}") from None
    if not isinstance(config, dict):
        raise OdooError(f"The Odoo To Sheet config at {CONFIG_PATH} must be a JSON object.")
    config.setdefault("profiles", {})
    config.setdefault("report_preferences", {})
    if not isinstance(config["profiles"], dict) or not isinstance(config["report_preferences"], dict):
        raise OdooError(f"The Odoo To Sheet config at {CONFIG_PATH} has invalid configuration sections.")
    return config


def write_config(config: dict[str, Any]) -> None:
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    if os.name != "nt":
        CONFIG_PATH.parent.chmod(0o700)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix="config-", suffix=".json", dir=CONFIG_PATH.parent
    )
    try:
        if os.name != "nt":
            os.fchmod(descriptor, 0o600)
        with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
            json.dump(config, stream, indent=2, ensure_ascii=False)
            stream.write("\n")
        os.replace(temporary_name, CONFIG_PATH)
        _secure_permissions(CONFIG_PATH)
    finally:
        if os.path.exists(temporary_name):
            os.unlink(temporary_name)


def load_profiles() -> dict[str, dict[str, Any]]:
    return read_config()["profiles"]


def get_profile(name: str) -> dict[str, Any]:
    profiles = load_profiles()
    profile = profiles.get(name)
    if not isinstance(profile, dict):
        available = ", ".join(sorted(profiles)) or "none"
        raise OdooError(f"Unknown Odoo connection profile `{name}`. Configured profiles: {available}.")
    required = ("url", "username", "auth_type", "secret", "output_dir")
    missing = [key for key in required if not profile.get(key)]
    if missing:
        raise OdooError(f"Profile `{name}` is missing required settings: {', '.join(missing)}.")
    if profile["auth_type"] not in ("api_key", "password"):
        raise OdooError(f"Profile `{name}` must use `api_key` or `password` authentication.")
    parsed = urllib.parse.urlsplit(str(profile["url"]))
    if parsed.scheme not in ("http", "https") or not parsed.hostname:
        raise OdooError(f"Profile `{name}` needs an Odoo URL beginning with http:// or https://.")
    if parsed.username or parsed.password or parsed.query or parsed.fragment:
        raise OdooError("Keep credentials and query parameters out of the Odoo URL; configure them in the profile fields.")
    profile["url"] = str(profile["url"]).rstrip("/")
    return profile


def config_path() -> Path:
    return CONFIG_PATH


class OdooClient:
    """Only exposes Odoo fields_get and search_read, never arbitrary methods."""

    def __init__(self, profile_name: str, profile: dict[str, Any]):
        self.profile_name = profile_name
        self.profile = profile
        self.base_url = profile["url"].rstrip("/")
        self._major_version: int | None = None
        self._xml_uid: int | None = None

    def _request_json(self, path: str, *, method: str = "GET", body: dict[str, Any] | None = None,
                      bearer: bool = False) -> Any:
        headers = {"Accept": "application/json", "User-Agent": "odoo2sheet-plugin/0.2"}
        payload = None
        if body is not None:
            headers["Content-Type"] = "application/json; charset=utf-8"
            payload = json.dumps(body, ensure_ascii=False).encode("utf-8")
        if bearer:
            headers["Authorization"] = f"bearer {self.profile['secret']}"
            database = str(self.profile.get("database", "")).strip()
            if database:
                headers["X-Odoo-Database"] = database
        request = urllib.request.Request(
            self.base_url + path, data=payload, headers=headers, method=method
        )
        try:
            with urllib.request.urlopen(request, timeout=HTTP_TIMEOUT_SECONDS) as response:
                raw = response.read().decode("utf-8")
        except urllib.error.HTTPError as exc:
            raw = exc.read().decode("utf-8", errors="replace")
            message = self._http_error_message(raw, exc.code)
            raise OdooError(self._redact(message)) from None
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            reason = getattr(exc, "reason", exc)
            raise OdooError(f"Cannot reach the configured Odoo service: {self._redact(str(reason))}") from None
        try:
            return json.loads(raw) if raw else None
        except json.JSONDecodeError:
            raise OdooError("Odoo returned a non-JSON response. Check the service URL and reverse-proxy configuration.") from None

    @staticmethod
    def _http_error_message(raw: str, status: int) -> str:
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError:
            payload = None
        if isinstance(payload, dict) and payload.get("message"):
            return f"Odoo returned HTTP {status}: {payload['message']}"
        labels = {401: "Authentication failed", 403: "Odoo denied access", 404: "Odoo API endpoint or model method was not found"}
        return f"{labels.get(status, 'Odoo request failed')} (HTTP {status})."

    def _redact(self, message: str) -> str:
        secret = str(self.profile.get("secret", ""))
        return message.replace(secret, "[redacted]") if secret else message

    def _detect_major_version(self) -> int | None:
        if self._major_version is not None:
            return self._major_version
        try:
            info = self._request_json("/web/version")
            version_info = info.get("version_info") if isinstance(info, dict) else None
            version = info.get("version") if isinstance(info, dict) else None
            if version_info and isinstance(version_info[0], int):
                self._major_version = version_info[0]
            elif version:
                match = re.match(r"\s*(\d+)", str(version))
                if match:
                    self._major_version = int(match.group(1))
        except OdooError:
            pass
        if self._major_version is None:
            try:
                common = _xmlrpc_proxy(self.base_url + "/xmlrpc/2/common")
                info = common.version()
                version_info = info.get("server_version_info") if isinstance(info, dict) else None
                version = info.get("server_version") if isinstance(info, dict) else None
                if version_info and isinstance(version_info[0], int):
                    self._major_version = version_info[0]
                elif version:
                    match = re.match(r"\s*(\d+)", str(version))
                    if match:
                        self._major_version = int(match.group(1))
            except Exception:
                pass
        return self._major_version

    def _uses_json2(self) -> bool:
        return self.profile["auth_type"] == "api_key" and (self._detect_major_version() or 0) >= 19

    def _xmlrpc_execute(self, model: str, method: str, args: list[Any], kwargs: dict[str, Any]) -> Any:
        database = str(self.profile.get("database", "")).strip()
        if not database:
            raise OdooError("This Odoo XML-RPC connection needs a database name. Add it to the local connection profile.")
        try:
            common = _xmlrpc_proxy(self.base_url + "/xmlrpc/2/common")
            uid = common.authenticate(database, self.profile["username"], self.profile["secret"], {})
            if not uid:
                raise OdooError("Odoo authentication failed. Check the database, username, and API key/password.")
            objects = _xmlrpc_proxy(self.base_url + "/xmlrpc/2/object")
            return objects.execute_kw(
                database, uid, self.profile["secret"], model, method, args, kwargs
            )
        except OdooError:
            raise
        except xmlrpc.client.Fault as exc:
            message = str(exc.faultString).split("\n", 1)[0]
            raise OdooError(self._redact(f"Odoo rejected the request: {message}")) from None
        except (xmlrpc.client.ProtocolError, OSError, TimeoutError) as exc:
            raise OdooError(f"Odoo XML-RPC request failed: {self._redact(str(exc))}") from None

    def _json2_execute(self, model: str, method: str, params: dict[str, Any]) -> Any:
        encoded_model = urllib.parse.quote(model, safe=".")
        encoded_method = urllib.parse.quote(method, safe="")
        result = self._request_json(
            f"/json/2/{encoded_model}/{encoded_method}", method="POST", body=params, bearer=True
        )
        return result

    def fields_get(self, model: str) -> dict[str, dict[str, Any]]:
        self._validate_model(model)
        attributes = ["string", "type", "relation", "selection", "store"]
        if self._uses_json2():
            result = self._json2_execute(model, "fields_get", {"attributes": attributes})
        else:
            result = self._xmlrpc_execute(model, "fields_get", [], {"attributes": attributes})
        if not isinstance(result, dict):
            raise OdooError(f"Odoo did not return field metadata for model `{model}`.")
        return result

    def search_read(self, model: str, domain: list[Any], fields: list[str], limit: int,
                    offset: int, order: str) -> list[dict[str, Any]]:
        self._validate_model(model)
        if not isinstance(domain, list):
            raise OdooError("The Odoo domain must be a JSON array.")
        if not fields or any(not isinstance(field, str) or not FIELD_RE.fullmatch(field) for field in fields):
            raise OdooError("Choose one or more direct Odoo field names (for example `name` or `amount_total`).")
        if not ORDER_RE.fullmatch(order):
            raise OdooError("The order value must be a comma-separated list of field names with optional asc/desc.")
        kwargs = {"fields": fields, "limit": limit, "offset": offset, "order": order}
        if self._uses_json2():
            result = self._json2_execute(
                model, "search_read", {"domain": domain, **kwargs}
            )
        else:
            result = self._xmlrpc_execute(model, "search_read", [domain], kwargs)
        if not isinstance(result, list):
            raise OdooError(f"Odoo did not return records for model `{model}`.")
        return result

    @staticmethod
    def _validate_model(model: str) -> None:
        if not isinstance(model, str) or not MODEL_RE.fullmatch(model):
            raise OdooError("Use an Odoo ORM model name such as `sale.order`.")

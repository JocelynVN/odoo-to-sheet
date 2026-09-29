---
name: odoo2sheet-connect
description: Add, replace, or select a saved Odoo service connection for Odoo To Sheet. Use when the user invokes /odoo2sheet-connect or asks to connect/configure an Odoo service.
---

# Connect Odoo To Sheet

Connection profiles and report preferences are stored on this computer at `~/.config/odoo2sheet/config.json` (the path is based on the user's home folder on each operating system). The plugin restricts the folder/file permissions on macOS/Linux. The file is not encrypted, so tell the user before they provide an API key. Never echo, summarize, or include the key in a filename, log, or tool result.

## Connect flow

1. Call `list_connections`. If the user says to use an existing service, offer the saved profile names and CSV destinations, then use that profile without asking for its key again. If adding a connection, ask for:
   - a short profile name, such as `company-prod`;
   - Odoo service URL;
   - database name, if known (required by XML-RPC, normally used by Odoo 18 and earlier; often optional for Odoo 19 JSON-2);
   - login email;
   - Odoo API key;
   - optional CSV folder (default `~/odoo2sheet-output`). This folder is created automatically at the first export.
2. If the requested profile name already exists, ask whether to replace it or choose a different name. Do not overwrite silently.
3. Prefer an HTTPS URL. If the URL uses HTTP, explain the credential is sent over an unencrypted connection and ask the user to confirm before calling `save_connection` with `allow_http=true`.
4. Call `save_connection` with the details. The tool writes the profile locally, uses an atomic file replacement, limits macOS/Linux permissions, and omits the API key from its response. Do not call shell commands to print or inspect the secret file.
5. After save succeeds, call `describe_model` for `sale.report` to check whether the connection can reach the requested report model. If this fails, leave the saved profile in place and explain whether the error indicates authentication, database, service URL, missing sales module, or Odoo access rights. Do not ask the user to send the key again unless they choose to replace the profile.
6. Confirm only the profile name, Odoo URL, database (if present), CSV folder, and local config path. Never display the API key.

The default CSV folder for new profiles is `~/odoo2sheet-output`. Existing profiles keep their currently configured CSV folder. Previously exported files are never moved or deleted when a profile's output folder changes.

If no profile is requested and there are existing profiles, ask whether the user wants to reuse one or add a new Odoo service. A profile is local to this computer; it is not shared through the plugin marketplace.

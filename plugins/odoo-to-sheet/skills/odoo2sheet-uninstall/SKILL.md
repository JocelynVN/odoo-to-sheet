---
name: odoo2sheet-uninstall
description: Remove saved Odoo connection profiles and guide the user through removing Odoo To Sheet from GPT Desktop.
---

# Remove Odoo To Sheet data or plugin

The user invoked `/odoo2sheet-uninstall`. Explain that saved Odoo profiles and the plugin are separate: removing profiles deletes the saved email/API key and report preferences from this computer, while existing CSV exports stay in place.

1. Call `list_connections` and show the user the local configuration path, normally `~/.config/odoo2sheet/config.json`.
2. Ask one clear choice:
   - **Keep saved connections** in case they use Odoo To Sheet again.
   - **Delete saved connections and report preferences** from this computer.
3. If the user explicitly chooses deletion, call `remove_connection` for each listed profile with `confirm=true`. Do not delete exported CSV files.
4. Guide the user to remove the plugin in GPT Desktop:
   - If they manage the workspace: open **Workspace settings → Plugins**, find **Odoo To Sheet**, then disable or remove it.
   - If they do not manage the workspace: ask the workspace manager to disable or remove it.
5. Clearly report which profiles were kept or removed, remind the user that exported CSV files remain in their output folder, and say whether a workspace manager still needs to remove the plugin.

Do not tell users to open a terminal or run command-line plugin tools. Do not claim the plugin was removed from the workspace; only a workspace administrator can do that in the desktop app.

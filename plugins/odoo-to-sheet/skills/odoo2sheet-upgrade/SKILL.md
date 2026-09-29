---
name: odoo2sheet-upgrade
description: Help refresh Odoo To Sheet in GPT Desktop from its GitHub marketplace. Use when the user invokes /odoo2sheet-upgrade or asks to update the plugin.
---

# Upgrade Odoo To Sheet

This plugin is normally imported into a ChatGPT workspace from the GitHub marketplace. Workspace administrators control marketplace sync; ordinary users cannot update the shared plugin themselves.

1. Tell the user that GitHub marketplaces sync automatically once a day.
2. If the user says they are a workspace administrator, guide them to **Workspace settings → Plugins → Marketplaces → Odoo To Sheet → Sync now**. Do not claim the sync succeeded; they must confirm it in the app.
3. If the user is not an administrator or is unsure, explain that they can ask their workspace administrator to sync the **Odoo To Sheet** marketplace. Provide this short message they can copy: “Please sync the Odoo To Sheet marketplace from GitHub so I can use the latest version.”
4. If the user installed a personal/local copy rather than a workspace copy, explain that the person who installed it must update that source and refresh the plugin in GPT Desktop.

Do not run terminal commands or claim that the plugin was updated. Odoo connection profiles and exported CSV files stay on the user's computer during a plugin update.

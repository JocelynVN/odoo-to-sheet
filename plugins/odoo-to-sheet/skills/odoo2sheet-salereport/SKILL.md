---
name: odoo2sheet-salereport
description: Export configurable rows from Odoo's sale.report model to CSV. Ask whether to reuse the last saved domain and columns or set new ones; suggest only filters and fields confirmed from live model metadata.
---

# Odoo sale.report to CSV

Use `/odoo2sheet-salereport <request>` for an Odoo sales analysis export. The target model is always `sale.report`. The user's profile, domain, and selected columns may differ by Odoo service/version and are stored locally when the user asks to save them.

## Step 1: choose the Odoo service

1. Call `list_connections`. If none are configured, point the user to `/odoo2sheet-connect` and stop before querying Odoo.
2. If there is one profile, use it. If there are several, ask the user to choose by profile name/service URL. Never ask them to paste credentials into this report request.
3. Call `describe_model` for `sale.report`. Use its current labels, technical names, types, relations, and selection values for every later suggestion. If Odoo has no accessible `sale.report`, report that fact and stop; do not substitute `sale.order` or another model.
4. Call `get_report_preferences` for the selected profile and `sale.report`.

## Step 2: choose the filters/domain

If a saved configuration exists, show a plain-language summary of its domain and ask the user to choose:

- **A. Reuse saved filters**
- **B. Set new filters**
- **C. Enter my own criteria/domain** (also available as a free-form response)

If no saved configuration exists, proceed with new filters. Use the user's request plus the live `describe_model` fields to offer only options that exist on this `sale.report`. Typical suggestions, when those fields are present, are:

- a date range using a suitable date/datetime field;
- order state, using the exact selection values returned by Odoo;
- customer, salesperson, sales team, company, product, or product category using the available relation fields;
- the user's own natural-language criteria or raw Odoo domain.

The user can choose several suggestions. Convert all chosen criteria into one Odoo domain. Never infer a date basis or add a state/company rule without the user's request. For an inclusive date interval use `>=` the start and `<` the day after the end. If a criterion could map to several fields, ask the user which one.

Summarize the chosen filters in normal language. For an existing saved domain, translate field names to labels from `describe_model` where possible. Do not make the user read raw domain JSON unless they chose to enter it themselves.

## Step 3: choose CSV columns/fields

After the filter choice, ask separately whether to reuse the saved columns or configure new ones:

- **A. Reuse saved columns**
- **B. Choose new columns**
- **C. Enter the column names/technical fields I want** (also available as a free-form response)

If no saved columns exist, offer only B and C. For B, present a short menu of common report columns **only if they appear in live metadata**, for example date, order reference, customer, product, salesperson, sales team, quantity, untaxed amount, total, discount, or margin. Show the Odoo label and technical field for each choice. Do not guess field names across Odoo versions.

Map the selected column labels to technical fields using `describe_model`; resolve ambiguity before export. Export only the chosen fields. If a saved field no longer exists, tell the user and ask them to configure columns again.

## Step 4: export and save preferences

Call `export_csv` with model `sale.report`, the selected direct fields, the complete user-approved domain, and any requested order/row limit. Use the default maximum of 10,000 rows unless the user requests another limit (hard maximum 50,000).

After a successful export, report the file path, row count, model, filters, and column labels. CSV files go to the output folder configured for the selected profile; new profiles default to `~/odoo2sheet-output`, which is created automatically when needed. The default filename is `odoo2sheet-sale-report-YYYYMMDD-HHMMSS.csv`; if that name already exists, the exporter adds a numeric suffix rather than overwriting a file. Then ask whether to save these filters and columns as the profile's reusable `sale.report` configuration:

- **Save for next time**: call `save_report_preferences`, replacing the last saved preference for this profile/model.
- **Use once**: do not change saved preferences.

Never paste sales rows into chat unless the user asks to inspect them. Odoo access remains read-only; only local CSV and local preference files are written.

---
type: odoo_invoice
status: done
customer_name: shoaib
invoice_date: '2026-03-10'
lines:
- product: AI Employee
  quantity: 1
  price_unit: 1000.0
approved_at: '2026-03-10T12:00:00Z'
customer_id: 9
odoo_invoice_id: 6
odoo_invoice_ref: INV/2026/00005
completed_at: '2026-03-10T09:25:24Z'
---
# Invoice Review

**Customer**: shoaib
**Date**: 2026-03-10

## Line Items

- AI Employee x 1 @ $1000.00

**Estimated Total**: $1000.00

---
## How to use:
## 1. Copy this file to vault/Approved/
## 2. Rename it to ODOO_INVOICE_<date>_<name>.md
## 3. Replace all CHANGE_ME with your values
## 4. Run: uv run python -m backend.orchestrator
## 5. Customer is auto-created in Odoo if not exists
## 6. File moves to vault/Done/ when processed

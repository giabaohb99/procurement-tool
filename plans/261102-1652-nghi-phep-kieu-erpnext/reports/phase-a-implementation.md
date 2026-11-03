# Phase A duoc-CR-715 — report
Migration lvacc715 (down jobrun01, hand-written idempotent, applied local). Backend: accrual_service.py (new), balance_service, request_service, catalog_model/constants/schema/controller, balance_controller+request_controller (available_days), main.py (quota router). FE: leave.ts, leave-api, use-leave, query-keys, leave-quota-rules(+test), leave-type-quota-card, leave-type-crud. Help: seed_help_nghi_phep.py (reseeded).
Gates: pytest -k filter 593 passed; tsc 0; eslint hr 0 errors; vitest hr 1426 passed.

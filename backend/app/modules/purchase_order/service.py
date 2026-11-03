"""Đơn mua hàng (ĐMH) — CỬA NHẬP LẠI tên cũ (bao-CR-715, đợt R3).

Đơn mua hàng: lưu header + dòng hàng + các lần giao; mỗi lần lưu reconcile side-effect (phiếu nhập kho ngầm,
tồn kho, công nợ 2 luồng). Idempotent theo id của dòng giao.

Mã nghiệp vụ đã chẻ theo bước, mỗi bước một tệp:
- `base_service`            hằng dùng chung (ENTITY, trạng thái giao / tiến độ), tỷ giá, `get_po`, `items_of`,
                            `deliveries_of`, đồng bộ về YCMH
- `item_service`            lưu dòng hàng (điền sẵn thông số, tên trên hóa đơn, tiền tệ, ngày dự kiến), ô bắt buộc
- `delivery_service`        lưu các lần giao, gỡ side-effect, tính lại phiếu nhập kho / tồn kho / công nợ
- `import_cost_service`     chi phí thu mua: tra cứu, ba giai đoạn, chốt, công nợ chi phí
- `cost_allocation_service` phân bổ chi phí vào dòng hàng, lưu bảng chi phí
- `progress_service`        tiến độ dòng: thứ tự bước, tự nhảy bước, đặt tiến độ tay
- `edit_service`            tạo / sửa / sao chép / xóa đơn, khóa sửa sau duyệt, đổi trạng thái, mở lại
- `query_service`           truy vấn đọc cho controller / serializer, điều khoản in

Mọi nơi vẫn gọi `service.<tên>` như cũ. ⚠️ Muốn monkeypatch một hàm trong bài kiểm thì patch ở TỆP CON định nghĩa
nó (vd `progress_service.highest_satisfied_step`) — patch ở cửa này không ăn vào lời gọi bên trong tệp con.
Thêm hàm mới thì đặt vào tệp con đúng bước rồi thêm tên vào dòng import tương ứng ở đây.
"""
# Cửa nhập lại: các tên dưới đây để nơi khác gọi `service.<tên>`, không phải import thừa.
# ruff: noqa: F401
from .base_service import (normalize_rate, rate_of, _pdate, _days, FILTERABLE, ENTITY, DELIV_PENDING, DELIV_SHORT,
                           DELIV_DEFECT, DELIV_RECEIVED, LINE_NOT_DELIVERED, LINE_PARTIAL, LINE_FULL, PROG_NOT_ORDERED,
                           PROG_ORDERED, PROG_RECEIVED, PROG_DOC_PENDING, PROG_DOC_SENT, PROG_COMPLETED, PROG_PAUSED,
                           PROG_CANCELLED, get_po, items_of, deliveries_of, _supplier_map, sync_urgent_group, _sync_pr)
from .item_service import (_product_specs_map, product_invoice_names_map, fill_blank_invoice_name, pr_expected_map,
                           _save_items, REQUIRED_LINE_FIELDS, _NUMERIC_FIELDS, missing_line_fields)
from .delivery_service import (_save_deliveries, _cleanup_delivery, recompute_effects)
from .import_cost_service import (import_costs_of, cost_type_map, cost_type_name, cost_type_creates_payable, stage_of,
                                  cost_amount_of, cost_rate_of, cost_base_of, compute_cost_bases, effective_stage_of,
                                  filled_stage_of, effective_base_of, is_final_cost, final_costs, IMPORT_COST_SOURCE,
                                  IMPORT_COST_PAYABLE_STATUSES, import_cost_payables_of, sync_import_cost_payables,
                                  block_complete_unpaid_import_costs, block_delete_paid_import_cost, paid_cost_ids,
                                  COST_STAGE_MIN_REASON, COST_STAGE_ADVANCE_ACTIONS, _fill_stage_from_previous,
                                  _cost_label, _stage_label, _require_reason, advance_cost_stage, reopen_cost_stage,
                                  _get_cost_row, finalize_cost_line, COST_FINAL_NAMES_IN_LOG, has_estimate,
                                  count_costs_missing_estimate, finalize_cost_lines, reopen_cost_line,
                                  block_complete_not_final_costs)
from .cost_allocation_service import (EQUAL_SHARE_LABEL, MANUAL_ALLOCATION_TOLERANCE, parse_manual_allocation,
                                      _line_goods_base, _basis_goods_base, _allocation_basis, allocation_base_of,
                                      allocate_import_costs, _COST_TEXT_FIELDS, _COST_NUMBER_FIELDS,
                                      is_cost_row_changed, _save_import_costs)
from .progress_service import (PROGRESS_ORDER, PROGRESS_EXCEPTIONS, is_line_paid, _STEP_MISSING, _step_ok,
                               validate_progress, highest_satisfied_step, auto_advance_line, apply_auto_progress,
                               set_item_progress)
from .edit_service import (_ITEM_COPY_FIELDS, copy_po, _default_nspt, _ensure_pr_dispatched, _handler_dept_of_pr,
                           create_po, APPROVED_STATUSES, LINE_FIELDS_EDITABLE_AFTER_APPROVAL, LINE_FIELD_LABELS,
                           ORDER_FIELD_LABELS, ORDER_FIELDS_EDITABLE_AFTER_APPROVAL, _EDIT_HINT, _differs,
                           block_edit_approved_order, block_clear_misa_in_use, unapprove_po, update_po,
                           DOCUMENT_STATUSES, set_document_status, delete_po, reopen_po, set_status)
from .query_service import (DEFAULT_INSPECTION_DAYS, DEFAULT_RETURN_DAYS, DEFAULT_INVOICE_DEADLINE, resolve_print_terms,
                            order_amount_map, list_po, list_display_names, pr_items_for_po, query_by_id, query_by_ids,
                            build_list_query, build_line_query, received_by_warehouse, pr_ids_by_code,
                            delivery_payables_of, invoice_names_by_code, latest_approved_actor, company_by_id,
                            supplier_by_code, warehouse_by_code, warehouses_by_codes, live_pr_by_code,
                            has_completed_item, items_unsorted_of)

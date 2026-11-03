"""Nghiệp vụ Yêu cầu mua hàng (YCMH) — CỬA NHẬP LẠI tên cũ (bao-CR-715, đợt R3).

Mã nghiệp vụ đã chẻ theo bước của vòng đời phiếu, mỗi bước một tệp:
- `base_service`       hằng dùng chung (ENTITY, trạng thái dòng), `get_pr`, `items_of`, mốc SLA
- `department_service` phòng ban, phòng xử lý, trưởng phòng phê duyệt (người duyệt chọn được)
- `edit_service`       tạo / sửa / sao chép / xóa phiếu, lưu dòng, cụm NCC, cờ gấp, chốt trước khi gửi duyệt
- `dispatch_service`   điều phối (duyệt lần 2) và phân công người thu mua
- `lifecycle_service`  hủy, trả về người yêu cầu, chuyển phòng xử lý, hoàn tất, đổi trạng thái
- `line_status_service` trạng thái dòng + trạng thái phiếu tính lại từ ĐMH, tiến độ đặt hàng
- `query_service`      truy vấn đọc cho controller / serializer (danh sách, tra tên, chuông)

Mọi nơi vẫn gọi `service.<tên>` như cũ. ⚠️ Bài kiểm monkeypatch `service.dispatch_enabled` — nên các tệp con gọi hàm
này QUA cửa (`from . import service` trong thân hàm), đừng import thẳng tên, kẻo patch không ăn.
Thêm hàm mới thì đặt vào tệp con đúng bước rồi thêm tên vào dòng import tương ứng ở đây.
"""
# Cửa nhập lại: các tên dưới đây để nơi khác gọi `service.<tên>`, không phải import thừa.
# ruff: noqa: F401
from .base_service import (FILTERABLE, ENTITY, sla_base_date, LINE_STATUS_NO_PO, LINE_STATUS_NOT_ORDERED,
                           LINE_STATUS_ORDERED, LINE_STATUS_RECEIVED, LINE_STATUS_COMPLETED, LINE_STATUS_CANCELLED,
                           LINE_STATUS_IDLE, LINE_STATUS_DONE, LINE_STATUS, items_of, get_pr)
from .department_service import (find_dept_head, find_dept_head_id, fill_department_from_employee,
                                 list_self_purchasing_dept_ids, default_handler_dept_id, backfill_handling_dept,
                                 handler_dept_name_of, resolve_employee_department, _find_dept, _approver_users,
                                 _can_user_approve_row, dept_head_candidates, complete_head_choices,
                                 dept_head_candidates_by_department, _scope_allows_department, sync_head_of_dept_name)
from .edit_service import (_AUTO_NOTE_PREFIX, _empty_cluster, _norm_cluster, clusters_of, apply_supplier_info,
                           build_clusters, ensure_submit_ready, urgent_reasons, apply_auto_urgent, _save_items, copy_pr,
                           create_pr, update_pr, set_urgent, delete_pr)
from .lifecycle_service import (cancel_pr, can_return_requester, return_pr, TRANSFERABLE_STATUSES, dept_name_of,
                                can_transfer_dept, validate_transfer_target, transfer_handler_dept, complete_pr,
                                _notify_survey_request_done, set_status)
from .dispatch_service import (dispatch_enabled, DISPATCH_CONTEXT_FIELDS, dispatch_context, dispatch_skip_rules,
                               skip_dispatch_for, dispatch_pr, assign)
from .line_status_service import (has_cancelled_line, _misa_covered_codes, PO_PENDING_STATUSES, PO_DEAD_STATUSES,
                                  PO_STATUS_LABELS, order_progress, recompute_status, _PROGRESS_ORDER,
                                  _PROG_NOT_ORDERED, _PROG_ORDERED, _PROG_COMPLETED, _PROG_PAUSED, _PROG_CANCELLED,
                                  sync_from_purchase_orders, _notify_expected_changed, _set_item_product_code,
                                  update_item_status)
from .query_service import (list_pr, query_by_id, query_live_by_id, query_live_by_ids, build_list_query,
                            list_line_summaries, assigned_user_ids, user_ids_of_employee_codes, notify_users,
                            purchasing_head, audit_actors_of, has_quote_file, linked_survey_requests, company_of,
                            product_thumbnails, employee_names_by_code)

"""Nghiệp vụ Yêu cầu báo giá (YCBG, mã cũ YCKS) — CỬA NHẬP LẠI tên cũ (bao-CR-715, đợt R3).

Mã nghiệp vụ đã chẻ theo bước của vòng đời phiếu, mỗi bước một tệp:
- `base_service`      hằng dùng chung (ENTITY, FILTERABLE...), `get_sr`, `lines_of`, `options_of`, `get_line`
- `edit_service`      tạo / sửa / nhân bản / xóa phiếu, lưu dòng
- `line_service`      quyền xử lý dòng, dòng người gọi được thấy, trạng thái dòng, phân công dòng, kho khảo sát
- `option_service`    phương án khảo sát của dòng (thêm, đồng bộ từ phiếu khảo sát, xóa, chọn)
- `lifecycle_service` đổi trạng thái, trả về người yêu cầu, chuyển phòng xử lý, chốt báo cáo, hoàn thành phiếu
- `pr_link_service`   sinh YCMH từ phương án đã chọn, tự hoàn tất khi YCMH xong, gỡ liên kết YCMH đã xóa
- `query_service`     truy vấn đọc cho controller / serializer (danh sách, lọc, tra người dùng, chuông)

Mọi nơi vẫn gọi `service.<tên>` như cũ. Thêm hàm mới thì đặt vào tệp con đúng bước rồi thêm tên vào dòng import
tương ứng ở đây.
"""
# Cửa nhập lại: các tên dưới đây để nơi khác gọi `service.<tên>`, không phải import thừa.
# ruff: noqa: F401
from .base_service import (ENTITY, FILTERABLE, MAX_OPTIONS_PER_LINE, HEADER_FIELDS, VN_OFFSET, _stamp_result_date,
                           get_sr, lines_of, options_of, valid_options_of, get_line)
from .edit_service import (_gen_code, _copy_pr_line_images, _save_lines, create_sr, update_sr, clone_sr, delete_sr)
from .line_service import (set_line_status, resolve_supplier_name, survey_header, is_purchaser, _has_scope_all,
                           can_process_line, _see_all_lines, visible_lines_for, normalize_filter_values,
                           available_survey_lines, auto_assign, set_line_assignee)
from .option_service import (_line_label, create_option, sync_options_from_surveys, delete_option, update_option_note,
                             set_option_fields, choose_option)
from .lifecycle_service import (set_status, TRANSFERABLE_STATUSES, can_transfer_dept, can_return_requester,
                                return_to_requester, transfer_handler_dept, _require_report_ready, finalize_sr,
                                complete_sr)
from .pr_link_service import (_gen_pr_code, create_prs, auto_complete_from_pr, _auto_complete_sr, unlink_deleted_pr,
                              list_deleted_linked_prs, unlink_deleted_prs)
from .query_service import (query_by_id, query_live_by_id, query_by_ids, build_list_query, employee_names_by_code,
                            same_dept_as_requester, notify, users_of_codes, users_with_id, user_with_id,
                            active_users_of_employee, survey_line_files, survey_product_line, pr_links_of)

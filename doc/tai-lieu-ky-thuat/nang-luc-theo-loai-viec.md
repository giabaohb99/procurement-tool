# Năng lực theo loại việc — định nghĩa «xong», «làm lại», «tải đang ôm» (duoc-CR-656)

Nguồn số liệu để AI chia việc và để quản trị trả lời: «chị A làm một YCMH trung bình mấy ngày, chậm nhất mấy ngày»,
«loại việc X phải làm lại bao nhiêu lần». **Máy tính số, AI viết chữ**: tài liệu này là hợp đồng của các con số.
Kế hoạch: `plans/261020-1600-d0-d1-ghi-nhan-thao-tac-nang-luc/` (phase 05–07). Đại ca đã chốt các mặc định ở `open-questions.md`.

## 1. Task Dự án có loại việc, giờ, kết quả (phase 05)

| Cột `tab_work_task` | Ý nghĩa |
|---|---|
| `task_type_id` | Loại việc (`tab_work_task_type`); `0` = chưa chọn. Quản trị khai (`setting.write`), ai dùng Dự án cũng chọn được. |
| `estimate_hours` | Giờ ước lượng, nhập tay lúc giao. `NULL` = chưa khai. |
| `actual_hours` | Giờ thực tế, nhập tay, **chỉ khi task đã xong**; không bắt buộc (số chính của báo cáo là thời gian trôi qua). Task nhiều PIC: giờ của CẢ task, chỉ dùng ở mức loại việc. |
| `outcome` | `0` chưa đánh giá · `1` Đạt · `2` Phải làm lại (`WorkTaskOutcome`, code set `work_task_outcome`). |

- Giờ: 0…999, tối đa 2 số lẻ; gửi `0` = xóa giờ.
- Người đặt kết quả: **người tạo task** hoặc **quản lý dự án**; chỉ khi task đã xong. «Phải làm lại» **mở lại** task (xóa `completed_at`, ghi lịch sử 2→1) và GIỮ nhãn «Phải làm lại» cho tới khi task xong lần nữa; mỗi lần xong thì kết quả cũ bị xóa để đánh giá lại.
- Xóa loại việc đã có task dùng = chỉ ngừng dùng (`is_active = 0`), số liệu cũ vẫn đọc được tên.
- AI lập kế hoạch (`work/plan_service`) đặt được `task_type_id`, `estimate_hours`; giá trị rác bị bỏ qua, không làm hỏng cả kế hoạch.

## 2. Thời gian trọn vòng và số lần làm lại (phase 06) — bảng `tab_work_cycle`

Một dòng / (loại phiếu, phiếu, vai, người): vai **Người lập** (1 dòng) + vai **Người xử lý** (mỗi người 1 dòng, cùng thời gian trọn vòng). Dựng gia tăng
mỗi đêm 05:00 VN (`capability.build_cycles`), dựng lại toàn bộ bằng `python -m scripts.backfill_work_cycles`. Giữ 3 năm theo ngày xong.
Thời gian trọn vòng = `done_at − started_at` theo **ngày lịch** (không trừ lễ, nghỉ), lưu bằng giờ.

Định nghĩa nằm ở MỘT chỗ: `backend/app/modules/capability/cycle_specs.py` (`SPECS`). Đổi một dòng rồi chạy lại backfill.

| Loại phiếu | «Xong» (trạng thái) | Hủy / Từ chối | «Làm lại» = đếm | Người lập | Người xử lý (mốc bắt đầu) |
|---|---|---|---|---|---|
| YCMH | `completed`/`done` | `cancelled` · `rejected` do audit `rejected` | audit `returned` | `requester_id` | **người phụ trách từng DÒNG hàng** (mốc: ngày tiếp nhận) + `assignee_id` nếu có |
| YCBG | `done` (không phải `survey_done`) | `cancelled` | status → `rejected` (= Trả về) | `requester_id` | người phụ trách từng dòng (mốc: ngày tiếp nhận dòng) |
| ĐMH | `received` (Đã nhận đủ) **hoặc** `completed`; mốc xong = lần ĐẦU (lúc nhận đủ) | `cancelled` | status → `rejected` (= Trả về) | tài khoản `created_by` → nhân sự | `nspt_id` |
| YCTT | `paid` | `cancelled` | — (không có trả về) | `created_by` → nhân sự | — |
| Văn bản | 3 hoặc 4, **lần đầu**; hết hiệu lực/lưu trữ rồi vẫn tính đã xong việc soạn | 7 (bãi bỏ) · 10 (từ chối) | 9 (trả về) | `drafter_employee_id` | — |
| Đặt xe | 5 | 7 hủy · 6 từ chối | 8 | `requester_id` | — |
| Duyệt dấu | 4 | 6 hủy · 5 từ chối | 7 | `requester_id` | Văn thư đóng dấu (`completed_by` → nhân sự; mốc: lúc duyệt) |
| Phòng họp | 3 | 6 hủy · 4 từ chối | 5 | `requester_employee_id` | — |
| Nghỉ phép | 3 | 6 hủy · 4 từ chối | 5 | `employee_id` | — |
| Task Dự án | 2, **lần cuối** | 3 | status 2 → 1 (mở lại) | `creator_employee_id` | mỗi PIC (mốc: lúc được giao) |

Nhận hàng không có vòng đời riêng nên **không tính** (là một bước của ĐMH).

Ghi chú diễn giải:
- Hai sự kiện cùng loại cách nhau ≤ 120 giây (nhật ký thay đổi và audit kể cùng một chuyện) được gộp làm một.
- YCMH dùng `rejected` cho cả «từ chối» lẫn «trả về»: audit quyết định; sự kiện sau cùng là «trả về» thì phiếu coi là còn chạy.
- `is_estimated = 1`: không có dấu vết trong nhật ký (phiếu cũ, hoặc tự chuyển trạng thái không ghi audit) nên `done_at` lấy từ cột mốc của chính bảng
  (`completed_at`, `decided_at`, `issued_at`) hoặc `updated_at`. **Báo cáo phải cho biết hoặc loại các dòng này** khi nói về thời gian.
- `is_late`: task có hạn; xong thì so ngày xong (giờ VN) với hạn, còn mở thì so hôm nay lúc dựng. Dòng đang mở chỉ được tính lại khi phiếu bị chạm.

### Kết quả kiểm tra nguồn lịch sử (spike, 20/10/2026, DB local)
- Đổi trạng thái qua ORM (kể cả mở lại task 2→1) **có** dòng `tab_change_log` field `status`; `query.update()` hàng loạt thì **không** — đã thử trực tiếp.
  Rà mã: không đường nào dùng `update()` hàng loạt để đổi `status` của 10 bảng trên (chỉ `tab_approval_task`, xóa mềm, `is_urgent`).
- `tab_change_log` chỉ bắt đầu từ **16/09/2026** (local); `tab_audit_log` từ **01/07/2026**. Nên Thu mua dùng cả hai nguồn; các bảng còn lại chỉ có change_log nên
  phiếu cũ trước ngày bật là dòng ước tính. Việc nền Celery / script không mở ngữ cảnh thì cũng không ghi nhật ký (đồng bộ app đặt xe cũ, nạp từ tệp).
- YCMH tự hoàn thành (`sync_from_purchase_orders`) không ghi audit (3/10 phiếu local) → dòng ước tính từ `updated_at`.
- `tab_purchase_request.assignee_id` là id nhân sự nhưng **luôn 0** (72/72 dòng local, bị xóa lúc duyệt/từ chối); người phụ trách thật nằm ở
  `tab_purchase_request_item.assignee` (mã nhân viên) → dùng cột đó.

## 3. Tải đang ôm, tính ngay lúc hỏi (phase 07) — `capability/workload_service.current_load`

Không bảng mới, không cache; ≤ 10 truy vấn bất kể số người (143 người local: 69 ms). **Không tự gác quyền** — người gọi truyền phạm vi đã duyệt;
không truyền `company_id` / `department_ids` / `employee_ids` thì trả `[]`. API quản trị: `GET /api/work-capability/load` (`setting.read`).

| Số | Nguồn |
|---|---|
| `approvals_pending`, `approvals_overdue` | `tab_approval_task` chờ, phiên duyệt còn mở (khớp màn «Việc của tôi» — đã đối chiếu 60 người) |
| `delegated_in`, `delegated_in_overdue`, `delegated_out_to` | ủy quyền còn hiệu lực hôm nay; việc tính ở **người ủy quyền**, người nhận thấy số riêng, **không cộng vào tổng** |
| `work_open`, `work_overdue`, `work_estimate_hours_open` | task Dự án đang mở (PIC), chưa xóa mềm; quá hạn = hạn < hôm nay (VN); Σ giờ ước lượng |
| `pr_handling` | số YCMH đang xử lý theo người phụ trách từng dòng hàng (phiếu chưa xong, dòng chưa xong/hủy) |
| `pr_approval_pending` | YCMH `submitted` theo `head_of_dept_id` — **đại diện** (duyệt Thu mua không gán người) |
| `po_handling` | ĐMH theo `nspt_id`, trừ `draft/received/completed/cancelled/rejected` — «Đã nhận đủ» (`received`) tính là XONG (đại ca chốt 20/10/2026) |
| `survey_lines_handling` | dòng YCBG chưa hoàn thành, chưa tạo YCMH, phiếu cha đang chạy |
| `docs_pending_issue` | văn bản trạng thái 11 theo **người soạn thảo** (`drafter_employee_id`) — kế hoạch ghi `clone_assignee_employee_id` là nhầm: `can_issue` so người soạn |
| `on_leave_today`, `leave_days_ahead` | đơn nghỉ đã duyệt giao `[hôm nay, hôm nay + horizon]` (ngày lịch) |
| `open_items_total` | tổng đếm thô các số «đang xử lý» + duyệt chờ. **Không trọng số** — AI tự cân và giải thích |

Quyền xem: xem mục 4.

## 4. Báo cáo «Năng lực theo loại việc» (ReportKey 16) và hợp đồng cho AI (phase 08, duoc-CR-657)

**Quyền.** Số theo TỪNG NGƯỜI (thời gian trọn vòng, làm lại, tải) chỉ quản trị mặc định, qua khóa báo cáo 16 (gán được cho người khác ở tab «Báo cáo»
của Phân quyền) cộng `setting.read` / `setting.export`. Gác cả `/api/work-capability/summary`, `/summary/export` và `/load`. Mỗi lần mở có dòng `tab_request_log`.

**Luật diễn giải (đại ca chốt 20/10/2026).**
- Số theo người (và theo loại) chỉ hiện khi **≥ 5 mẫu** cùng loại; dưới ngưỡng mọi số là `null`, `below_threshold = true` — giao diện ghi «chưa đủ mẫu».
- Dòng `is_estimated` **không bao giờ** vào trung vị/p90/làm lại: chỉ đếm riêng ở `n_estimated` («+N ước tính»). Phiếu đặt xe nhập từ hệ cũ (toàn dòng ước tính) vì thế không làm bẩn số liệu.
- Đơn vị: thời gian = ngày lịch (2 số lẻ); `rework_rate` = số lần làm lại / số phiếu xong (0…n, giao diện hiện %); `late_rate` = tỷ lệ trên các phiếu có hạn; `est_ratio_p50` = trung vị (giờ thực tế / giờ ước lượng).
- «Chậm» có thể chỉ là việc khó hơn — trang có dải nhắc «chỉ dùng tham khảo, không chấm điểm».

**API** (`capability/controller.py`): `GET /summary` (`preset|date_from|date_to`, `company_id`, `department_id[]`, `kind`, `task_type_id`, `role` mặc định 2 = Người xử lý) trả `types[]` + `people[]` + `n_estimated`;
`GET /summary/export` (Excel); `GET /load` (tải tức thì, phải truyền phạm vi). `/summary` tốn **3–4 truy vấn cố định**, `/load` ≤ 10 (bất kể số người; xem test đếm truy vấn).

**Hai hàm cho trợ lý (Agent 4 / A1 bọc thành công cụ MCP — ERP KHÔNG làm công cụ).** Tệp `capability/ai_contract.py`, nhận `db` + `user` (hàm tự hỏi khóa 16 qua `can_view_report`):
- `suggest_assignees(db, user, *, kind, task_type_id=0, company_id=None, department_ids=None, employee_ids=None, limit=5, window_days=180, now=None, profile=None) -> list[dict]`
  - phạm vi PHẢI do người gọi truyền (trưởng phòng: phòng mình + phòng con; hàm không tự mở rộng); không truyền → `[]`.
  - xếp hạng (KHÔNG phải điểm): ① không nghỉ hôm nay ② đủ mẫu trước ③ ít `open_items_total` ④ trung vị ngắn ⑤ làm lại ít. Mỗi mục: `rank, employee_id, employee_code, full_name, reasons[]` (`ON_LEAVE_TODAY`, `BELOW_THRESHOLD`).
  - **có khóa 16**: thêm `stats` (đủ trường ở trên) và `load` (các số thành phần của `current_load`). **Không có khóa**: chỉ thứ tự + lý do, không số (doc 22 §6: người khác chỉ thấy kết quả đề xuất).
- `get_capability(db, user, employee_id, *, kinds=None, window_days=180, now=None, profile=None) -> {"employee_id", "window_days", "by_type": [...], "load": {...}|None}` — ném `CapabilityForbidden` (PermissionError) nếu không có khóa 16.
- Hai hàm gọi `stats_service.task_type_stats` / `workload_service.current_load` — A1 **không** tự viết lại công thức; tự cân tải với tốc độ và giải thích bằng lời. Không có điểm tổng.
- Lõi dùng chung: `stats_service.fetch_stats(db, StatsFilter(...))` (≤ 4 truy vấn). `StatsFilter.unrestricted=True` chỉ dành cho đường API quản trị đã qua `require_report`.

# Phase 04 — Snapshot tuần + nhóm so sánh + nhận kiểu (pha 3), đăng ký Celery

**Ưu tiên:** P1 · **Effort:** 8h · **Phụ thuộc:** 02, 03 · **Trạng thái:** pending

## Ngữ cảnh
- §4 (kiểu làm việc) và §7 (khuôn dữ liệu cho AI) của thiết kế. Công thức "Snap": [`metric-definitions.md`](metric-definitions.md).
- `tab_user_role(user_id, role_id)` — một người nhiều vai trò. Vai trò quản trị: `admin`, `ADMINISTRATOR` (`report_access/seed_defaults._ADMIN_ROLE_CODES`).
- Celery `timezone="Asia/Ho_Chi_Minh"`, `enable_utc=False` → crontab ghi thẳng giờ VN.

## Nhóm so sánh (cohort)
1. Tập đo = người có dòng `tab_usage_daily` trong cửa sổ W (4 tuần) và user active.
2. Vai trò ứng viên = vai trò của người đó TRỪ vai trò quản trị.
3. Chọn vai trò **cụ thể nhất có đủ ≥ 5 người trong tập đo** (ít thành viên nhất trong số đạt ngưỡng; hòa → role_id nhỏ). Lý do: "Nhân viên" chung ai cũng có — chọn vai trò đông nhất thì mọi người so với cả công ty.
4. Không vai trò nào đạt → pháp nhân (`employee.company_id`) nếu ≥ 5 → ngược lại toàn công ty. Ghi `cohort_kind`, `cohort_key`, `cohort_size` vào snapshot (hồ sơ ghi rõ "đang so với …").
5. Trung vị nhóm tính trên thành viên CÓ giá trị của chỉ số đó (bỏ người `unmeasured`); chính người đó có trong trung vị.

## Khuôn snapshot `metrics` (schema_version = 1) — sẵn cho pha 4
```json
{
  "period": {"start": "2026-10-12", "end": "2026-10-18", "window_weeks": 4},
  "subject": {"tenure_days": 120, "cohort_role_id": 7},
  "context": {"workdays_net": 22.5, "leave_days": 1.5, "holidays": 0, "on_behalf_received": 3, "tracking_since": "2026-10-20"},
  "metrics": {"active_ratio": {"v": 0.95, "med": 0.9, "trend": [0.9, 1.0, 0.92, 0.95]}, "...": {}},
  "lists": {"top_screens": [["/procurement/purchase-orders", 120, 480000]], "top_paths": [["/a", "/b", "/c", 9]],
            "heatmap": [[0, 0, "...24 số"], "...7 hàng"], "docs": {"purchase_order": {"c": 14, "s": 14, "ret": 2}}},
  "unmeasured": {"notif_read_p50_min": 1, "form_submit_p50_ms": 2},
  "labels": [{"code": 2, "score": 0.8, "evidence": ["approval_wait_p50_h", "pending_now"]}]
}
```
Luật: chỉ SỐ và MÃ (route mẫu, tên entity, khóa chỉ số là định danh, không phải văn bản tự do); không tên người, không bình luận, không từ khóa. Khóa chỉ số lấy từ `metric_catalog.py`.

## Luật nhận kiểu (`label_rules.py`, thuần; ngưỡng gom ở `label_thresholds.py`)
Cửa sổ W 4 tuần; "×med" = so trung vị nhóm. Thiếu dữ liệu tối thiểu → KHÔNG gắn nhãn (không phải "không phải kiểu này").
| Mã | Kiểu | Điều kiện gắn (đề xuất đầu, chỉnh sau 2–4 tuần chạy thật) | Dữ liệu tối thiểu |
|---|---|---|---|
| 1 | Làm dồn | `month_end_create_share` ≥ 0,4 HOẶC `batch_approval_share` ≥ 0,5 HOẶC 3 ô đậm nhất của heatmap ≥ 50% lượt | ≥ 10 phiếu / ≥ 10 lượt duyệt / ≥ 200 lượt |
| 2 | Nút thắt duyệt | `approval_wait_p50_h` ≥ 2×med VÀ ≥ 8 giờ, HOẶC `pending_now` ≥ 10 | ≥ 5 việc duyệt xong |
| 3 | Dùng Excel song song | `exports` ≥ 3/tuần VÀ (`export_per_list_view` ≥ 0,3 HOẶC cùng entity xuất ≥ 3/4 tuần) | ≥ 3 lượt xuất |
| 4 | Người mới đang vướng | `tenure_days` ≤ 90 VÀ ≥ 2 trong {422 ≥ 2×med, bỏ form ≥ 2×med, 403 ≥ 5, help_views ≥ 3, active_ratio < 0,5} | ≥ 5 ngày làm việc ròng |
| 5 | Người thạo | `saved_prefs` ≥ 1 VÀ 422 ≤ med VÀ `distinct_screens_30d` ≥ p75 nhóm VÀ (form_submit ≤ med nếu đo được) | ≥ 10 ngày active |
| 6 | Hay đi lạc | `http_403` ≥ 5 VÀ ≥ 2×med, HOẶC `loop_share` ≥ 0,2 | ≥ 50 lượt xem màn hoặc ≥ 5 lượt 403 |
| 7 | Làm trên điện thoại | `mobile_write_share` ≥ 0,6 | ≥ 20 lượt ghi |
| 8 | Phiếu kém chất lượng | `returned_rate` ≥ 0,2 VÀ ≥ 2×med, HOẶC `edits_after_submit_share` ≥ 0,3 | ≥ 5 phiếu đã gửi |
| 9 | Nhờ làm hộ | `on_behalf_received` / (phiếu tự lập + được lập hộ) ≥ 0,5 | ≥ 5 phiếu |
| 10 | Ít dùng | `active_ratio` < 0,4 VÀ med nhóm ≥ 0,7 (đã trừ nghỉ phép; ngày được bấm hộ tính là có làm) | `workdays_net` ≥ 8 |
`score` = mức vượt ngưỡng chuẩn hóa 0..1 (để sắp thứ tự); `evidence` = khóa chỉ số đã kích hoạt điều kiện.

## Kiến trúc (`usage_profile/`)
```
metric_catalog.py       khóa chỉ số → (đơn vị, mục §3, pha, hướng tốt/xấu) — nguồn duy nhất, API trả kèm
cohort.py               chọn nhóm + trung vị/p75 (thuần)
snapshot_sources.py     truy vấn CỐ ĐỊNH cho cả công ty: usage_daily W · audit chuỗi phiếu (subquery entity_id gửi trong W) ·
                        approval_task (decided trong W + đang chờ) · notification W · mention + phản hồi · comment ·
                        assistant_message/change · user_preference · import_batch · work_task(+assignee) · ticket ·
                        ui_event PAGE_VIEW tuần (đường đi) · user_role + đếm thành viên · user/employee · snapshot 3 tuần trước (xu hướng)
snapshot_metrics.py     tính chỉ số + unmeasured (thuần)
snapshot_paths.py       bộ ba màn + vòng lặp theo (session_id, tab_key) (thuần)
label_thresholds.py · label_rules.py
snapshot_builder.py     ghép + ghi idempotent (DELETE nhãn/snapshot của tuần rồi INSERT)
tasks_snapshot.py       `usage.build_weekly_snapshots(week_start=None)`: trước khi dựng, gọi gom ngày cho ngày còn thiếu trong W (tự lành)
```

## Celery (`core/celery_app.py` — phase này sở hữu)
- `imports` += `app.modules.usage_profile.tasks_daily`, `.tasks_snapshot`, `.tasks_cleanup`
- beat: `usage.cleanup_ui_events` 04:20 hằng ngày · `usage.aggregate_daily` 04:30 hằng ngày · `usage.build_weekly_snapshots` thứ Hai 05:15.
  Không trùng giờ backup (01:00/13:00), archive (03:00 ngày 1), dọn request_log (03:40), system_log (03:50), attachment (04:10).

## Tệp
- Tạo: 9 tệp trên; test `test_ho_so_lam_viec_snapshot_cr641.py`, `test_ho_so_lam_viec_nhan_kieu_cr641.py`
- Sửa: `core/celery_app.py`

## Todo
- [ ] metric_catalog (khóa khớp metric-definitions.md)
- [ ] cohort + test ngưỡng 5, loại vai trò quản trị
- [ ] snapshot_sources (số truy vấn cố định) + metrics + paths
- [ ] label_rules + thresholds + test biên
- [ ] builder idempotent + task tự lành ngày thiếu
- [ ] đăng ký Celery 3 job

## Kiểm
- Cohort: vai trò A 6 người, B 30 người, cùng có → chọn A; A 4 người → B; không vai trò nào ≥ 5 → pháp nhân; pháp nhân < 5 → toàn công ty; admin không được chọn.
- Chuỗi phiếu: tạo → update ×3 → submit → update → return(người khác) ⇒ drafts=3, sửa-sau-gửi=1, bị trả=1.
- Duyệt: 5 việc 2/4/6/8/30 giờ → p50 = 6, p90 đúng nội suy đã chọn (ghi rõ cách tính trong docstring).
- Đường đi: 2 tab xen kẽ không tạo bộ ba giả; A→B→A tính vào `loop_share`.
- Chưa bật thu thập → mọi khóa P2 nằm trong `unmeasured` mã 1, KHÔNG có giá trị 0.
- Xu hướng: lấy đúng 3 snapshot trước + tuần này.
- **Khuôn pha 4**: duyệt đệ quy JSON — mọi giá trị là số/bool/None/list/dict; chuỗi chỉ được phép ở vị trí route mẫu/khóa entity (danh sách trắng).
- Nhãn: mỗi luật 3 ca — trúng, sát dưới ngưỡng, thiếu dữ liệu tối thiểu.
- **Đếm truy vấn**: 3 người vs 12 người → bằng nhau.
Chạy: `docker compose exec -T api python -m pytest test/backend/test_ho_so_lam_viec_snapshot_cr641.py test/backend/test_ho_so_lam_viec_nhan_kieu_cr641.py -q`

## Rủi ro
| Rủi ro | K × T | Giảm thiểu |
|---|---|---|
| Nhãn sai gây hiểu lầm về nhân viên | Trung bình × Cao | ngưỡng tối thiểu, so nhóm, hiện bằng chứng + "đang so với", mặc định đọc theo KẾT QUẢ (§8); 4 tuần đầu coi là thử, chỉnh `label_thresholds.py` |
| Người nhiều vai trò lệch nhóm | Trung bình × Trung bình | luật "cụ thể nhất ≥ 5" cố định + hiện tên nhóm trên hồ sơ |
| Mốc "tới lượt" của duyệt lần lượt sai | Trung bình × Trung bình | kiểm `task_service`; nếu việc tạo sẵn thì lấy `decided_at` của việc trước |
| Job tuần chạy lâu | Thấp × Thấp | ~20 truy vấn cố định; ~30k dòng ui_event/tuần |

## Bảo mật
Snapshot không chứa văn bản tự do (§7.4) → khi pha 4 đưa cho AI không lộ bình luận/từ khóa, không có chỗ cho câu lệnh lừa AI.

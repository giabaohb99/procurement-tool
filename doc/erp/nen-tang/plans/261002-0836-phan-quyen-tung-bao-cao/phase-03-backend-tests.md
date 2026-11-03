# Phase 03 — Backend test: test mới + vá test HTTP cũ

**Ưu tiên:** P1 · **Effort:** 3h · **Trạng thái:** done · **Phụ thuộc:** 02

## Context
- `test/backend/conftest.py` (`db`, `seed`, `cap_quyen`), khuôn `client_as` ở `test_bao_cao_van_ban.py:146`
- Luật test: cố làm nó SAI; SQLite không ép `VARCHAR` → kiểm `max_length` ở tầng schema (`pytest.raises(ValidationError)`).

## Fixture mới (conftest.py)
`gan_bao_cao(db)` → `_gan(subject_kind, subject_id, *keys, effect=1)` chèn dòng `ReportAccess`; mặc định mọi `ReportKey` khi không truyền khóa. Dùng chung cho test mới và test cũ.

## Test mới (tách tệp <200 dòng)
`test_phan_quyen_bao_cao_gac_duong.py`
- Soi `app.routes`: mọi `APIRoute` có path kết thúc `/summary` hoặc `/summary/export` phải nằm trong ĐÚNG MỘT trong hai danh sách: `GATED` (26 đường, kèm khóa mong đợi) hoặc `NOT_REPORT` (payables, system-logs, customs rows, leave tools) — thêm `/summary` mới mà không phân loại là đỏ.
- Mỗi `ReportKey` xuất hiện đúng 2 lần (summary + export); không khóa nào thiếu/thừa.
- Tham số hóa 26 đường: tài khoản đủ `read`+`export` trên entity, CHƯA gán → 403; gán qua vai trò → 200 (`preset=this_month&compare=none`).
- Gác KÉP: được gán nhưng thiếu quyền entity → 403; có `read` mà thiếu `export` → `/export` 403.
- Gán khóa A không mở khóa B (gán `WORK` → `/api/documents/summary` vẫn 403).

`test_phan_quyen_bao_cao_chu_the.py` (gọi `viewable_keys` trực tiếp)
- Khớp theo từng chủ thể: nhân sự · phòng chính · phòng KIÊM NHIỆM · pháp nhân · vai trò.
- CẤM thắng: cho phép qua vai trò + cấm qua phòng → không thấy; cấm trên nhân sự đè cho phép trên pháp nhân.
- Dòng thu hồi không tính (cả cho phép lẫn cấm: thu hồi dòng cấm → thấy lại).
- `valid_to` hôm qua / `valid_from` ngày mai → không tính.
- Tài khoản không có `employee_id` và không vai trò → `set()`, không nổ.
- Số truy vấn của `viewable_keys` = 1 (đếm bằng event listener, cùng khuôn test «gom SQL» sẵn có).

`test_phan_quyen_bao_cao_cau_hinh_api.py`
- `GET` cần `role.read` (không có → 403); `POST/DELETE` cần `role.write`.
- `GET` trả đủ 13 mục, đúng thứ tự khóa, có `label/group`, tên chủ thể đúng, KHÔNG chứa dòng thu hồi.
- `POST` trùng chủ thể + cùng effect → `updated`, không đẻ dòng; chủ thể id không tồn tại → `skipped`; `key=999` → 404; `subjects=[]` / 201 phần tử → 422; `subject_kind=9`, `effect=3` → 422.
- `reason` 501 ký tự → `ValidationError` ở schema (không tin SQLite).
- `DELETE` lần 2 → 400; dòng còn trong DB với `revoked_at`.
- Audit: có dòng `entity="report_access"` sau POST/DELETE.
- `/api/auth/me` có `report_keys` khớp `viewable_keys`.

`test_phan_quyen_bao_cao_mac_dinh_admin.py`
- `ensure_report_access_defaults` trên DB có role `admin`: chèn 13 dòng; chạy lần 2 → 0.
- Thu hồi dòng admin của 1 khóa rồi chạy lại → KHÔNG chèn lại (không ghi đè chỉnh sửa).
- Khóa đã có dòng gán cho người khác (không phải admin) → không chèn admin.
- Không có role `admin` → 0, không nổ.
- `ReportKey` liên tục 1..N, không trùng; `REPORT_META` đủ mọi khóa; bộ mã `report_key` có trong `all_sets()`.
- Migration: không chạy alembic trong SQLite — kiểm thủ công ở phase 01 (lên/xuống/lên).

## Vá test cũ (ăn 403 sau khi gác)
Tệp gọi `/summary` qua HTTP: `test_bao_cao_cong_viec.py`, `test_bao_cao_hanh_chinh.py`, `test_bao_cao_nhan_su.py`, `test_bao_cao_cache_tong_quan.py`, `test_bao_cao_phe_duyet.py`, `test_bao_cao_van_ban.py` → sau `cap_quyen(...)` gọi `gan_bao_cao(4, role.id)`. Bài nào khẳng định 403 do thiếu quyền entity giữ nguyên (vẫn 403). Không nới khẳng định nào chỉ để xanh.
- `test_pham_vi_luat_bat_bien.py`: thêm `report_access/controller.py` vào `BB4_CONTROLLER_MIEN_TRU` kèm lý do thật.

## Lệnh (chỉ phần vừa sửa)
```bash
docker compose exec -T api python -m pytest -q \
  test/backend/test_phan_quyen_bao_cao_*.py test/backend/test_bao_cao_*.py \
  test/backend/test_pham_vi_luat_bat_bien.py test/backend/test_status_catalog_b01.py \
  test/backend/test_van_ban_thu_muc_quyen*.py test/backend/test_van_ban_thu_muc.py
```

## Sở hữu tệp
Tạo 4 tệp `test_phan_quyen_bao_cao_*.py`. Sửa `conftest.py` + 6 tệp `test_bao_cao_*` ở trên + `test_pham_vi_luat_bat_bien.py`.

## Todo
- [x] fixture `gan_bao_cao`
- [x] 4 tệp test mới
- [x] vá 6 tệp HTTP cũ + BB-4
- [x] lệnh trên xanh

## Tiêu chí xong
Lệnh trên xanh; bỏ decorator của 1 đường bất kỳ → test soi route đỏ (thử tay 1 lần rồi hoàn lại).

## Rủi ro
| Rủi ro | K×T | Giảm thiểu |
|---|---|---|
| Đường cần tham số bắt buộc → 422 thay vì 200 | TB×Thấp | Bảng tham số riêng từng đường trong test |
| Test đếm truy vấn qua HTTP tăng 1 | Thấp×Thấp | Đã soi: test đếm truy vấn gọi service trực tiếp, không qua route |

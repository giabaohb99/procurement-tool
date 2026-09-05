# PHA 5 — Runtime luồng duyệt (bridge) + Test tổng thể + Phân quyền

> Tổng quan: [README.md](README.md) · Log: [TIEN-DO.md](TIEN-DO.md). Trạng thái: **CHƯA LÀM**.
> Khuôn 1-1: `vehicle_booking/approval_bridge.py` + `test_dat_xe_luong_duyet_runtime.py` + `test_dat_xe_tong_the.py`.

## Mục tiêu
Nối **cổng 1 (TBP)** vào **engine luồng duyệt cấu hình** (`approval_flow`) để duyệt đa-bước có thể cấu
hình trên `/approval/flows` — **tương thích ngược** (cờ tắt = đường trực tiếp PHA 2). Phủ **test tổng
thể** luồng 2 cổng + **kịch bản phân quyền** đầy đủ.

## Phạm vi & việc cụ thể
- [ ] `seal_request/approval_bridge.py`: `entity_hooks.register("seal_request", on_approved, on_rejected, on_returned, on_withdrawn)` + `register_subject` + `register_reader`; `submit_for_approval` mở phiên.
- [ ] `service._after_submit`: cờ `ApprovalSwitch` bật + có luồng khớp entity `seal_request` → mở phiên engine; tắt → đường trực tiếp (PHA 2). `block_legacy_path` chặn `/approve` `/return` `/reject` trực tiếp khi phiên engine đang chạy.
- [ ] FE: `SealApprovalPanel` trên chi tiết (Duyệt/Trả/Từ chối qua engine + dấu vết) — reuse `ApprovalActionDialog` + `ApprovalTrailCard`; ẩn cụm nút cổng-1 trực tiếp khi `approval_running` (field mới ở serialize chi tiết).
- [ ] Tạo **luồng duyệt cấu hình** mẫu "Duyệt yêu cầu đóng dấu" (entity `seal_request`) trên `/approval/flows` + seed.
- [ ] **Test tổng thể** tầng service (`test_duyet_dau_tong_the.py`).
- [ ] **Kịch bản phân quyền** (`test_duyet_dau_phan_quyen.py`) + tài liệu kiểm tay (như `dat-xe-duyet-dau/test-phan-quyen.md`).
- [ ] ↳ E2E trình duyệt (Playwright, host-run) — luồng 2 cổng.

## Thiết kế kỹ thuật
- **Cổng 2 (Văn thư) KHÔNG qua engine** — luôn là bước "đóng dấu" sau khi engine cổng 1 kết thúc *Đã duyệt*. Engine chỉ thay cổng 1 (TBP → có thể nhiều bước).
- `block_legacy_path` chỉ chặn nhóm endpoint **cổng 1**; `/complete` (Văn thư) không đụng.
- Test tổng thể (mô hình `test_dat_xe_tong_the.py`) phủ:
  - Happy path: NS tạo (đủ tệp) → gửi → TBP duyệt → Văn thư hoàn thành → *Hoàn thành*.
  - Nhánh: TBP trả/từ chối; Văn thư trả/từ chối; gửi duyệt **thiếu tệp signed_doc → 400**.
- Kịch bản phân quyền (dùng fixture `cap_quyen` + `get_perm_profile` + `apply_scope`):
  | Vai trò | Phạm vi | Kỳ vọng |
  |---|---|---|
  | NS1 | own | chỉ thấy phiếu mình tạo |
  | TBP1 | dept | thấy phiếu cùng phòng, không thấy phòng khác |
  | Văn thư CTY-A | company | chỉ thấy phiếu công ty A (theo `company_id` con dấu) |
  | Giám đốc CTY-A | company | chỉ thấy phiếu công ty A |
  | seal_admin | all | thấy tất cả |
  - Văn thư A **không** hoàn thành được phiếu công ty B.

## Cấu hình / migration
- Không thêm cột. Seed luồng duyệt cấu hình + tài khoản test (khuôn `seed_datxe_test_accounts` / `_cases`).
```bash
docker compose exec -T api python -m pytest test/backend/test_duyet_dau_tong_the.py test/backend/test_duyet_dau_phan_quyen.py -q
docker compose exec -T api python -m pytest test/backend -q      # toàn bộ
docker compose exec erp npm run check
```

## Chống trùng / Idempotent
- Cờ `ApprovalSwitch` tắt → hành vi y hệt PHA 2 (không đổi dữ liệu cũ).
- Bật engine phải **ẩn** cụm nút cổng-1 trực tiếp để tránh 2 đường đổi trạng thái (lỗi kinh điển của bridge).

## Kiểm thử & tiêu chí
- Cờ tắt: luồng trực tiếp xanh (PHA 2 tests vẫn pass).
- Cờ bật + luồng khớp: gửi duyệt mở phiên; `/approve` trực tiếp bị `block_legacy_path`; duyệt qua panel engine → *Đã duyệt* → Văn thư hoàn thành.
- Ma trận phân quyền 5 vai trò xanh; Văn thư/Giám đốc lọc đúng `company_id`.
- `pytest test/backend -q` và `npm run check` xanh.

## Rủi ro & lưu ý
- **Hai đường đổi trạng thái** (trực tiếp vs engine) là nguồn lỗi lớn nhất — bật engine thì khóa đường cũ ở cả BE (`block_legacy_path`) lẫn FE (ẩn nút).
- Engine chỉ thay **cổng 1**; đừng vô tình đẩy **cổng 2 (đóng dấu)** vào engine — Văn thư là bước vận hành thực tế, không phải bước phê duyệt.
- E2E cần host + tài khoản demo (Văn thư/TBP/NS + đa công ty) — chạy trên host như Đặt xe.

# Phase 05 — Tài liệu, bài kiểm, phát hành

| Bản | Ngày | Người phụ trách | Trạng thái | CR liên quan |
|---|---|---|---|---|
| 1 | 25/11/2026 | planner | Nháp | duoc-CR-784, bao-CR-789 |

Ưu tiên P2 · 2 giờ · cần 02–04.

## Ma trận kiểm
| Tầng | Kiểm gì | Lệnh |
|---|---|---|
| Đơn vị + tích hợp (pytest, SQLite) | luật sổ giá mới, nguồn báo giá, hàm chuyển dữ liệu của migration, đếm truy vấn | `docker compose exec -T api python -m pytest test/backend -k cr784 -q --timeout=120` (chia nhóm nếu nặng) |
| Migration thật (MySQL) | `upgrade` → `downgrade -1` → `upgrade` trên bản sao DB dev nạp vào local | `alembic upgrade head` / `downgrade -1`; so số dòng, tổng `price`, tập khóa trước / sau |
| Cổng | ruff `app`, `kiem_tai_lieu.py` (kèm `KIEM_TAI_LIEU_ROOT=$PWD`), typecheck + lint v2, vitest `src/modules/procurement` | như CLAUDE.md |
| Tay (dev) | Lịch sử mua hàng v1 (devthumua) + v2 (deverp): dấu ĐMH đang mở, cột Nguồn; báo giá form + Excel | |

## Tài liệu
- `doc/erp/thu-mua/tai-lieu-ky-thuat/`: bảng nguồn sổ giá + nguồn báo giá (một chỗ duy nhất), luật `line_stage`.
- `api.md` của thu mua: trường mới `line_stage`, `is_open`, `source_type` / `source_id` báo giá, lỗi 409; chạy `dung_bang_api.py`.
- Đánh dấu luật "nguồn 1 chỉ chèn / nguồn 2 xóa khi vào lịch sử" ở kế hoạch 261120 phase-01 / 02 là *thay bằng* kế hoạch này.
- Sổ: dòng CR ở `change-log.md` (đặt chỗ ngay khi nhận việc) + mục `nhat-ky-task.md` (mã mục duy nhất, câu trọn vẹn).
- HDSD: chỉ thêm câu "cột Nguồn" ở bài Báo giá VTBB nếu có giao diện (seed_help + reindex RAG); sổ giá không đổi chữ người dùng.

## Phát hành
1. Gộp nhánh định mức (`bompart784`) → rồi `opt784` vào `erp-v2` → dev chạy migration (đếm trước bằng câu chỉ đọc của phase 02 / 03).
2. Chạy `scripts/backfill_product_price_ledger.py --dry-run` trên dev: số chèn / sửa / xóa phải bằng 0 (sổ đã khớp luật mới).
3. Báo bao-CR-789: chuỗi migration CR-784 lên prod gồm `pkgcost784 … ppld784, bompart784, opt784`; prod chưa có dữ liệu nên
   không có bước chuyển, chỉ cần backfill sổ giá sau khi lên.

## Quay lui
Theo từng phase: revert commit + `alembic downgrade` về `bompart784`; sổ giá dựng lại bằng backfill.

## Việc cần làm
- [ ] Ma trận kiểm xanh
- [ ] Tài liệu kỹ thuật + api.md + sổ
- [ ] Báo bao-CR-789 thứ tự migration

# Phase 01 — Định mức bao bì tách bảng thành phần (đang làm) + việc nối tiếp

| Bản | Ngày | Người phụ trách | Trạng thái | CR liên quan |
|---|---|---|---|---|
| 1 | 25/11/2026 | planner | Nháp | duoc-CR-784 |

Trạng thái: **đang làm** bởi agent khác ở worktree `/Users/tmduoc/.claude/jobs/adfea3fb/tmp/bom784` (nhánh `duoc-cr784-bom-parts`,
chưa commit). Kế hoạch này KHÔNG thiết kế lại; chỉ ghi lại để các phase sau nối đúng và thêm hai việc nhỏ.

## Liên kết
- Migration đang viết: `backend/migrations/versions/bompart784_chuan_hoa_dinh_muc_bao_bi_thanh_phan.py` (revises `ppld784`).
- Mô hình mới: `backend/app/modules/packaging_cost/model.py` của worktree đó, `bom_parts_service.py`.
- Chủ dự án chốt 25/11/2026: "thêm cái type là được, rồi gắn thêm id vô".

## Cấu trúc (đang làm, giữ nguyên)
| Bảng | Cột | Ghi chú |
|---|---|---|
| `tab_packaging_bom` | id, `hh_code` (duy nhất), `hh_name`, `legal_name`, `carton_qty` INT, 4 cột kiểm toán | đầu phiếu; bỏ 5 cột mã + 5 chỉ mục đơn |
| `tab_packaging_bom_part` | id, `bom_id` FK ON DELETE CASCADE, `part_type` SMALLINT (`PackagingRole`), `part_code` String(50) | duy nhất `(bom_id, part_type)`, chỉ mục `(part_code)` |

Đọc API giữ tên trường phẳng cũ (`bottle_code`...) qua `column_property` chỉ đọc, nên v1 + v2 không phải đổi.

## Việc nối tiếp đề xuất (gửi agent đang làm, không mở phase riêng)
1. **Chỉ mục phủ cho tra ngược.** Câu "sản phẩm nào dùng mã X" (màn Tác động, chế độ sản phẩm của Lịch sử, đếm số sản phẩm
   dùng) cần `bom_id` + `part_type` theo `part_code`. Chỉ mục `(part_code)` chỉ mang thêm `id` (khóa chính), phải quay về bảng
   lấy `bom_id`. Đổi thành `ix_pbom_part_code (part_code, part_type, bom_id)` — vẫn phục vụ mọi chỗ đang lọc theo `part_code`.
   Nên sửa ngay trong `bompart784` (chưa lên đâu) thay vì thêm migration.
2. **`history_service._universe_codes`** đang `union` năm cột cũ của `PackagingBom` — phải đọc `PackagingBomPart.part_code`
   (agent kia đã sửa `history_service.py`; chỉ cần soát lại khi gộp).
3. `carton_qty` INT, 0 = chưa có: giữ (cảnh báo `MISSING_CARTON_QTY` đã dựa vào 0).
4. `hh_code` / `hh_name` là định danh tiếng Việt không dấu (trái luật mục 1) — xem câu C8, đề xuất giữ.

## Rủi ro
| Rủi ro | Khả năng x Ảnh hưởng | Giảm thiểu |
|---|---|---|
| Phase 02 sửa cùng `so_gia_factory_cr784.py` khi nhánh định mức chưa gộp | Cao x Trung bình | Phase 02 chỉ bắt đầu sau khi `bompart784` vào `erp-v2` |
| Hạ cấp `bompart784` mất loại thành phần > 5 | Thấp x Thấp | đã ghi trong migration của agent kia |

## Việc cần làm
- [ ] Gửi agent định mức hai ý 1–2 ở trên
- [ ] Chờ nhánh `duoc-cr784-bom-parts` gộp vào `erp-v2`, ghi revision cuối cùng (để `opt784` trỏ `down_revision`)

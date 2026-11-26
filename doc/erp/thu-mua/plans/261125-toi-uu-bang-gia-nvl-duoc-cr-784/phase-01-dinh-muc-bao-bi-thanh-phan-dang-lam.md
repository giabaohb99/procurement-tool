# Phase 01 — Định mức bao bì tách bảng thành phần + việc nối tiếp

| Bản | Ngày | Người phụ trách | Trạng thái | CR liên quan |
|---|---|---|---|---|
| 1 | 25/11/2026 | planner | Nháp | duoc-CR-784 |
| 2 | 25/11/2026 | điều phối | **Xong, đã commit `erp-v2`** (chưa deploy dev) | duoc-CR-784 |

Trạng thái: **XONG, ĐÃ COMMIT lên `erp-v2` (25/11/2026)**, chưa deploy dev — cần sao lưu DB dev trước khi deploy. Xem mục *Kết quả* bên dưới.

## Kết quả (25/11/2026)
**Đã làm gì và vì sao.** Định mức cũ là một dòng mỗi mã HH với 5 cột mã cố định; thêm loại thành phần mới (PET, phôi, màng
co...) là phải thêm cột, sửa mọi truy vấn. Nay tách thành đầu phiếu + bảng thành phần có cột loại (`part_type`) và nối về đầu
phiếu bằng id (`bom_id`) đúng ý chủ dự án — thêm loại mới chỉ cần thêm một thành viên `PackagingRole` + nhãn, không đổi bảng.

| Hạng mục | Kết quả |
|---|---|
| Migration `bompart784` (revises `ppld784`) | Lên: tạo bảng thành phần, chép 5 cột sang dòng (bỏ mã rỗng), xóa 5 cột + 5 chỉ mục cũ. Xuống: dựng lại cột + chỉ mục, chép ngược, xóa bảng. Chạy thật trên bản sao MySQL lên → xuống → lên: 1.000 định mức thành 3.078 dòng thành phần (1.000 chai / 991 nắp / 983 nhãn / 104 nhãn thùng / 0 thùng); sau khi xuống 1.000/1.000 dòng khớp bảng gốc |
| Chỉ mục | Duy nhất `(bom_id, part_type)`; chỉ mục phủ `ix_pbom_part_code (part_code, part_type, bom_id)` cho tra ngược (EXPLAIN: *Using index*) |
| Mã nguồn | `bom_parts_service.py` mới (đọc mọi định mức + thành phần bằng MỘT truy vấn, đếm số SP dùng mã, ghi mã); mọi dịch vụ duyệt `PackagingRole` thay vì 5 cột; nhập Excel ghi đầu phiếu + thành phần |
| API | Giữ nguyên tên trường phẳng (`bottle_code`...) qua thuộc tính chỉ đọc — màn Định mức và nhập Excel của v1 + v2 không phải sửa; thêm `parts[]` |
| Dùng chung | `core/crud.py` thêm tùy chọn `virtual_fields`, `after_create`; `core/base_controller.py` nhận khóa xếp tính toán do model khai — mặc định giữ hành vi cũ, đã chạy bài kiểm các danh mục khác |
| Kết quả giữ nguyên | Chạy bản cũ và bản mới trên cùng bản sao dữ liệu: 16 bộ JSON (Tác động 500 mã, Tổng hợp, Bảng giá, Giá mua gần nhất, Lịch sử theo SP / theo mã, danh sách định mức) giống hệt từng byte; số truy vấn không đổi |
| Tốc độ (trung vị) | Tác động 500 mã 125 → 102 ms; Tổng hợp 102 → 81 ms; Lịch sử theo mã 203 → 87 ms; danh sách định mức 4 → 23 ms (mỗi dòng một truy vấn con, chấp nhận) |
| Bài kiểm | 796 qua; 17 bài mới (`test_dinh_muc_bao_bi_thanh_phan_cr784.py`: migration, CRUD giữ thành phần đồng bộ, lọc / xếp theo mã thành phần, tra ngược, thêm loại giả định không đổi bảng); 1 bài Trợ lý đỏ sẵn trên mã gốc, không liên quan |

**Lưu ý khi lên dev / prod.** Migration xóa 5 cột → sao lưu DB trước; sau đó chỉ cần khởi động lại api (`start.sh` tự chạy
`alembic upgrade head`). Hạ cấp sẽ mất loại thành phần số lớn hơn 5 (chưa có).

## Liên kết
- Migration đang viết: `backend/migrations/versions/bompart784_chuan_hoa_dinh_muc_bao_bi_thanh_phan.py` (revises `ppld784`).
- Mô hình mới: `backend/app/modules/packaging_cost/model.py` của worktree đó, `bom_parts_service.py`.
- Chủ dự án chốt 25/11/2026: "thêm cái type là được, rồi gắn thêm id vô".

## Cấu trúc (đã làm)
| Bảng | Cột | Ghi chú |
|---|---|---|
| `tab_packaging_bom` | id, `hh_code` (duy nhất), `hh_name`, `legal_name`, `carton_qty` INT, 4 cột kiểm toán | đầu phiếu; bỏ 5 cột mã + 5 chỉ mục đơn |
| `tab_packaging_bom_part` | id, `bom_id` FK ON DELETE CASCADE, `part_type` SMALLINT (`PackagingRole`), `part_code` String(50) | duy nhất `(bom_id, part_type)`, chỉ mục phủ `(part_code, part_type, bom_id)` |

Đọc API giữ tên trường phẳng cũ (`bottle_code`...) qua thuộc tính chỉ đọc (truy vấn con tương quan), nên v1 + v2 không phải đổi.

## Việc nối tiếp đề xuất (gửi agent đang làm, không mở phase riêng)
1. **Chỉ mục phủ cho tra ngược.** Câu "sản phẩm nào dùng mã X" (màn Tác động, chế độ sản phẩm của Lịch sử, đếm số sản phẩm
   dùng) cần `bom_id` + `part_type` theo `part_code`. Chỉ mục `(part_code)` chỉ mang thêm `id` (khóa chính), phải quay về bảng
   lấy `bom_id`. Đổi thành `ix_pbom_part_code (part_code, part_type, bom_id)` — vẫn phục vụ mọi chỗ đang lọc theo `part_code`.
   Nên sửa ngay trong `bompart784` (chưa lên đâu) thay vì thêm migration. **Đã làm.**
2. **`history_service._universe_codes`** đang `union` năm cột cũ của `PackagingBom` — phải đọc `PackagingBomPart.part_code`
   (agent kia đã sửa `history_service.py`; chỉ cần soát lại khi gộp). **Đã làm** (đọc qua `bom_parts_service`).
3. `carton_qty` INT, 0 = chưa có: giữ (cảnh báo `MISSING_CARTON_QTY` đã dựa vào 0).
4. `hh_code` / `hh_name` là định danh tiếng Việt không dấu (trái luật mục 1) — C8 ĐÃ CHỐT đổi sang `fg_code` / `fg_name`, làm ở [phase 06](phase-06-doi-ten-hh-sang-fg.md).

## Rủi ro
| Rủi ro | Khả năng x Ảnh hưởng | Giảm thiểu |
|---|---|---|
| Phase 02 sửa cùng `so_gia_factory_cr784.py` khi nhánh định mức chưa gộp | Cao x Trung bình | Phase 02 chỉ bắt đầu sau khi `bompart784` vào `erp-v2` |
| Hạ cấp `bompart784` mất loại thành phần > 5 | Thấp x Thấp | đã ghi trong migration của agent kia |

## Việc cần làm
- [x] Gửi agent định mức hai ý 1–2 ở trên (đã làm cả hai)
- [x] Tách bảng thành phần, migration `bompart784`, so kết quả cũ / mới giống hệt, bài kiểm (25/11/2026)
- [x] Commit, đẩy `erp-v2` (25/11/2026; revision cuối: `bompart784`, `opt784` trỏ vào đây)
- [x] Sao lưu DB dev, deploy dev (25/11/2026)

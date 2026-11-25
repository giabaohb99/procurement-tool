---
title: "Tối ưu bốn bảng cụm Giá nguyên vật liệu sản xuất"
description: "Gộp nguồn sổ giá lịch sử mua + dòng ĐMH, nguồn bắt buộc cho báo giá, soát cột / chỉ mục / ngưỡng, nối tiếp chuẩn hóa định mức"
status: pending
priority: P2
effort: 17h
branch: erp-v2
tags: [thu-mua, gia-nvl, so-gia, bao-gia, migration]
created: 2026-11-25
---

# Tối ưu bảng cụm Giá NVL sản xuất (duoc-CR-784)
Trạng thái kế hoạch: **đang làm** (chưa viết mã, chờ chủ dự án chốt câu hỏi)

| Bản | Ngày | Người phụ trách | Trạng thái | CR liên quan |
|---|---|---|---|---|
| 1 | 25/11/2026 | planner | Nháp | duoc-CR-784 (kế hoạch gốc [261120](../261120-tac-dong-gia-bao-bi/plan.md)), bao-CR-789 |

Yêu cầu 25/11: tối ưu bốn bảng (giá, ngưỡng, cột), soát `source_type` / `source_id`, "LSMH và ĐMH hình như là 1", báo giá
phải có nguồn không NULL. Đã soát mã ở `origin/erp-v2 @f1a8b80c2` + nhánh định mức đang làm; số liệu local ở phase 02 / 03.

## Phạm vi: đúng bốn bảng + một bảng con đang làm
`tab_product_price_ledger` (sổ giá, 11.560 dòng local) · `tab_product_price_quote` (báo giá, 0) · `tab_product_price_limit`
(ngưỡng, 0, đang tắt ở giao diện) · `tab_packaging_bom` (định mức, 1.000) + `tab_packaging_bom_part` (đang làm, phase 01).
Đọc kèm, KHÔNG sửa cấu trúc: `tab_purchase_history`, `tab_po_item`, `tab_import_batch`, `tab_setting` (mốc `misa_price_cutoff`).

## Thời điểm: làm TRƯỚC khi CR-784 lên prod
Migration CR-784 (`pkgcost784` → `ppld784`, sắp có `bompart784`) chưa có trên `main`; prod chưa có dòng nào. Đổi cấu trúc bây giờ
chỉ phải chuyển dữ liệu dev + local. Báo bao-CR-789 (đang soát để lên prod): giữ đợt prod tới khi migration `opt784` vào `erp-v2`,
hoặc phát hành cả chuỗi một lần. Thứ tự gộp: nhánh định mức (`bompart784`) trước, rồi `opt784` (revises `bompart784`).

## Các phase
| # | Phase | Giờ | Phụ thuộc | Trạng thái |
|---|---|---|---|---|
| 01 | [Định mức tách thành phần (agent khác) + việc nối tiếp](phase-01-dinh-muc-bao-bi-thanh-phan-dang-lam.md) | 0,5 thêm | — | đang làm (worktree `bom784`) |
| 02 | [Sổ giá: gộp nguồn lịch sử + dòng ĐMH theo `po_item_id`](phase-02-so-gia-gop-nguon-lich-su-va-dong-dmh.md) | 8 | 01 đã gộp | C1 đã chốt (gộp) |
| 03 | [Báo giá: `source_type` / `source_id` NOT NULL + khóa duy nhất](phase-03-bao-gia-nguon-bat-buoc.md) | 4 | 02 (cùng migration, cùng `model.py`) | C2 đã chốt; chờ C3, C4 |
| 04 | [Cột, chỉ mục, bỏ ngưỡng, dọn nhỏ](phase-04-cot-chi-muc-nguong-don-dep.md) | 4,5 | 03 | C6, C7, C9 đã chốt; chờ C5 |
| 05 | [Tài liệu, bài kiểm, phát hành](phase-05-tai-lieu-kiem-phat-hanh.md) | 2 | 02–04, 06 | chưa |
| 06 | [Đổi tên `hh_code` / `hh_name` sang `fg_code` / `fg_name`](phase-06-doi-ten-hh-sang-fg.md) | 4 | 01 đã gộp; chung `opt784` | C8 đã chốt (đổi) |

Một người giữ 02 → 03 → 04 → 06 nối tiếp: cả ba sửa `product_price/model.py`, `core/packaging_price_codes.py` và CHUNG một tệp
migration `opt784` (luật "chỉ mục gom một migration"). Không phase nào chạy song song với phase 01 vì bộ dựng dữ liệu kiểm
`test/backend/so_gia_factory_cr784.py` đang bị nhánh định mức sửa.

## Luồng dữ liệu
```
TRƯỚC  tab_po_item --sync (có rồi thì cập nhật)--> sổ nguồn 2 (source_id = po_item.id)
       dòng hoàn thành --snapshot_line--> tab_purchase_history --chèn sổ nguồn 1 (source_id = ph.id) + XÓA dòng nguồn 2
       legacy Excel --> tab_purchase_history (po_item_id NULL) --> sổ nguồn 1 · Misa --> sổ nguồn 3 (source_id tự đánh số)
       báo giá: form / Excel --> tab_product_price_quote (không biết nguồn)
SAU    tab_po_item --sync--> sổ nguồn 2, line_stage = Đang mở; hoàn thành --> CÙNG dòng sổ, cập nhật số chốt, line_stage = Đã chốt
       (id giữ nguyên, không xóa / chèn lại; dòng Đã chốt sync không đụng nữa) · nguồn 1 chỉ còn legacy · nguồn 3 như cũ
       báo giá: form --> (1 Nhập tay, 0) · Excel --> (2 Nhập Excel, tab_import_batch.id)
```

## Câu hỏi cần chủ dự án chốt (A/B + đề xuất)
| # | Câu hỏi | A | B | Đề xuất |
|---|---|---|---|---|
| C1 | Gộp nguồn 1 + 2? | Gộp: dòng ĐMH là MỘT dòng sổ theo `po_item_id` suốt đời, thêm `line_stage`; nguồn 1 chỉ còn legacy | Giữ ba nguồn, chỉ ghi rõ tài liệu | **ĐÃ CHỐT 25/11: A, gộp** |
| C2 | Bộ nguồn báo giá | 1 Nhập tay, 2 Nhập Excel (số 3 để dành YCBG khi cần) | Thêm luôn 3 = phương án YCBG đã chọn + đường tự tạo báo giá | **ĐÃ CHỐT 25/11: A** (1 Nhập tay, 2 Nhập Excel, số 3 để dành YCBG) |
| C3 | `source_id` của báo giá nhập tay | 0 = không có chứng từ gốc (cùng nếp `doc_id = 0`) | Bắt đính kèm tệp báo giá NCC, `source_id` = id tệp | **A** |
| C4 | Nhập Excel đè giá báo giá đã có | Nguồn = lần ghi giá cuối (đổi sang đợt nhập) | Nguồn = nơi tạo, không đổi | **A** (biết giá đang dùng đến từ đâu; vết cũ ở nhật ký) |
| C5 | Khóa duy nhất báo giá `(mã, NCC, ngày hiệu lực)` | Thêm (form trùng báo 409, Excel đã dùng khóa này) | Không | **A** |
| C6 | Bảng ngưỡng (đang tắt) | Giữ nguyên, không đổi cấu trúc | Xóa bảng + mã tới khi cần | **ĐÃ CHỐT 25/11: xóa hẳn** (bảng, API, cảnh báo 6/7, cột Excel, trường công cụ AI, phần ẩn ở v1 + v2) |
| C7 | VAT dòng Misa (luôn 0 = không biết) | Để NULL = không biết, giao diện hiện trống | Giữ 0 | **ĐÃ CHỐT 25/11: A, để NULL** |
| C8 | Đổi tên `hh_code` / `hh_name` (định danh tiếng Việt) | Đổi thành `fg_code` / `fg_name` như `tab_po_item` | Giữ (đổi API cả v1, v2, AI, mẫu Excel) | **ĐÃ CHỐT 25/11: A, đổi sang tiếng Anh** (`fg_code` / `fg_name`) — [phase 06](phase-06-doi-ten-hh-sang-fg.md) |
| C9 | Bảng tóm tắt "giá gần nhất mỗi mã" | Không làm (đo 0,24 s trên dev) | Làm bảng tóm tắt theo pháp nhân x mã | **ĐÃ CHỐT 25/11: không làm** |

## Quay lui
Một revision `opt784`, `downgrade` đảo đủ: sổ giá tách lại nguồn 1 cho dòng Đã chốt (nối `tab_purchase_history.po_item_id`), bỏ
`line_stage`; báo giá bỏ hai cột + khóa; dựng lại bảng ngưỡng rỗng; đổi `fg_code` / `fg_name` về `hh_code` / `hh_name`. Sổ giá là dữ liệu dẫn xuất: sai gì thì `scripts/backfill_product_price_ledger.py`
dựng lại. Mã: revert commit của phase. Prod chưa có bảng nên không có quay lui trên prod.

## Tiêu chí xong
Bài kiểm cụm `*_cr784.py` xanh, số truy vấn cố định không tăng, `alembic upgrade` / `downgrade` / `upgrade` chạy sạch trên bản
sao DB dev, màn Lịch sử mua hàng cả v1 + v2 vẫn đánh dấu đúng "ĐMH đang mở", báo giá mới nào cũng có nguồn.

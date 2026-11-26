---
title: "Tối ưu bốn bảng cụm Giá nguyên vật liệu sản xuất"
description: "Gộp nguồn sổ giá lịch sử mua + dòng ĐMH, nguồn bắt buộc cho báo giá, soát cột / chỉ mục / ngưỡng, nối tiếp chuẩn hóa định mức"
status: in-progress
priority: P2
effort: 17h
branch: erp-v2
tags: [thu-mua, gia-nvl, so-gia, bao-gia, migration]
created: 2026-11-25
---

# Tối ưu bảng cụm Giá NVL sản xuất (duoc-CR-784)
Trạng thái kế hoạch: **xong trên dev, chờ phát hành prod** (26/11/2026) — phase 01–04, 06, 07 đã commit và lên dev 25/11/2026; phase 05 xong phần
tài liệu, HDSD, cẩm nang (chưa commit; seed HDSD + xuất bản cẩm nang + nạp lại chỉ mục chờ chạy trên dev), danh sách việc lên prod ở
[phase 05](phase-05-tai-lieu-kiem-phat-hanh.md) (mục *Phát hành prod*) chờ duyệt (chủ dự án duyệt triển khai 25/11/2026: "triển khai tối ưu từ từ theo plan")

| Bản | Ngày | Người phụ trách | Trạng thái | CR liên quan |
|---|---|---|---|---|
| 1 | 25/11/2026 | planner | Nháp | duoc-CR-784 (kế hoạch gốc [261120](../261120-tac-dong-gia-bao-bi/plan.md)), bao-CR-789 |
| 2 | 25/11/2026 | fullstack | Phase 02 xong; **đổi cách chia migration**: mỗi phase một migration viết tay riêng (không gộp một `opt784`) để phát hành từng phase | duoc-CR-784 |
| 3 | 26/11/2026 | tài liệu và kiểm thử | Mọi phase mã đã lên dev; phase 05 viết tài liệu, HDSD, cẩm nang, danh sách việc lên prod | duoc-CR-784, bao-CR-789 |

Yêu cầu 25/11: tối ưu bốn bảng (giá, ngưỡng, cột), soát `source_type` / `source_id`, "LSMH và ĐMH hình như là 1", báo giá
phải có nguồn không NULL. Đã soát mã ở `origin/erp-v2 @f1a8b80c2` + nhánh định mức đang làm; số liệu local ở phase 02 / 03.

## Phạm vi: đúng bốn bảng + một bảng con đang làm
`tab_product_price_ledger` (sổ giá, 11.560 dòng local) · `tab_product_price_quote` (báo giá, 0) · `tab_product_price_limit`
(ngưỡng, 0, đang tắt ở giao diện) · `tab_packaging_bom` (định mức, 1.000) + `tab_packaging_bom_part` (đang làm, phase 01).
Đọc kèm, KHÔNG sửa cấu trúc: `tab_purchase_history`, `tab_po_item`, `tab_import_batch`, `tab_setting` (mốc `misa_price_cutoff`).

## Thời điểm: làm TRƯỚC khi CR-784 lên prod
Migration CR-784 (`pkgcost784` → `misa784` → `amt784` → `ppld784` → `bompart784` → `srcmerge784` → `quotesrc784` → `cleanup784` → `fgname784` →
`bombatch784`, cập nhật 26/11/2026) chưa có trên `main`; prod chưa có dòng nào. Đổi cấu trúc bây giờ
chỉ phải chuyển dữ liệu dev + local. Báo bao-CR-789 (đang soát để lên prod): giữ đợt prod tới khi cả chuỗi vào `erp-v2`, hoặc phát hành cả
chuỗi một lần. **Cập nhật 25/11/2026:** kế hoạch ban đầu gộp phase 02–06 vào MỘT migration `opt784`; đổi thành **mỗi phase một migration
viết tay**, nối tiếp nhau (phase 02 = `srcmerge784`, `down_revision = bompart784`; các phase sau đặt id theo phase và trỏ vào phase trước).
Các tệp phase 03–06 còn ghi `opt784` — đọc là "migration của phase đó".

## Các phase
| # | Phase | Giờ | Phụ thuộc | Trạng thái |
|---|---|---|---|---|
| 01 | [Định mức tách thành phần + việc nối tiếp](phase-01-dinh-muc-bao-bi-thanh-phan-dang-lam.md) | 0,5 thêm | — | **xong, đã commit lên `erp-v2` + lên dev 25/11** (cùng đợt phase 02, sao lưu DB dev trước) — kết quả cũ / mới giống hệt, 796 bài kiểm qua — migration `bompart784` |
| 02 | [Sổ giá: gộp nguồn lịch sử + dòng ĐMH theo `po_item_id`](phase-02-so-gia-gop-nguon-lich-su-va-dong-dmh.md) | 8 | 01 đã gộp | **xong, đã commit + lên dev 25/11** (sao lưu DB dev trước, gộp 87 dòng, kiểm lệch 0) — migration `srcmerge784`; kết quả cũ / mới giống hệt trên bản sao dữ liệu, 1.005 bài kiểm backend + 1.806 bài vitest + tsc v1 / v2 qua |
| 03 | [Báo giá: `source_type` / `source_id` NOT NULL + khóa duy nhất](phase-03-bao-gia-nguon-bat-buoc.md) | 4 | 02 (cùng `model.py`; migration riêng nối sau `srcmerge784`) | **xong, đã commit + lên dev 25/11** (sao lưu DB dev trước, 0 trùng khóa) — migration `quotesrc784`; MySQL lên / xuống / lên lại sạch trên bản sao local, 19 bài kiểm mới + `cr784 or cr789` xanh, vitest procurement 1.813 bài + tsc v1 / v2 qua |
| 04 | [Cột, chỉ mục, bỏ ngưỡng, dọn nhỏ](phase-04-cot-chi-muc-nguong-don-dep.md) | 4,5 | 03 | **xong, đã commit + lên dev 25/11** (sao lưu DB dev trước, 0 dòng ngưỡng) — migration `cleanup784`; bỏ hẳn ngưỡng sàn / trần (C6), VAT Misa NULL (C7), `synced_at` một nguồn giờ, chốt chặn Misa HTML vs module 6; MySQL lên / xuống / lên lại sạch trên bản sao, kết quả cũ / mới giống hệt (trừ phần đã bỏ), 688 + 216 bài kiểm backend, vitest procurement 1.810 bài + tsc v1 / v2 qua |
| 05 | [Tài liệu, bài kiểm, phát hành](phase-05-tai-lieu-kiem-phat-hanh.md) | 2 | 02–04, 06, 07 | **tài liệu xong 26/11** (chưa commit); seed HDSD / cẩm nang / chỉ mục chờ chạy trên dev; phát hành prod chờ duyệt |
| 06 | [Đổi tên `hh_code` / `hh_name` sang `fg_code` / `fg_name`](phase-06-doi-ten-hh-sang-fg.md) | 4 | 01 đã gộp | **xong, đã commit + lên dev 25/11** — migration `fgname784`; tài liệu ở phase 05 |
| 07 | [Đánh dấu lô nhập trên định mức + xóa dữ liệu theo lô](phase-07-danh-dau-lo-nhap-va-xoa-theo-lo.md) | 3 | 03 | **xong, đã commit + lên dev 25/11** — migration `bombatch784` (đánh dấu 1.000 định mức lô 98 trên dev); HDSD ở phase 05 |

Một người giữ 02 → 03 → 04 → 06 nối tiếp: cả ba sửa `product_price/model.py`, `core/packaging_price_codes.py` (mỗi phase một
migration riêng nối tiếp, xem mục *Thời điểm*; luật "chỉ mục gom một migration" áp trong phạm vi từng phase). Không phase nào chạy song song với phase 01 vì bộ dựng dữ liệu kiểm
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
| C3 | `source_id` của báo giá nhập tay | 0 = không có chứng từ gốc (cùng nếp `doc_id = 0`) | Bắt đính kèm tệp báo giá NCC, `source_id` = id tệp | **ĐÃ CHỐT 25/11: A** (`source_id` = 0 cho nhập tay) — làm ở phase 03 |
| C4 | Nhập Excel đè giá báo giá đã có | Nguồn = lần ghi giá cuối (đổi sang đợt nhập) | Nguồn = nơi tạo, không đổi | **ĐÃ CHỐT 25/11: A** (biết giá đang dùng đến từ đâu; vết cũ ở nhật ký) — làm ở phase 03 |
| C5 | Khóa duy nhất báo giá `(mã, NCC, ngày hiệu lực)` | Thêm (form trùng báo 409, Excel đã dùng khóa này) | Không | **ĐÃ CHỐT 25/11: A** (thêm khóa duy nhất) — làm ở phase 03 |
| C6 | Bảng ngưỡng (đang tắt) | Giữ nguyên, không đổi cấu trúc | Xóa bảng + mã tới khi cần | **ĐÃ CHỐT 25/11: xóa hẳn** (bảng, API, cảnh báo 6/7, cột Excel, trường công cụ AI, phần ẩn ở v1 + v2) |
| C7 | VAT dòng Misa (luôn 0 = không biết) | Để NULL = không biết, giao diện hiện trống | Giữ 0 | **ĐÃ CHỐT 25/11: A, để NULL** |
| C8 | Đổi tên `hh_code` / `hh_name` (định danh tiếng Việt) | Đổi thành `fg_code` / `fg_name` như `tab_po_item` | Giữ (đổi API cả v1, v2, AI, mẫu Excel) | **ĐÃ CHỐT 25/11: A, đổi sang tiếng Anh** (`fg_code` / `fg_name`) — [phase 06](phase-06-doi-ten-hh-sang-fg.md) |
| C9 | Bảng tóm tắt "giá gần nhất mỗi mã" | Không làm (đo 0,24 s trên dev) | Làm bảng tóm tắt theo pháp nhân x mã | **ĐÃ CHỐT 25/11: không làm** |

## Quay lui
Mỗi phase một revision, `downgrade` đảo đủ: phase 02 (`srcmerge784`) tách lại nguồn 1 cho dòng Đã chốt (nối `tab_purchase_history.po_item_id`),
bỏ `line_stage`; phase 03 báo giá bỏ hai cột + khóa; phase 04 dựng lại bảng ngưỡng rỗng; phase 06 đổi `fg_code` / `fg_name` về `hh_code` / `hh_name`. Sổ giá là dữ liệu dẫn xuất: sai gì thì `scripts/backfill_product_price_ledger.py`
dựng lại. Mã: revert commit của phase. Prod chưa có bảng nên không có quay lui trên prod.

## Tiêu chí xong
Bài kiểm cụm `*_cr784.py` xanh, số truy vấn cố định không tăng, `alembic upgrade` / `downgrade` / `upgrade` chạy sạch trên bản
sao DB dev, màn Lịch sử mua hàng cả v1 + v2 vẫn đánh dấu đúng "ĐMH đang mở", báo giá mới nào cũng có nguồn.

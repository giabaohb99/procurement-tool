---
title: "Tác động giá bao bì — sổ giá, báo giá, định mức bao bì, mô phỏng giá"
description: "Sổ giá gom lịch sử mua + dòng ĐMH, bảng báo giá, ngưỡng giá, định mức bao bì theo mã HH; màn Tác động giá và Bảng giá VTBB"
status: pending
priority: P2
effort: 33h
branch: erp-v2
tags: [thu-mua, gia, bao-bi, bao-cao, import-excel]
created: 2026-11-20
---

# Tác động giá bao bì (duoc-CR-784)

> **Cập nhật 26/11/2026 — đọc trước khi dùng kế hoạch này.** Nhiều quyết định dưới đây đã được thay bằng
> [kế hoạch tối ưu 261125](../261125-toi-uu-bang-gia-nvl-duoc-cr-784/plan.md) (đã lên dev 25/11/2026): (1) **ngưỡng sàn / trần bỏ hẳn**
> (quyết định 4 bên dưới hết hiệu lực: bảng `tab_product_price_limit`, đường `/api/product-price-limits`, cảnh báo 6 / 7, cột Excel,
> trường công cụ AI đều đã xóa — migration `cleanup784`); (2) luật sổ giá "nguồn 1 chỉ chèn, dòng vào lịch sử thì xóa dòng nguồn 2"
> (quyết định 1) thay bằng **một dòng sổ mỗi dòng ĐMH** có `line_stage` Đang mở / Đã chốt (`srcmerge784`); (3) định danh `hh_code` /
> `hh_name` / `hh_codes` đổi thành **`fg_code` / `fg_name` / `fg_codes`** (`fgname784`) — chữ `hh_*` trong các phase của kế hoạch này là
> tên cũ; (4) định mức tách đầu phiếu + bảng thành phần (`bompart784`); (5) báo giá có nguồn bắt buộc và khóa duy nhất (`quotesrc784`);
> (6) nhập Excel cụm này xóa được theo lô (`bombatch784`). Hiện trạng: [chức năng 21](../../chuc-nang/21-tac-dong-gia-bao-bi.md),
> [mô hình dữ liệu](../../tai-lieu-ky-thuat/mo-hinh-du-lieu-gia-nvl-san-xuat.md).

Trạng thái kế hoạch: **xong trên dev** (mã viết và lên dev 20–25/11/2026; phần tối ưu và phát hành prod theo kế hoạch 261125; dòng cũ ghi "đang làm, chưa viết mã" đã hết hạn)

| Bản | Ngày | Người phụ trách | Trạng thái | CR liên quan |
|---|---|---|---|---|
| 1 | 20/11/2026 | planner | Nháp | duoc-CR-784 (nền: D-025, bao-CR-720, duoc-CR-562) |

Nguồn nghiệp vụ: bản mẫu `Bao cao gia NVL san xuat - 11.2026.html` (hàm `build`, `productRow`, `renderImpact`, `renderPrices`,
`importExcel`). Mô hình sản phẩm: [`mo-hinh-du-lieu-san-pham.md`](../../../mat-hang/tai-lieu-ky-thuat/mo-hinh-du-lieu-san-pham.md) §2, §11.

## Quyết định đã chốt (người chủ chốt)
1. Bảng **sổ giá** `tab_product_price_ledger`: nguồn 1 = lịch sử mua (chỉ chèn), nguồn 2 = dòng ĐMH (có rồi thì cập nhật).
   Dòng vào lịch sử mua thì xóa dòng nguồn 2 của nó. Báo giá **không** vào sổ (lý do ở phase 01).
2. Bảng **báo giá** `tab_product_price_quote` + màn "+ Báo giá mới".
3. Bảng **định mức bao bì** `tab_packaging_bom` theo mã HH, nạp từ `DATA_CHAI.xlsx` qua `import_tool`, có màn sửa.
4. Min/max = cả hai: tính từ sổ giá (lọc ngày) + **ngưỡng sàn/trần** đặt tay ở bảng riêng `tab_product_price_limit`.
5. API nhanh: số truy vấn cố định, bài kiểm đếm truy vấn, index gom một migration.
6. Màn ở phân hệ **Thu mua** (frontend-v2 `procurement`), khóa quyền MỚI `packaging_cost`, xuất Excel ở máy chủ.

## Công thức (giữ đúng bản mẫu)
- CP bao bì/chai = chai + nắp + nhãn + (nhãn thùng + thùng) / quy cách thùng; CP/thùng = CP/chai x quy cách.
- Giá cũ / mới một mã: có báo giá hiệu lực thì mới = báo giá, cũ = lần mua có giá gần nhất; không có thì mới = lần mua có
  giá gần nhất, cũ = lần trước đó; chỉ một lần thì cũ = mới. Bỏ dòng đơn giá 0. Thiếu giá chai thì CP = rỗng.

## Các phase

| # | Phase | Giờ | Phụ thuộc | Trạng thái |
|---|---|---|---|---|
| 01 | [BE mô hình dữ liệu, migration, khóa quyền, bộ mã](phase-01-be-mo-hinh-du-lieu-migration-quyen.md) | 3 | — | xong BE (local 20/11) |
| 02 | [BE đồng bộ sổ giá + script nạp lại](phase-02-be-so-gia-dong-bo-backfill.md) | 6 | 01 | xong BE (local 20/11) |
| 03 | [BE báo giá, ngưỡng, định mức + nhập Excel](phase-03-be-bao-gia-nguong-dinh-muc-nhap-excel.md) | 5 | 01, 02 | xong BE (local 20/11) |
| 04 | [BE API tác động giá, bảng giá, xuất Excel](phase-04-be-api-tac-dong-bang-gia-xuat-excel.md) | 6 | 01, 03 | xong BE (local 20/11) |
| 05 | [FE màn Giá bao bì (frontend-v2)](phase-05-fe-man-gia-bao-bi.md) | 10 | 04 (hợp đồng chốt ở 04) | xong (local 20/11) |
| 06 | [Tài liệu, HDSD, RAG, sổ](phase-06-tai-lieu-hdsd-rag.md) | 3 | 05 | chưa |
| 07 | [Đợt sau: lịch sử theo mã/SP, 5 lần gần nhất, tổng hợp](phase-07-dot-sau-lich-su-5-lan-tong-hop.md) | (8, không tính) | 06 | tab Giá mua gần nhất (3/5/10 lần, nhóm cột) đã làm 20/11 và tab Lịch sử mua hàng (theo mã VTBB / theo SP, biểu đồ, Excel) đã làm 21/11 theo yêu cầu người chủ; tab Tổng hợp còn hoãn |

Backend 01 → 02 → 03 → 04 chạy **nối tiếp, một người giữ** (02 và 03 cùng sửa `import_tool/service.py`; 03 và 04 cùng
`main.py`). Phase 05 được dựng khung từ lúc 04 chốt hợp đồng, nối API thật sau khi 04 xong.

## Luồng dữ liệu
```
tab_po_item (ĐMH đã duyệt, dòng chưa hủy) --sync_po_price_ledger--> ledger nguồn 2 (upsert)
tab_purchase_history (system|legacy) --snapshot_line / sync_history_ledger--> ledger nguồn 1 (chỉ chèn; xóa nguồn 2 cùng dòng)
ledger + tab_product_price_quote + tab_product_price_limit --price_state_service--> giá cũ/mới/min/max/ngưỡng theo mã
tab_packaging_bom + giá theo mã + giá giả định --packaging_cost_service--> CP/chai, CP/thùng, KPI --> màn + Excel
```

## Ma trận kiểm
| Tầng | Kiểm gì | Ở đâu |
|---|---|---|
| Đơn vị (pytest) | luật cũ/mới, công thức CP, đọc Excel 2 khuôn, schema `max_length` | phase 03, 04 |
| Tích hợp (pytest, SQLite) | mọi mốc sửa ĐMH → sổ giá; nạp lại legacy; đếm truy vấn <= 7; 403/422 | phase 02, 04 |
| Bài canh | cụm 6 bài `them-entity-moi`; bài tĩnh `_sync_pr` ↔ `sync_po_price_ledger` | phase 01, 02 |
| Giao diện (vitest) | menu theo quyền, ô chọn nhiều, giá giả định vi-VN, bấm đúp | phase 05 |
| Đầu-cuối (tay, dev) | duyệt ĐMH → Bảng giá đổi; nhập DATA_CHAI → Tác động khớp bản mẫu với cùng dữ liệu | phase 06 |

## Quay lui
Bốn bảng mới, không sửa cột bảng cũ. Sổ giá là dữ liệu dẫn xuất, dựng lại được bằng script. Quay lui = revert commit hook
+ `alembic downgrade` một bước (xóa 4 bảng). Chưa tick quyền `packaging_cost` trên prod thì không ai thấy màn.

## Câu hỏi
Đã chốt 20/11: Q1 (chưa nạp MISA), Q2 (báo giá tương lai tính ngay), Q4 (khóa `packaging_cost`, theo pháp nhân),
Q8 (ĐMH từ đã duyệt). Còn treo Q3 (ĐVT), Q5 (ngày legacy tương lai), Q6 (tệp DATA_CHAI thật), Q7 (phiên bản định mức) —
cuối [phase-01](phase-01-be-mo-hinh-du-lieu-migration-quyen.md).

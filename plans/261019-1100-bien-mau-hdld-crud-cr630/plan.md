---
title: "duoc-CR-630 — Quản lý «Danh sách biến» của mẫu HĐLĐ (CRUD + biến tùy chỉnh nhập tay)"
description: "Biến mẫu HĐLĐ chuyển từ mã cứng sang bảng tab_labor_contract_variable: 50 biến hệ thống sửa nhãn/ẩn, biến tùy chỉnh nhập tay theo từng hợp đồng."
status: completed
priority: P2
effort: 17h
branch: erp-v2
tags: [hr, labor-contract, docx, backend, frontend-v2, migration]
created: 2026-10-19
---

# duoc-CR-630 — Danh sách biến mẫu HĐLĐ

Change-log: dòng `duoc-CR-630-bien-mau-hdld-crud` (đã điền). **PO chốt 19/10 ghi đè plan:** biến TOÀN HỆ THỐNG; chỉ phạm vi «tất cả pháp nhân» mới ghi danh mục (kể cả nhãn biến hệ thống); mặc định SAO vào HĐ lúc lập (không áp lúc sinh); «Bắt buộc» chặn cả Sinh tệp lẫn chuyển «Đã ký»; giá trị biến ngừng dùng hiện chỉ-đọc ở hộp Sửa HĐ; còn lại theo đề xuất của plan (Q3 write, Q6 số ≥0 ≤2 lẻ, Q7 `_bang_chu` tự động, Q9 100/20 000).

## Luồng dữ liệu

```
HR (labor_contract_template.write) ──► /api/labor-contract-variables ──► tab_labor_contract_variable
   biến HỆ THỐNG (50, seed insert-only): chỉ nhãn · mô tả · ẩn khỏi danh sách; GIÁ TRỊ vẫn từ code (context_builder)
   biến TÙY CHỈNH: mã · nhãn · kiểu · ví dụ · mặc định · bắt buộc khi sinh · thứ tự · đang dùng

Tải mẫu / Thay tệp / Soạn web ──► variable_registry.allowed_keys() = hệ thống(code) ∪ tùy chỉnh ĐANG DÙNG ∪ «_bang_chu» của biến tiền
   (+ biến ngừng dùng ĐÃ có sẵn trong chính mẫu đó) ──► docx_engine.inspect_template(data, allowed) ──► tpl.placeholders (JSON, đã có)

Lập/Sửa HĐ (Nháp) ──► custom_values {mã: chuỗi chuẩn} ──► tab_labor_contract.custom_values (JSON, gộp theo khóa)
Sinh tệp ──► ctx = build_context(hệ thống) ∪ custom_context(giá trị HĐ → mặc định → "", định dạng theo kiểu)
   ├─ mẫu dùng biến đã bị xóa ⇒ 422 · biến bắt buộc (đang dùng, có trong mẫu) rỗng ⇒ 422 nêu nhãn
   └─ docx_engine.render(...)
Xóa biến ──► «đang dùng» = có trong tpl.placeholders của BẤT KỲ mẫu nào HOẶC có HĐ (kể cả xóa mềm) giữ giá trị ⇒ 409, chỉ «Ngừng dùng»
```

## Phases

| # | Phase | Effort | Phụ thuộc | Status |
|---|---|---|---|---|
| 01 | [Nền: mã số, bảng, migration `lbvar01`, seed, luật thuần, registry](phase-01-nen-du-lieu-bang-bien-migration.md) | 3h | CR-629 commit (head `lbrct02`) | done |
| 02 | [API quản lý biến](phase-02-api-quan-ly-bien.md) | 3h | 01 | done |
| 03 | [Tích hợp mẫu + giá trị theo HĐ + sinh tệp + che nhật ký](phase-03-tich-hop-mau-gia-tri-hop-dong-sinh-tep.md) | 3.5h | 01 | done |
| 04 | [FE: màn quản lý biến](phase-04-fe-man-quan-ly-bien.md) | 4h | 02 (hợp đồng API) | done |
| 05 | [FE: ô nhập biến trong hộp Lập/Sửa HĐ](phase-05-fe-o-nhap-bien-trong-hop-dong.md) | 2h | 03, 04 | done |
| 06 | [Hồi quy, tài liệu, triển khai](phase-06-hoi-quy-tai-lieu-trien-khai.md) | 1.5h | 01–05 | done |

**02 ∥ 03** (tệp tách bạch, hàm dùng chung nằm ở `variable_registry.py` của 01). **04 ∥ 03** (FE chỉ cần hợp đồng API của 02).

## Quyết định khóa
- Bảng mới `tab_labor_contract_variable`, **toàn hệ thống** (không `company_id`) — xem câu hỏi mở Q1.
- Giá trị theo HĐ: **cột JSON `tab_labor_contract.custom_values`** (không bảng con) — lý do ở phase 01.
- Biến hệ thống: **hợp lệ theo CODE** (`placeholder_catalog.KNOWN_KEYS`), DB chỉ giữ nhãn/mô tả/ẩn ⇒ thiếu dòng DB không bao giờ làm mẫu bị từ chối.
- «Đang dùng trong mẫu» đọc cột `placeholders` sẵn có của mẫu (ghi lúc tải/thay/soạn) — không quét .docx lúc xóa.
- Biến tiền tự có bạn đồng hành `{{ <mã>_bang_chu }}` (đọc số thành chữ), không phải tạo dòng riêng.
- Quyền: tái dùng `labor_contract_template` (read xem · write tạo/sửa · delete xóa); KHÔNG entity mới ⇒ ENTITIES/SCOPE_FIELDS không đổi.
- Migration `lbvar01` (down=`lbrct02`); **phase 07 CR-629b (`lbrct03`) phải đổi `down_revision="lbvar01"`** (đã ghi chú vào tệp phase 07).

## Rollback
Mỗi phase 1 commit. FE (05→04) revert thuần. BE: revert 03 → 02 → 01, rồi `alembic downgrade lbrct02` (drop cột `custom_values` + bảng biến). ⚠️ Downgrade MẤT giá trị biến tùy chỉnh đã nhập ⇒ dump `tab_labor_contract(id, custom_values)` trước khi xuống. Tệp .docx đã sinh không bị ảnh hưởng. Nếu `lbrct03` đã lên thì phải xuống nó trước.

## Câu hỏi mở — cuối phase 06.

---
title: "duoc-CR-629 — Lập HĐLĐ sinh bản lưu trữ bên Văn bản (chỉ Nhân sự xem)"
description: "Bấm «Lập hợp đồng» là sinh 1 văn bản loại HDLD; tệp .docx + bản ký chép sang; trạng thái đồng bộ; quyền đọc ủy thác cho labor_contract.read."
status: pending
priority: P2
effort: 15.5h
branch: erp-v2
tags: [hr, labor-contract, document, permissions, search, backend, frontend-v2]
created: 2026-10-19
---

# duoc-CR-629 — HĐLĐ → bản lưu trữ ở phân hệ Văn bản

Change-log đã đặt chỗ: `duoc-CR-629-hdld-sinh-van-ban-luu-tru` (`doc/tai-lieu-ky-thuat/change-log.md:44`).
Nền HĐLĐ: `frontend-v2/plans/261005-1537-hop-dong-lao-dong-mau-theo-phap-nhan/plan.md`.

## Luồng dữ liệu

```
HR bấm Lập / Sửa / Sinh tệp / Tải bản ký / Chuyển trạng thái / Xóa (labor_contract controller)
   │ service cũ commit xong (KHÔNG đổi luật HĐLĐ)
   ▼
archive_sync(lc)  ── best-effort, lỗi chỉ log; khóa dòng HĐ FOR UPDATE
   ├─ chưa có văn bản → create_document(loại HDLD, content_mode=2, company/dept snapshot) → lc.document_id, commit
   ├─ đồng bộ tiêu đề · ngày · trạng thái (bảng ánh xạ ở phase 03)
   └─ gương tệp: phiên bản hiện hành = {bản sao generated_file, bản sao signed_file} (so sha256)
          tệp HĐ gốc ─ CHÉP byte ─► tab_file MỚI + FileLink(document_version)   (không dùng chung file_id)

Đọc văn bản (danh sách · chi tiết · tệp · tìm · thư mục · tổng quan · báo cáo · trợ lý AI)
   └─ access_service.visible_condition / can()
        văn bản có dòng tab_labor_contract.document_id trỏ tới  ⇒  CHỈ labor_contract.read trong phạm vi
        mọi nguồn khác (phạm vi document, chia sẻ, sổ, duyệt, phạm vi áp dụng, clone) KHÔNG tính
        ghi/xóa/sao chép/clone/trích/ký ⇒ chặn (bản lưu trữ chỉ đọc, quản lý từ Nhân sự)
   └─ search_index_service.reindex: loại HDLD / văn bản HĐLĐ ⇒ KHÔNG vào chỉ mục toàn văn
```

## Phases

| # | Phase | Effort | Phụ thuộc | Status |
|---|---|---|---|---|
| 01 | [Nền: cột, migration, loại văn bản HDLD, seed](phase-01-nen-cot-migration-loai-van-ban.md) | 1.5h | — | pending |
| 02 | [Luật đọc bản lưu trữ ở phân hệ Văn bản](phase-02-luat-doc-ban-luu-tru-van-ban.md) | 3h | 01 | pending |
| 03 | [Cầu nối đồng bộ HĐLĐ → Văn bản + script bù](phase-03-cau-noi-dong-bo-hdld-van-ban.md) | 4h | 01 | pending |
| 04 | [FE: nút «Văn bản lưu trữ»](phase-04-fe-nut-van-ban-luu-tru.md) | 1.5h | 03 (hợp đồng API) | pending |
| 05 | [Tài liệu, triển khai, bù dữ liệu](phase-05-tai-lieu-trien-khai-bu-du-lieu.md) | 1.5h | 02, 03, 04, 06 | pending |
| 06 | **CR-628b** [Bước A: gộp giao diện mẫu HĐLĐ vào «Thư viện văn bản mẫu»](phase-06-cr629b-gop-giao-dien-mau-hdld-vao-thu-vien.md) | 4h | CR-610 đã commit | pending |
| 07 | **CR-628b** [Bước B: gộp dữ liệu mẫu — đề xuất HOÃN](phase-07-cr629b-gop-du-lieu-mau-de-xuat-hoan.md) | (10–12h) | 06 + đại ca duyệt | deferred |

**02 ∥ 03** chạy song song được: tệp không chồng nhau (02 = `document/*`, 03 = `labor_contract/*`).
Hợp đồng giữa hai bên chỉ là: cột `tab_labor_contract.document_id` + hằng `LABOR_CONTRACT_DOC_TYPE` (phase 01).
**06** chỉ đụng frontend-v2 (route/menu/trang Thiết lập/catalog HĐLĐ), không chung tệp với 04 ⇒ chạy song song với 01–04.

## CR-628b — gộp mẫu HĐLĐ vào Thư viện văn bản mẫu (thêm 19/10/2026)
`tab_document_template` chỉ có mẫu HTML theo loại văn bản. Nó không có tệp, biến, pháp nhân hay phạm vi, và mọi vai trò đều đọc được.
⇒ **Bước A (06):** gộp phần GIAO DIỆN thôi. Màn HĐLĐ sang `/document/settings?tab=templates&kind=labor-contract`, vẫn gọi `/api/labor-contract-templates`, quyền vẫn là `labor_contract_template`, backend và dữ liệu giữ nguyên.
**Bước B (07):** gộp bảng. Tách riêng, khuyến nghị KHÔNG làm vì có nguy cơ rò mẫu và gãy `tab_labor_contract.template_id` mà người dùng không được thêm gì.

## Quyết định khóa

- Nhận diện bản lưu trữ bằng **liên kết** (`tab_labor_contract.document_id`), KHÔNG bằng mã loại — đổi mã/tên loại trên UI không mở khóa. Mã loại chỉ dùng để tìm loại khi tạo + loại khỏi chỉ mục.
- Loại `HDLD` seed **insert-only** trong `ALL_DOC_TYPES` (`seed_document_phase1` chạy ở cả `seed.py` lẫn `seed_prod.py`), `is_personal=True` làm lưới an toàn thứ hai. Loại thiếu / tắt ⇒ cầu nối bỏ qua im lặng (khuôn GNP).
- KHÔNG đặt `owner_employee_id` = người lao động; không ghi `metadata`; tiêu đề/tóm tắt KHÔNG chứa lương.
- Tệp: CHÉP byte sang `tab_file` mới (vì `delete_stored_file` không soi `FileLink`). Văn bản là **gương** của HĐ: sinh lại / thay bản ký ⇒ bản sao cũ bị gỡ.
- Không thư mục riêng «Nhân sự/HĐLĐ» (thư mục theo pháp nhân, `default_folder_id` chỉ khớp 1 pháp nhân) — rơi về gốc pháp nhân; admin tự đặt `default_folder_id` nếu muốn.
- Không backfill trong migration — script chạy tay `scripts/backfill_hdld_van_ban_luu_tru.py` (idempotent, `--dry-run`).
- Không đổi luật tải bản ký (PDF/JPG/PNG, Nháp/Đã ký, 50MB) — xem câu hỏi mở.

## Rollback

CR-628b bước A: revert 1 commit FE, không có dữ liệu. Phần còn lại: mỗi phase 1 commit. Revert FE (04) → revert BE (03, 02) → `alembic downgrade` về head trước `lbrct02` (drop cột + index).
Văn bản đã sinh còn lại: loại `HDLD` `is_personal` ⇒ chỉ người tạo + vai trò `document` phạm vi *tất cả* thấy; muốn sạch hẳn thì chạy `--soft-delete-all` của script trước khi downgrade.

## Câu hỏi mở — xem cuối phase 05.

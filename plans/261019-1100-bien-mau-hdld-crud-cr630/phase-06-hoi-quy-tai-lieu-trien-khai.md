# Phase 06 — Hồi quy, tài liệu, triển khai

**Ưu tiên:** P2 · **Status:** pending · **Effort:** 1.5h · **Phụ thuộc:** 01–05

## Hồi quy (chỉ tệp liên quan — máy giới hạn tài nguyên, KHÔNG quét cả `test/backend`)
```bash
docker compose exec -T api python -m pytest -q test/backend/test_hdld_bien_mau_nen_cr630.py test/backend/test_hdld_bien_mau_api_cr630.py test/backend/test_hdld_bien_mau_sinh_tep_cr630.py
docker compose exec -T api python -m pytest -q test/backend/test_hdld_bo_may_docx.py test/backend/test_hdld_sua_loi_review.py test/backend/test_hdld_sinh_tai_tep.py test/backend/test_hdld_hop_dong_api.py test/backend/test_hdld_mau_hop_dong_api.py test/backend/test_hdld_soan_mau_tren_web.py
docker compose exec -T api python -m pytest -q test/backend/test_hdld_nen_du_lieu.py test/backend/test_hdld_khoa_dong_xoa_mem_cr627.py test/backend/test_hdld_van_ban_luu_tru_dong_bo_cr629.py test/backend/test_pham_vi_khai_du_b07.py test/backend/test_status_catalog_b01.py test/backend/test_dong_bo_giao_dien_v2.py test/backend/test_canh_do_dai_o_chu_cr538.py
docker compose exec -T erp npm run typecheck && docker compose exec -T erp npm run lint
docker compose exec -T erp npx vitest run src/modules/hr src/modules/document src/app/router
```
`test_pham_vi_khai_du_b07` phải giữ nguyên số entity (không thêm entity).

## Ma trận kiểm thử tổng
| Lớp | Phủ |
|---|---|
| Đơn vị (pytest thuần) | luật mã, chuẩn hóa/định dạng 5 kiểu, seed insert-only, registry, câu SQL json_extract (SQLite chạy + MySQL biên dịch) |
| Tích hợp (pytest API, SQLite) | CRUD + quyền + chốt xóa/đổi mã; tải/thay/soạn mẫu theo danh mục động; lưu giá trị HĐ; sinh tệp; che nhật ký |
| FE (vitest) | trang biến, hộp form, ô theo kiểu, ô trong hộp HĐ, gác route |
| E2E tay (local, Chrome) | kịch bản dưới |

**Kịch bản tay:** (1) thêm biến `so_ngay_phep` (số, bắt buộc), `ngay_hieu_luc_phu_luc` (ngày), `muc_thuong` (tiền); (2) soạn web mẫu chèn 3 biến + `muc_thuong_bang_chu`; (3) lập HĐ bỏ trống `so_ngay_phep` → Sinh tệp báo thiếu; (4) nhập đủ → Sinh tệp, mở .docx kiểm định dạng; (5) ngừng dùng `muc_thuong` → ô biến mất khỏi hộp HĐ, mẫu cũ vẫn sinh; tải mẫu MỚI dùng nó → 422; (6) xóa `so_ngay_phep` → 409 nêu mẫu; (7) sửa nhãn `ho_ten` → khung chèn biến hiện nhãn mới; (8) xem Nhật ký hệ thống: không thấy giá trị biến.

## Tài liệu (agent ghi khi làm phase này)
- `doc/tai-lieu-ky-thuat/change-log.md`: dòng **`duoc-CR-630-bien-mau-hdld-crud`** — ⚠️ KHÔNG sửa lúc lập plan (agent khác đang sửa); đặt chỗ khi nhận việc, ghi đủ khi xong.
- `doc/tai-lieu-ky-thuat/nhat-ky-task.md`: mục mã duy nhất (câu tiếng Việt trọn, `Mã nguồn:`/`Commit:` dòng cuối).
- `frontend-v2/plans/261005-1537-hop-dong-lao-dong-mau-theo-phap-nhan/phase-02-bo-may-docx-danh-muc-bien.md`: 1 dòng «đã thay bởi CR-630».
- Tài liệu chức năng HĐLĐ (nơi mô tả Mẫu HĐ — tìm `grep -rl "Mẫu hợp đồng" doc/erp/hrm doc/tai-lieu-chuc-nang`): mục «Danh sách biến» — 2 loại biến, kiểu, mặc định, bắt buộc khi sinh, ngừng dùng vs xóa, `_bang_chu`.
- Hướng dẫn sử dụng HR (nếu có trang Mẫu HĐ trong help-center/v2): cách thêm biến + chép `{{ mã }}`.
- `docstring` `placeholder_catalog.py`: ghi rõ nay là nguồn biến HỆ THỐNG (giá trị + nhãn mặc định để seed); nhãn hiển thị ở DB.
- Cân nhắc thêm 5–8 dòng vào `.claude/rules/` (khu `labor_contract/` chưa có tệp luật): danh mục động, JSON `custom_values` gán dict mới, json_extract thay `col[key]`, `keep` khi thay tệp.

## Triển khai
1. Phase 07 CR-629b chưa lên ⇒ thứ tự migration `lbrct02 → lbvar01 (→ lbrct03)`; `alembic heads` = 1.
2. Prod: `start.prod.sh` chạy `alembic upgrade head` rồi `seed_prod` ⇒ 50 dòng hệ thống tự chèn. Không cần `SEED_FORCE_SYNC` (không đổi quyền).
3. Vai trò cũ: không đổi (tái dùng `labor_contract_template`).
4. Sau deploy: mở trang biến (thấy 50 dòng hệ thống), tải lại 1 mẫu cũ (vẫn nhận), sinh lại 1 HĐ nháp (y như trước).

## Rollback
Revert FE (05, 04) → revert BE (03, 02, 01) → `alembic downgrade lbrct02`. Trước downgrade: `SELECT id, custom_values FROM tab_labor_contract WHERE custom_values IS NOT NULL` lưu ra tệp (downgrade mất cột). Mẫu đã dùng biến tùy chỉnh sẽ bị từ chối khi tải lại / sinh lỗi 422 sau khi revert ⇒ phải ngừng dùng các mẫu đó trước.

## Tiêu chí xong (đo được)
- 3 tệp test mới + toàn bộ hồi quy trên xanh; 3 cổng FE xanh.
- 8 bước kịch bản tay đạt.
- Mẫu + HĐ hiện có trên bản sao dữ liệu: tải lại / sinh lại không đổi kết quả (so văn bản .docx trước/sau).

## Câu hỏi mở
1. **Q1 — Toàn hệ thống hay theo pháp nhân?** Đề xuất TOÀN HỆ THỐNG (không `company_id`). Gắn pháp nhân không rẻ: `apply_scope` theo `company_id` sẽ giấu dòng toàn hệ thống (`0`) với HR phạm vi pháp nhân, kiểm mẫu phải lọc theo pháp nhân của mẫu, ô trong hộp HĐ lọc theo pháp nhân HĐ. Chủ dự án xác nhận?
2. **Q2 — Ai được sửa danh mục toàn hệ thống?** HR chỉ phạm vi pháp nhân A sửa nhãn/mặc định/ngừng dùng ảnh hưởng mẫu của pháp nhân B. Chấp nhận (audit đủ), hay chỉ cho người có phạm vi `all` của `labor_contract_template` ghi?
3. **Q3 — Tạo biến dùng `write` (PO chốt) thay vì `create`** — vai trò có `create` mà không `write` sẽ không thêm được biến. Giữ?
4. **Q4 — Giá trị mặc định áp lúc SINH, không điền sẵn vào HĐ** ⇒ đổi mặc định sẽ đổi kết quả sinh lại của HĐ nháp cũ (HĐ đã ký không sinh lại được nên an toàn). Đồng ý?
5. **Q5 — «Bắt buộc» chỉ chặn ở bước Sinh tệp, không chặn Lưu nháp** — đồng ý?
6. **Q6 — Kiểu «số»:** không âm, tối đa 2 chữ số lẻ (hệ số lương 2,34). Cần số âm / nhiều số lẻ hơn?
7. **Q7 — `_bang_chu` tự động cho mọi biến tiền** (không tùy chọn bật/tắt) — đồng ý?
8. **Q8 — Giá trị của biến đã NGỪNG DÙNG** không hiện ở hộp Sửa HĐ (vẫn lưu, vẫn in vào mẫu cũ). Cần hiện chỉ-đọc không?
9. **Q9 — Trần 100 biến tùy chỉnh / 20 000 ký tự giá trị mỗi HĐ** — đủ?

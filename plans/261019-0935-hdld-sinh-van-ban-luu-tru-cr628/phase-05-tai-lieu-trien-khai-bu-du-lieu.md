# Phase 05 — Tài liệu, triển khai, bù dữ liệu

**Ưu tiên:** P2 · **Trạng thái:** pending · **Effort:** 1.5h · **Phụ thuộc:** 02, 03, 04
**Sở hữu tệp:** `doc/**`, `.claude/rules/document-folders-search.md`, `.claude/rules/hr-employee-profile.md`

## Tài liệu cần sửa
- `doc/tai-lieu-ky-thuat/change-log.md:44` — dòng `duoc-CR-628-...` (đã đặt chỗ): điền kết quả, trạng thái «Xong».
- `doc/tai-lieu-ky-thuat/nhat-ky-task.md` — mục mới mã duy nhất (`duoc-CR-628`, lượt sau thêm hậu tố); câu tiếng Việt trọn vẹn, tên tệp/commit dồn xuống dòng `Mã nguồn:` / `Commit:` (luật 17/09/2026).
- `doc/tai-lieu-chuc-nang/14-van-thu-van-ban.md` — §8 «Quyền truy cập theo từng văn bản»: thêm mục «Bản lưu trữ HĐLĐ» (ai xem, chỉ đọc, không chia sẻ/sao chép/clone/trích/ký, không có trong tìm toàn văn).
- `doc/erp/hrm/01-ho-so-nhan-su.md` — dòng bảng :152 + một đoạn ngắn «HĐLĐ → bản lưu trữ Văn bản» (ánh xạ trạng thái, gương tệp, script bù). Nếu tài liệu HĐLĐ riêng chưa có thì để ở đây, KHÔNG tạo tệp mới.
- `.claude/rules/document-folders-search.md` — 3 gạch: (1) bản lưu trữ HĐLĐ nhận diện bằng `tab_labor_contract.document_id`, quyền đọc chỉ theo `labor_contract.read`; (2) `visible_condition` không còn trả `None`; (3) loại `HDLD` bị loại khỏi `tab_document_search`.
- `.claude/rules/hr-employee-profile.md` (hoặc rule HĐLĐ nếu có) — 1 gạch: mọi đường ghi HĐ mới phải gọi `archive_sync`.
- **CR-628b:** thêm dòng `duoc-CR-628b-gop-mau-hdld-vao-thu-vien` ở `change-log.md` (đặt chỗ NGAY khi nhận việc) + mục sổ nhật ký mã riêng `duoc-CR-628b`; `14-van-thu-van-ban.md` mục thiết lập/thư viện mẫu: thêm «Mẫu hợp đồng lao động» (ai thấy, URL, quản lý bằng `labor_contract_template`); `doc/erp/hrm/01-ho-so-nhan-su.md`: đường mới của màn mẫu; `.claude/rules/frontend-v2-migration-status.md` nếu bảng màn có ghi `/hr/labor-contract-templates`.

## Triển khai (dev → prod)
1. Kiểm prod trước: `SELECT id, code, name, is_active FROM tab_doc_type WHERE code='HDLD'` — có sẵn mà khác nghĩa ⇒ dừng, hỏi đại ca.
2. Deploy bình thường (`-f docker-compose.production.yml` với prod) ⇒ `alembic upgrade head` + `seed_prod` tạo loại `HDLD`. Không cần dựng lại image (không thêm thư viện).
3. Phân quyền (D-018): vai trò Nhân sự đang chạy **không tự có** `document.read`. Tick `document.read` phạm vi «Của tôi» cho vai trò giữ `labor_contract` ở màn Phân quyền (hoặc `SEED_FORCE_SYNC=true` một lần — cân nhắc vì đè mọi vai trò). Người dùng đăng xuất/đăng nhập lại.
4. Bù dữ liệu (sau khi đại ca đồng ý — câu hỏi 1):
   `docker compose exec -T api python scripts/backfill_hdld_van_ban_luu_tru.py --dry-run` → đọc số → chạy thật.
5. Kiểm sau deploy: một tài khoản văn thư phạm vi công ty tìm tên 1 NV có HĐ ⇒ 0 kết quả; HR mở được văn bản từ tab Hợp đồng.

## Ma trận kiểm thử (tổng)
| Lớp | Phạm vi | Ở đâu |
|---|---|---|
| Unit/integration pytest | Luật đọc + mọi đường đọc + chặn thao tác dẫn xuất | phase 02 (13 nhóm) |
| Integration pytest | Tạo/đồng bộ/gương tệp/trạng thái/xóa/script | phase 03 (14 nhóm) |
| Hồi quy pytest | test HĐLĐ cũ + văn bản cá nhân | phase 02/03, chỉ tệp liên quan |
| Vitest | Nút mở bản lưu trữ | phase 04 |
| Vitest | CR-628b: luật tab Thiết lập, cửa menu/route, redirect, link hộp thoại, catalog HĐLĐ | phase 06 (7 nhóm) |
| Hồi quy pytest | CR-628b: `/api/labor-contract-templates` vẫn 403 với người thiếu khóa | `test_hdld_mau_hop_dong_api.py` |
| E2E thủ công | Luồng HR lập → sinh → ký → chấm dứt; văn thư không thấy; tìm kiếm MySQL thật (FULLTEXT — SQLite không bắt) | local Docker trước merge |

## Tiêu chí chấp nhận (toàn CR)
- Bấm «Lập hợp đồng» ⇒ có đúng 1 văn bản loại HDLD trạng thái Nháp gắn với HĐ.
- Sinh .docx / tải bản ký ⇒ văn bản có bản sao đúng tệp mới nhất (sha256 bằng nhau), không trùng.
- Ký / chấm dứt / hủy / xóa HĐ ⇒ trạng thái văn bản theo bảng ánh xạ; không văn bản nào bị xóa cứng.
- Văn thư phạm vi công ty, admin không có `labor_contract`, chính người lao động: 0 văn bản HĐLĐ ở danh sách, tìm, tổng quan, cây thư mục, trợ lý AI; mở theo id ⇒ 404; tải tệp ⇒ 404.
- HR có `labor_contract.read` (+ `document.read` cho danh sách/tải tệp) thấy đúng HĐ trong phạm vi của mình.
- `tab_document_search` không có dòng nào của văn bản HĐLĐ.
- **CR-628b:** menu HR «Mẫu hợp đồng», link trong «Lập hợp đồng»/«Sinh tệp» và `/hr/labor-contract-templates` đều tới `/document/settings?tab=templates&kind=labor-contract`. HR chỉ có `labor_contract_template` thì vào được và chỉ thấy mẫu HĐLĐ. Văn thư thiếu khóa đó thì không thấy mẫu HĐLĐ nào, kể cả khi gõ thẳng URL. Mọi thao tác mẫu (tải lên, thay tệp, soạn trên web CR-606, «⋯» CR-610, ngừng dùng, xóa) và việc sinh tệp HĐ từ mẫu chạy như cũ. `tab_labor_contract.template_id` không đổi.

## Rollback
Xem `plan.md`. Thứ tự: `--soft-delete-all` (tùy) → revert FE → revert BE → `alembic downgrade` về head trước `lbrct02`. Loại `HDLD` để lại vô hại (tắt `is_active` để cầu nối ngừng nếu chỉ muốn dừng tính năng mà không revert).

## Câu hỏi mở
1. Bù văn bản cho HĐ đã có trước CR này: chạy script trên prod ngay hay để đại ca quyết? (Mặc định: chờ đồng ý, chạy `--dry-run` trước.)
2. Vai trò `hr_profile` thêm `document.read` phạm vi «Của tôi» — đồng ý? Không thêm thì HR không có vai trò Văn bản chỉ mở được chi tiết qua nút, **không tải được tệp** (lớp 1 của `/api/attachments/*/download`) và không thấy trong danh sách Văn bản.
3. Thay bản ký: văn bản là **gương** (bản cũ bị gỡ). Có cần giữ lịch sử mọi bản ký đã từng tải (lưu trữ pháp lý) không?
4. Mở rộng bản ký nhận `.docx` (HĐ cũ soạn ngoài hệ thống) và cho tải sau khi Chấm dứt? Mặc định KHÔNG đổi (luồng hiện có đủ: tải lúc Nháp/Đã ký).
5. Thư mục «Nhân sự/HĐLĐ» theo từng pháp nhân: hiện rơi về gốc pháp nhân. Cần tự tạo thư mục con mỗi pháp nhân không?
6. Thời hạn lưu (`retention_months`) cho loại HDLD: để mặc định 120 tháng hay vĩnh viễn?
7. HR tự xem bản lưu trữ HĐ của **chính mình** (có `labor_contract.read` phạm vi tất cả): luật ủy thác cho phép, giống màn HĐLĐ hiện tại. Có cần chặn riêng ở Văn bản không? (Mặc định: không — giữ đồng nhất với HĐLĐ.)
8. **CR-628b:** đồng ý chỉ làm bước A (gộp giao diện), HOÃN bước B (gộp bảng, phase 07)? Nếu muốn bước B: cần số dòng `tab_labor_contract_template` trên prod và một lần diễn tập trên bản sao.
9. **CR-628b:** vì cửa «Thiết lập văn bản» nay nhận thêm `labor_contract_template`, HR sẽ thấy thẻ phân hệ Văn bản mở khóa (bên trong chỉ có mẫu HĐLĐ cùng các mục vốn công khai). Chấp nhận được không?
10. **CR-628b:** người chỉ có `labor_contract_template.read` (không có tạo/sửa/xóa) không qua được cửa `manage` của trang Thiết lập. Seed hiện chưa có vai trò nào như vậy. Nếu cần hỗ trợ họ thì phải nới `module-visibility` (lớp dùng chung) ở một CR riêng.
11. **CR-628b:** tên tham số `kind=labor-contract` có ổn không? Có cần đổi nhãn tab thành «Thư viện mẫu» khi người xem chỉ thấy mẫu HĐLĐ không?
